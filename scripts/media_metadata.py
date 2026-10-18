"""Bounded, format-aware extraction of text metadata from publication media."""

from __future__ import annotations

import zlib

MAX_MEDIA_BYTES = 8 * 1024 * 1024
MAX_METADATA_BYTES = 1024 * 1024
MAX_AVIF_BOXES = 10_000


class MediaInspectionError(ValueError):
    """A media candidate is malformed, spoofed, oversized, or not safely inspectable."""

    def __init__(self, message: str, *, format_name: str | None = None, cause_class: str | None = None):
        super().__init__(message)
        self.reason_code = message
        self.format_name = format_name
        self.cause_class = cause_class


def media_diagnostic_code(error: MediaInspectionError) -> str:
    """Return a stable, safe category without exposing parser text to users."""
    reason = error.reason_code.lower()
    if "inspection limit" in reason or "exceeds" in reason or "resource limit" in reason:
        return "STAGED_MEDIA_RESOURCE_LIMIT"
    if "signature mismatch" in reason or "file type box missing" in reason:
        return "STAGED_MEDIA_SIGNATURE_MISMATCH"
    if "unsupported" in reason or "brand" in reason:
        return "STAGED_MEDIA_UNSUPPORTED_FEATURE"
    if "location" in reason or "extent" in reason or "metadata" in reason:
        return "STAGED_MEDIA_METADATA_UNINSPECTABLE"
    return "STAGED_MEDIA_INVALID"


def _bounded(parts: list[bytes]) -> str:
    raw = b"\n".join(parts)
    if len(raw) > MAX_METADATA_BYTES:
        raise MediaInspectionError("metadata exceeds inspection limit")
    return raw.decode("utf-8", errors="replace")


def _png(data: bytes) -> str:
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise MediaInspectionError("PNG signature mismatch")
    offset = 8
    texts: list[bytes] = []
    seen_end = False
    seen_header = False
    while offset < len(data):
        if len(data) - offset < 12:
            raise MediaInspectionError("truncated PNG chunk")
        length = int.from_bytes(data[offset:offset + 4], "big")
        kind = data[offset + 4:offset + 8]
        end = offset + 12 + length
        if length > MAX_METADATA_BYTES or end > len(data):
            raise MediaInspectionError("invalid PNG chunk size")
        payload = data[offset + 8:offset + 8 + length]
        if not seen_header:
            if kind != b"IHDR" or length != 13:
                raise MediaInspectionError("PNG header chunk missing or misplaced")
            if int.from_bytes(payload[:4], "big") == 0 or int.from_bytes(payload[4:8], "big") == 0:
                raise MediaInspectionError("invalid PNG dimensions")
            seen_header = True
        elif kind == b"IHDR":
            raise MediaInspectionError("duplicate PNG header chunk")
        expected = int.from_bytes(data[offset + 8 + length:end], "big")
        if zlib.crc32(kind + payload) & 0xffffffff != expected:
            raise MediaInspectionError("PNG chunk checksum mismatch")
        if kind == b"tEXt":
            texts.append(payload.replace(b"\x00", b" "))
        elif kind == b"iTXt":
            fields = payload.split(b"\x00", 5)
            if len(fields) != 6:
                raise MediaInspectionError("invalid PNG international text")
            keyword, compressed, compression_method, _language, _translated, text = fields
            if compression_method != b"\x00":
                raise MediaInspectionError("unsupported PNG text compression method")
            if compressed == b"\x01":
                decoder = zlib.decompressobj()
                text = decoder.decompress(text, MAX_METADATA_BYTES + 1)
                if decoder.unconsumed_tail or len(text) > MAX_METADATA_BYTES or not decoder.eof:
                    raise MediaInspectionError("compressed PNG text exceeds inspection limit")
            elif compressed != b"\x00":
                raise MediaInspectionError("invalid PNG text compression flag")
            texts.append(keyword + b" " + text)
        elif kind == b"zTXt":
            keyword, separator, packed = payload.partition(b"\x00")
            if not separator or not packed.startswith(b"\x00"):
                raise MediaInspectionError("invalid PNG compressed text")
            decoder = zlib.decompressobj()
            text = decoder.decompress(packed[1:], MAX_METADATA_BYTES + 1)
            if decoder.unconsumed_tail or len(text) > MAX_METADATA_BYTES or not decoder.eof:
                raise MediaInspectionError("compressed PNG text exceeds inspection limit")
            texts.append(keyword + b" " + text)
        offset = end
        if kind == b"IEND":
            if length != 0 or offset != len(data):
                raise MediaInspectionError("invalid PNG end chunk")
            seen_end = True
            break
    if not seen_header or not seen_end:
        raise MediaInspectionError("PNG end chunk missing")
    return _bounded(texts)


