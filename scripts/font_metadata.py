"""Bounded extraction of searchable metadata from OpenType and web fonts."""

from __future__ import annotations

from io import BytesIO

MAX_FONT_BYTES = 8 * 1024 * 1024
MAX_DECOMPRESSED_BYTES = 32 * 1024 * 1024
MAX_METADATA_BYTES = 1024 * 1024


class FontInspectionError(ValueError):
    def __init__(self, reason_code: str, format_name: str | None = None, cause_class: str | None = None):
        super().__init__(reason_code)
        self.reason_code = reason_code
        self.format_name = format_name
        self.cause_class = cause_class


def _format(data: bytes, suffix: str) -> str:
    signatures = {
        ".ttf": ((b"\x00\x01\x00\x00", "TrueType"), (b"true", "TrueType")),
        ".otf": ((b"OTTO", "OpenType-CFF"),),
        ".woff": ((b"wOFF", "WOFF"),),
        ".woff2": ((b"wOF2", "WOFF2"),),
    }
    choices = signatures.get(suffix.lower())
    if choices is None:
        raise FontInspectionError("STAGED_FONT_UNSUPPORTED")
    actual = next((name for magic, name in choices if data.startswith(magic)), None)
    if actual is None:
        detected = next((name for choices_for_suffix in signatures.values()
                         for magic, name in choices_for_suffix if data.startswith(magic)), None)
        raise FontInspectionError("STAGED_FONT_FORMAT_MISMATCH", detected)
    if actual in {"WOFF", "WOFF2"}:
        header_size = 44 if actual == "WOFF" else 48
        if len(data) < header_size:
            raise FontInspectionError("STAGED_FONT_INVALID", actual)
        declared_file = int.from_bytes(data[8:12], "big")
        expanded = int.from_bytes(data[16:20], "big")
        if declared_file != len(data) or expanded > MAX_DECOMPRESSED_BYTES:
            raise FontInspectionError("STAGED_FONT_RESOURCE_LIMIT", actual)
        if actual == "WOFF":
            table_count = int.from_bytes(data[12:14], "big")
            directory_end = 44 + table_count * 20
            if table_count == 0 or table_count > 256 or directory_end > len(data):
                raise FontInspectionError("STAGED_FONT_INVALID", actual)
            original_total = 0
            for offset in range(44, directory_end, 20):
                table_start = int.from_bytes(data[offset + 4:offset + 8], "big")
                compressed_length = int.from_bytes(data[offset + 8:offset + 12], "big")
                original_length = int.from_bytes(data[offset + 12:offset + 16], "big")
                if (table_start < directory_end or table_start + compressed_length > len(data)
                        or compressed_length > original_length):
                    raise FontInspectionError("STAGED_FONT_INVALID", actual)
                original_total += original_length
                if original_total > expanded:
                    raise FontInspectionError("STAGED_FONT_RESOURCE_LIMIT", actual)
    if actual in {"TrueType", "OpenType-CFF"} and len(data) < 12:
        raise FontInspectionError("STAGED_FONT_INVALID", actual)
    if actual == "TrueType" and suffix.lower() == ".otf" or actual == "OpenType-CFF" and suffix.lower() == ".ttf":
        raise FontInspectionError("STAGED_FONT_FORMAT_MISMATCH", actual)
    return actual


def extract_font_metadata(data: bytes, suffix: str) -> tuple[str, str]:
    fmt = _format(data, suffix)
    if len(data) > MAX_FONT_BYTES:
        raise FontInspectionError("STAGED_FONT_RESOURCE_LIMIT", fmt)
    if fmt == "WOFF2":
        try:
            import brotli  # noqa: F401
        except ImportError as exc:
            raise FontInspectionError("STAGED_FONT_BROTLI_UNAVAILABLE", fmt, type(exc).__name__) from exc
    try:
        from fontTools.ttLib import TTFont
    except ImportError as exc:
        raise FontInspectionError("STAGED_FONT_INSPECTOR_UNAVAILABLE", fmt, type(exc).__name__) from exc
    font = None
    try:
        font = TTFont(BytesIO(data), lazy=True, recalcBBoxes=False, recalcTimestamp=False)
        if len(font.reader.tables) > 256:
            raise FontInspectionError("STAGED_FONT_RESOURCE_LIMIT", fmt)
        # Validate table directory ranges before accessing metadata tables.
        if fmt not in {"WOFF", "WOFF2"}:
            for table in font.reader.tables.values():
                if table.offset < 0 or table.length < 0 or table.offset + table.length > len(data):
                    raise FontInspectionError("STAGED_FONT_INVALID", fmt)
        signatures = set(font.reader.tables)
        sfnt_version = font.sfntVersion
        is_cff = "CFF " in signatures or "CFF2" in signatures
        if sfnt_version == "OTTO" and not is_cff or sfnt_version != "OTTO" and "glyf" not in signatures:
            raise FontInspectionError("STAGED_FONT_INVALID", fmt)
        output: list[str] = [f"format={fmt}"]
        name = font.get("name")
        if name:
            for record in name.names:
                try:
                    value = record.toUnicode()
                except (UnicodeError, ValueError):
                    continue
                if value:
                    output.append(value)
        os2 = font.get("OS/2")
        if os2:
            output.extend(str(getattr(os2, field)) for field in ("achVendID",) if getattr(os2, field, None))
        text = "\n".join(output)
        if len(text.encode("utf-8")) > MAX_METADATA_BYTES:
            raise FontInspectionError("STAGED_FONT_RESOURCE_LIMIT", fmt)
        return text, fmt
    except FontInspectionError:
        raise
    except Exception as exc:  # fontTools exceptions vary by malformed table/version.
        raise FontInspectionError("STAGED_FONT_INVALID", fmt, type(exc).__name__) from exc
    finally:
        if font is not None:
            font.close()