def _jpeg(data: bytes) -> str:
    if not data.startswith(b"\xff\xd8") or not data.endswith(b"\xff\xd9"):
        raise MediaInspectionError("JPEG boundary marker mismatch")
    offset = 2
    texts: list[bytes] = []
    saw_frame = False
    saw_scan = False
    in_scan = False
    saw_eoi = False
    while offset < len(data) - 2:
        if in_scan:
            # Skip entropy-coded bytes, stuffed FF00 and restart markers; resume
            # segment parsing at every other marker so metadata between scans is seen.
            while offset < len(data) - 1:
                if data[offset] != 0xff:
                    offset += 1
                    continue
                marker_start = offset
                while offset < len(data) and data[offset] == 0xff:
                    offset += 1
                if offset >= len(data):
                    raise MediaInspectionError("truncated JPEG entropy marker")
                marker = data[offset]
                if marker == 0x00 or 0xd0 <= marker <= 0xd7:
                    offset += 1
                    continue
                if marker == 0xd9:
                    if marker_start != len(data) - 2:
                        raise MediaInspectionError("trailing bytes after JPEG end marker")
                    saw_eoi = True
                    offset = len(data)
                    break
                offset = marker_start
                in_scan = False
                break
            if saw_eoi:
                break
            if in_scan:
                break
        if data[offset] != 0xff:
            raise MediaInspectionError("invalid JPEG marker")
        while offset < len(data) and data[offset] == 0xff:
            offset += 1
        if offset >= len(data):
            raise MediaInspectionError("truncated JPEG marker")
        marker = data[offset]
        offset += 1
        if marker == 0xd9:
            if offset != len(data) - 2:
                raise MediaInspectionError("trailing bytes after JPEG end marker")
            saw_eoi = True
            break
        if marker == 0xd8 or 0xd0 <= marker <= 0xd7 or marker == 0x01:
            continue
        if offset + 2 > len(data):
            raise MediaInspectionError("truncated JPEG segment")
        length = int.from_bytes(data[offset:offset + 2], "big")
        if length < 2 or offset + length > len(data):
            raise MediaInspectionError("invalid JPEG segment size")
        payload = data[offset + 2:offset + length]
        if 0xc0 <= marker <= 0xcf and marker not in {0xc4, 0xc8, 0xcc}:
            components = payload[5] if len(payload) >= 6 else 0
            if len(payload) < 6 + components * 3:
                raise MediaInspectionError("truncated JPEG frame header")
            saw_frame = True
        if marker == 0xfe:
            texts.append(payload)
        elif 0xe0 <= marker <= 0xef:
            # XMP and printable EXIF user metadata are inspected; image payload is not.
            if marker == 0xe1 and payload.startswith(b"http://ns.adobe.com/xap/1.0/\x00"):
                texts.append(payload.split(b"\x00", 1)[1])
            elif marker == 0xe1 and payload.startswith(b"Exif\x00\x00"):
                texts.extend(_printable_runs(payload[6:]))
            else:
                texts.extend(_printable_runs(payload))
        if marker == 0xda:
            components = payload[0] if payload else 0
            if len(payload) < 4 + components * 2:
                raise MediaInspectionError("truncated JPEG scan header")
            saw_scan = True
            in_scan = True
        offset += length
    if not saw_frame or not saw_scan or not saw_eoi:
        raise MediaInspectionError("JPEG frame or scan header missing")
    return _bounded(texts)


def _printable_runs(data: bytes) -> list[bytes]:
    runs: list[bytes] = []
    start = None
    for index, byte in enumerate(data + b"\x00"):
        if 32 <= byte < 127 or byte in (9, 10, 13):
            if start is None:
                start = index
        elif start is not None:
            if index - start >= 4:
                runs.append(data[start:index])
            start = None
    for codec in ("utf-16-le", "utf-16-be"):
        decoded = data[:len(data) - (len(data) % 2)].decode(codec, errors="ignore")
        run: list[str] = []
        for char in decoded + "\x00":
            if char.isprintable() or char in "\r\n\t":
                run.append(char)
            else:
                if len(run) >= 4:
                    runs.append("".join(run).encode("utf-8"))
                run = []
    return runs


def _webp(data: bytes) -> str:
    if len(data) < 12 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise MediaInspectionError("WebP signature mismatch")
    declared = int.from_bytes(data[4:8], "little") + 8
    if declared != len(data):
        raise MediaInspectionError("WebP RIFF size mismatch")
    offset = 12
    texts: list[bytes] = []
    seen_image = False
    while offset < len(data):
        if len(data) - offset < 8:
            raise MediaInspectionError("truncated WebP chunk")
        kind = data[offset:offset + 4]
        length = int.from_bytes(data[offset + 4:offset + 8], "little")
        end = offset + 8 + length
        padded = end + (length & 1)
        if end > len(data) or padded > len(data):
            raise MediaInspectionError("invalid WebP chunk size")
        payload = data[offset + 8:end]
        if kind in {b"EXIF", b"XMP "}:
            texts.extend(_printable_runs(payload))
        elif kind in {b"VP8 ", b"VP8L", b"VP8X"}:
            if kind == b"VP8X" and len(payload) != 10:
                raise MediaInspectionError("invalid WebP extended header")
            if kind == b"VP8 " and len(payload) < 10:
                raise MediaInspectionError("invalid WebP lossy image chunk")
            if kind == b"VP8L" and (len(payload) < 5 or payload[0] != 0x2f):
                raise MediaInspectionError("invalid WebP lossless image chunk")
            seen_image = True
        offset = padded
    if not seen_image:
        raise MediaInspectionError("WebP image chunk missing")
    return _bounded(texts)


def _mp3(data: bytes) -> str:
    if len(data) < 4:
        raise MediaInspectionError("MP3 audio frame header missing")
    if data[:3] == b"ID3":
        if len(data) < 10:
            raise MediaInspectionError("truncated ID3 header")
        version, revision, flags = data[3:6]
        if version not in {3, 4} or revision == 0xff or flags != 0:
            raise MediaInspectionError("unsupported ID3 version or flags")
        size_bytes = data[6:10]
        if len(size_bytes) != 4 or any(byte & 0x80 for byte in size_bytes):
            raise MediaInspectionError("invalid ID3 size")
        size = (size_bytes[0] << 21) | (size_bytes[1] << 14) | (size_bytes[2] << 7) | size_bytes[3]
        end = 10 + size
        if end > len(data) or size > MAX_METADATA_BYTES:
            raise MediaInspectionError("invalid or oversized ID3 tag")
        offset = 10
        texts: list[bytes] = []
        while offset < end:
            if offset + 10 > end:
                raise MediaInspectionError("truncated ID3 frame")
            frame_id = data[offset:offset + 4]
            if version == 3:
                frame_size = int.from_bytes(data[offset + 4:offset + 8], "big")
            else:
                raw_size = data[offset + 4:offset + 8]
                if any(byte & 0x80 for byte in raw_size):
                    raise MediaInspectionError("invalid ID3 frame size")
                frame_size = (raw_size[0] << 21) | (raw_size[1] << 14) | (raw_size[2] << 7) | raw_size[3]
            if frame_id == b"\x00\x00\x00\x00":
                break
            frame_flags = data[offset + 8:offset + 10]
            frame_end = offset + 10 + frame_size
            if frame_end > end:
                raise MediaInspectionError("ID3 frame exceeds tag")
            if frame_id.startswith(b"T") or frame_id == b"COMM":
                if frame_flags != b"\x00\x00":
                    raise MediaInspectionError("transformed ID3 text frame is unsupported")
                frame = data[offset + 10:frame_end]
                if frame:
                    encoding = frame[0]
                    content = frame[1:]
                    try:
                        codec = {0: "latin-1", 1: "utf-16", 2: "utf-16-be", 3: "utf-8"}[encoding]
                        texts.append(content.decode(codec, errors="strict").encode("utf-8"))
                    except (KeyError, UnicodeError) as exc:
                        raise MediaInspectionError("invalid ID3 text encoding") from exc
            offset = frame_end
        audio_offset = end
    else:
        texts = []
        audio_offset = 0
    if len(data) - audio_offset < 4:
        raise MediaInspectionError("MP3 audio frame header missing")
    frame_header = int.from_bytes(data[audio_offset:audio_offset + 4], "big")
    version_id = (frame_header >> 19) & 0x3
    layer = (frame_header >> 17) & 0x3
    if (frame_header >> 21) != 0x7ff or version_id == 1 or layer == 0:
        raise MediaInspectionError("invalid MPEG audio frame header")
    return _bounded(texts)


def _m4a(data: bytes) -> str:
    from m4a_inspection import inspect_m4a, metadata_text
    try:
        return metadata_text(inspect_m4a(data).metadata)
    except ValueError as exc:
        raise MediaInspectionError("invalid M4A container") from exc


def _avif(data: bytes) -> str:
    """Inspect a static AVIF container and extract bounded Exif/XMP item text.

    This validates ISO-BMFF structure and metadata locations; it does not decode
    AV1 image payloads or establish visual quality.
    """
    def boxes(payload: bytes, start: int = 0, end: int | None = None):
        limit = len(payload) if end is None else end
        offset = start
        count = 0
        while offset < limit:
            count += 1
            if count > MAX_AVIF_BOXES:
                raise MediaInspectionError("AVIF box count exceeds inspection limit")
            if limit - offset < 8:
                raise MediaInspectionError("truncated AVIF box")
            size = int.from_bytes(payload[offset:offset + 4], "big")
            kind = payload[offset + 4:offset + 8]
            header = 8
            if size == 1:
                if limit - offset < 16:
                    raise MediaInspectionError("truncated AVIF extended box")
                size = int.from_bytes(payload[offset + 8:offset + 16], "big")
                header = 16
            elif size == 0:
                size = limit - offset
            if size < header or offset + size > limit:
                raise MediaInspectionError("invalid AVIF box size")
            yield kind, offset + header, offset + size
            offset += size
        if offset != limit:
            raise MediaInspectionError("invalid AVIF box boundary")

    try:
        top = list(boxes(data))
        if not top or top[0][0] != b"ftyp":
            raise MediaInspectionError("AVIF file type box missing")
        _, ftyp_start, ftyp_end = top[0]
        ftyp = data[ftyp_start:ftyp_end]
        if len(ftyp) < 8 or (len(ftyp) - 8) % 4:
            raise MediaInspectionError("invalid AVIF file type box")
        brands = {ftyp[:4]} | {ftyp[index:index + 4] for index in range(8, len(ftyp), 4)}
        if b"avis" in brands or not ({b"avif", b"mif1", b"miaf"} & brands):
            raise MediaInspectionError("unsupported AVIF brand")
        meta_boxes = [item for item in top if item[0] == b"meta"]
        if len(meta_boxes) != 1:
            raise MediaInspectionError("AVIF metadata box missing or duplicated")
        _, meta_start, meta_end = meta_boxes[0]
        if meta_end - meta_start < 4:
            raise MediaInspectionError("truncated AVIF metadata box")
        meta_children = list(boxes(data, meta_start + 4, meta_end))
        by_type: dict[bytes, list[tuple[int, int]]] = {}
        for kind, start, end in meta_children:
            by_type.setdefault(kind, []).append((start, end))
        if len(by_type.get(b"iinf", [])) != 1 or len(by_type.get(b"iloc", [])) != 1:
            raise MediaInspectionError("AVIF item index is incomplete")

        # Map item IDs to metadata MIME/type declarations.
        item_types: dict[int, tuple[bytes, bytes]] = {}
        iinf_start, iinf_end = by_type[b"iinf"][0]
        if iinf_end - iinf_start < 6:
            raise MediaInspectionError("truncated AVIF item information")
        iinf_version = data[iinf_start]
        count_width = 2 if iinf_version == 0 else 4
        if iinf_version not in {0, 1} or iinf_end - iinf_start < 4 + count_width:
            raise MediaInspectionError("unsupported AVIF item information version")
        info_count = int.from_bytes(data[iinf_start + 4:iinf_start + 4 + count_width], "big")
        info_boxes = list(boxes(data, iinf_start + 4 + count_width, iinf_end))
        if info_count != len(info_boxes):
            raise MediaInspectionError("AVIF item information count mismatch")
        for kind, start, end in info_boxes:
            if kind != b"infe" or end - start < 12:
                continue
            version = data[start]
            if version not in {2, 3}:
                continue
            width = 2 if version == 2 else 4
            item_id = int.from_bytes(data[start + 4:start + 4 + width], "big")
            type_offset = start + 8
            item_kind = data[type_offset:type_offset + 4]
            tail = data[type_offset + 4:end]
            if item_kind == b"Exif":
                item_types[item_id] = (item_kind, b"")
            elif item_kind == b"mime":
                fields = tail.split(b"\x00")
                mime = fields[1].lower() if len(fields) >= 2 else b""
                if mime in {b"application/rdf+xml", b"application/xml", b"text/xml"}:
                    item_types[item_id] = (item_kind, mime)

        # Parse iloc versions 0–2, retaining only bounded local extents.
        iloc_start, iloc_end = by_type[b"iloc"][0]
        if iloc_end - iloc_start < 8:
            raise MediaInspectionError("truncated AVIF item locations")
        version = data[iloc_start]
        if version not in {0, 1, 2}:
            raise MediaInspectionError("unsupported AVIF item location version")
        sizes_at = iloc_start + 4
        offset_size, length_size = data[sizes_at] >> 4, data[sizes_at] & 15
        base_size = data[sizes_at + 1] >> 4
        index_size = data[sizes_at + 1] & 15 if version in {1, 2} else 0
        if max(offset_size, length_size, base_size, index_size) > 8:
            raise MediaInspectionError("unsupported AVIF item location field size")
        cursor = sizes_at + 2
        count_width = 4 if version == 2 else 2
        item_count = int.from_bytes(data[cursor:cursor + count_width], "big")
        cursor += count_width
        id_width = 4 if version == 2 else 2
        idat_boxes = by_type.get(b"idat", [])
        metadata_parts: list[bytes] = []

        def read_uint(width: int) -> int:
            nonlocal cursor
            if cursor + width > iloc_end:
                raise MediaInspectionError("truncated AVIF item location entry")
            value = int.from_bytes(data[cursor:cursor + width], "big") if width else 0
            cursor += width
            return value

        for _ in range(item_count):
            item_id = read_uint(id_width)
            method_raw = read_uint(2) if version in {1, 2} else 0
            if method_raw & 0xfff0:
                raise MediaInspectionError("invalid AVIF item construction method")
            method = method_raw & 0x000f
            data_reference = read_uint(2)
            base = read_uint(base_size)
            extent_count = read_uint(2)
            targets_metadata = item_id in item_types
            for _extent in range(extent_count):
                if index_size:
                    read_uint(index_size)
                extent_offset = read_uint(offset_size)
                extent_length = read_uint(length_size)
                if not targets_metadata:
                    continue
                if data_reference != 0 or method not in {0, 1}:
                    raise MediaInspectionError("unsupported AVIF metadata location")
                absolute = base + extent_offset
                if method == 1:
                    if len(idat_boxes) != 1:
                        raise MediaInspectionError("AVIF item data box missing or duplicated")
                    idat_start, idat_end = idat_boxes[0]
                    absolute += idat_start
                    if absolute < idat_start or absolute + extent_length > idat_end:
                        raise MediaInspectionError("invalid AVIF item data extent")
                elif absolute + extent_length > len(data):
                    raise MediaInspectionError("invalid AVIF item extent")
                elif not any(start <= absolute and absolute + extent_length <= end
                             for kind, start, end in top if kind == b"mdat"):
                    raise MediaInspectionError("AVIF metadata extent is outside item data")
                if extent_length > MAX_METADATA_BYTES or sum(map(len, metadata_parts)) + extent_length > MAX_METADATA_BYTES:
                    raise MediaInspectionError("metadata exceeds inspection limit")
                item_kind, mime = item_types[item_id]
                if item_kind == b"Exif" or mime in {b"application/rdf+xml", b"application/xml", b"text/xml"}:
                    metadata_parts.append(data[absolute:absolute + extent_length])
        if cursor != iloc_end:
            raise MediaInspectionError("invalid AVIF item location boundary")
        texts: list[bytes] = []
        for part in metadata_parts:
            if len(part) >= 4 and part[:4].isdigit():
                exif_offset = int.from_bytes(part[:4], "big")
                if 4 + exif_offset < len(part):
                    texts.extend(_printable_runs(part[4 + exif_offset:]))
            else:
                texts.extend(_printable_runs(part))
        return _bounded(texts)
    except MediaInspectionError:
        raise
    except (IndexError, OverflowError, ValueError) as exc:
        raise MediaInspectionError("invalid AVIF container") from exc


MEDIA_FORMAT_REGISTRY = {
    ".png": ("raster", _png),
    ".jpg": ("raster", _jpeg),
    ".jpeg": ("raster", _jpeg),
    ".webp": ("raster", _webp),
    ".avif": ("raster", _avif),
    ".m4a": ("audio", _m4a),
    ".mp3": ("audio", _mp3),
}
RASTER_SUFFIXES = frozenset(suffix for suffix, (kind, _handler) in MEDIA_FORMAT_REGISTRY.items() if kind == "raster")
MEDIA_SUFFIXES = frozenset(MEDIA_FORMAT_REGISTRY)


def extract_metadata(data: bytes, suffix: str) -> str:
    if len(data) > MAX_MEDIA_BYTES:
        raise MediaInspectionError("media exceeds inspection limit")
    if suffix.lower() in {".ttf", ".otf", ".woff", ".woff2"}:
        from font_metadata import FontInspectionError, extract_font_metadata
        try:
            text, _format = extract_font_metadata(data, suffix)
            return text
        except FontInspectionError as exc:
            raise MediaInspectionError(exc.reason_code, format_name=exc.format_name,
                                      cause_class=exc.cause_class) from exc
    registered = MEDIA_FORMAT_REGISTRY.get(suffix.lower())
    if not registered:
        raise MediaInspectionError("unsupported binary format")
    _kind, handler = registered
    return handler(data)
