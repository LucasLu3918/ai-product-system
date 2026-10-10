"""Confined image inspection and passive SVG/PNG container validation."""
from __future__ import annotations

import base64
import binascii
import hashlib
import re
import struct
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path, PurePosixPath
from typing import Any, NoReturn

MAX_IMAGE_BYTES = 20 * 1024 * 1024

MAX_IMAGE_DIMENSION = 16_384

MAX_IMAGE_PIXELS = 100_000_000

SVG_NS = "http://www.w3.org/2000/svg"

FORBIDDEN_SVG_ELEMENTS = {
    "script",
    "foreignObject",
    "iframe",
    "object",
    "embed",
    "audio",
    "video",
}

class ArtifactError(ValueError):
    """A bounded, user-actionable validation error."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code

def _error(code: str, message: str) -> NoReturn:
    raise ArtifactError(code, message)

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(64 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()

def _project_path(project: Path, value: object, *, must_exist: bool = True) -> Path:
    if not isinstance(value, str) or not value.strip():
        _error("PATH_INVALID", "A non-empty project-relative path is required.")
    supplied = PurePosixPath(value)
    if supplied.is_absolute() or ".." in supplied.parts or "\\" in value:
        _error(
            "PATH_OUTSIDE_PROJECT",
            "Absolute paths and parent traversal are not allowed.",
        )
    root = project.resolve()
    candidate = root.joinpath(*supplied.parts)
    try:
        resolved = candidate.resolve(strict=must_exist)
    except (OSError, RuntimeError) as exc:
        _error("PATH_INVALID", f"Path cannot be resolved safely: {exc}")
    if resolved != root and root not in resolved.parents:
        _error("PATH_OUTSIDE_PROJECT", "Symlink target escapes the project root.")
    if must_exist and not resolved.is_file():
        _error("FILE_MISSING", f"Project file does not exist: {value}")
    return resolved

def _dimensions(width: int, height: int) -> tuple[int, int]:
    if (
        width <= 0
        or height <= 0
        or width > MAX_IMAGE_DIMENSION
        or height > MAX_IMAGE_DIMENSION
    ):
        _error(
            "IMAGE_DIMENSIONS_INVALID",
            "Image dimensions are outside the supported range.",
        )
    if width * height > MAX_IMAGE_PIXELS:
        _error("IMAGE_TOO_LARGE", "Image pixel count exceeds the supported maximum.")
    return width, height

def _png_dimensions(data: bytes) -> tuple[int, int]:
    if len(data) > MAX_IMAGE_BYTES or not data.startswith(b"\x89PNG\r\n\x1a\n"):
        _error(
            "PNG_INVALID",
            "PNG signature is invalid or the image exceeds the size limit.",
        )
    offset = 8
    width = height = 0
    seen_ihdr = seen_idat = seen_iend = idat_ended = False
    image_data: list[bytes] = []
    bit_depth = color_type = interlace = 0
    while offset + 12 <= len(data):
        length = struct.unpack_from(">I", data, offset)[0]
        chunk_type = data[offset + 4 : offset + 8]
        end = offset + 12 + length
        if end > len(data):
            _error("PNG_TRUNCATED", "PNG chunk extends beyond the end of the file.")
        payload = data[offset + 8 : offset + 8 + length]
        recorded_crc = struct.unpack_from(">I", data, offset + 8 + length)[0]
        if zlib.crc32(chunk_type + payload) & 0xFFFFFFFF != recorded_crc:
            _error("PNG_CRC_INVALID", "PNG chunk checksum does not match its bytes.")
        if not seen_ihdr:
            if chunk_type != b"IHDR" or length != 13:
                _error("PNG_IHDR_INVALID", "PNG must begin with one valid IHDR chunk.")
            width, height = struct.unpack_from(">II", payload)
            _dimensions(width, height)
            bit_depth, color_type = payload[8], payload[9]
            interlace = payload[12]
            valid_depths = {
                0: {1, 2, 4, 8, 16},
                2: {8, 16},
                3: {1, 2, 4, 8},
                4: {8, 16},
                6: {8, 16},
            }
            if (
                color_type not in valid_depths
                or bit_depth not in valid_depths[color_type]
                or payload[10:12] != b"\x00\x00"
                or interlace != 0
            ):
                _error(
                    "PNG_IHDR_INVALID",
                    "PNG bit depth, color type, compression, filter, or interlace mode is unsupported.",
                )
            seen_ihdr = True
        elif chunk_type == b"IHDR":
            _error("PNG_IHDR_INVALID", "PNG contains more than one IHDR chunk.")
        if seen_idat and chunk_type not in {b"IDAT", b"IEND"}:
            idat_ended = True
        if chunk_type == b"IDAT":
            if idat_ended:
                _error("PNG_IDAT_ORDER_INVALID", "PNG IDAT chunks must be contiguous.")
            seen_idat = True
            image_data.append(payload)
        if chunk_type == b"IEND":
            if length != 0:
                _error("PNG_IEND_INVALID", "PNG IEND chunk must be empty.")
            seen_iend = True
            offset = end
            break
        offset = end
    if not (seen_ihdr and seen_idat and seen_iend) or offset != len(data):
        _error(
            "PNG_TRUNCATED",
            "PNG is missing image data/end marker or has trailing bytes.",
        )
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color_type]
    scanline_bytes = (width * channels * bit_depth + 7) // 8
    expected_bytes = (scanline_bytes + 1) * height
    decompressor = zlib.decompressobj()
    decoded_bytes = 0
    try:
        for chunk in image_data:
            pending = chunk
            while pending:
                decoded = decompressor.decompress(
                    pending, min(65536, expected_bytes - decoded_bytes + 1)
                )
                decoded_bytes += len(decoded)
                if decoded_bytes > expected_bytes:
                    _error(
                        "PNG_IMAGE_DATA_INVALID",
                        "Decoded PNG data exceeds its declared dimensions.",
                    )
                pending = decompressor.unconsumed_tail
        tail = decompressor.flush()
        decoded_bytes += len(tail)
    except zlib.error:
        _error("PNG_IMAGE_DATA_INVALID", "PNG image data is not a valid zlib stream.")
    if not decompressor.eof or decoded_bytes != expected_bytes:
        _error(
            "PNG_IMAGE_DATA_INVALID",
            "PNG image data length does not match its declared dimensions.",
        )
    return width, height

def _svg_dimension(value: str | None) -> float | None:
    if not value:
        return None
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)(?:px)?\s*", value, flags=re.IGNORECASE)
    return float(match.group(1)) if match else None

def _validate_svg_bytes(data: bytes, *, nested_depth: int = 0) -> tuple[int, int]:
    if len(data) > MAX_IMAGE_BYTES:
        _error("SVG_TOO_LARGE", "SVG input exceeds the size limit.")
    if nested_depth > 2:
        _error("SVG_NESTING_TOO_DEEP", "Nested SVG data URI depth exceeds the limit.")
    upper = data.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        _error(
            "SVG_XML_DECLARATION_FORBIDDEN",
            "SVG DTDs and entity declarations are not allowed.",
        )
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        _error("SVG_XML_INVALID", f"SVG XML is malformed: {exc}")
    if root.tag not in {f"{{{SVG_NS}}}svg", "svg"}:
        _error("SVG_ROOT_INVALID", "Document root must be an SVG element.")

    for node in root.iter():
        local_name = (
            node.tag.rsplit("}", 1)[-1].lower() if isinstance(node.tag, str) else ""
        )
        if local_name in FORBIDDEN_SVG_ELEMENTS:
            _error("SVG_ACTIVE_CONTENT", f"SVG element is not allowed: {local_name}.")
        if local_name == "style":
            css = (node.text or "").lower()
            if (
                "@import" in css
                or "javascript:" in css
                or any(
                    not value.startswith("#")
                    for value in re.findall(r"""url\(\s*['"]?([^)'"\s]+)""", css)
                )
            ):
                _error(
                    "SVG_EXTERNAL_REFERENCE",
                    "SVG style blocks may reference local fragments only.",
                )
        for raw_name, raw_value in node.attrib.items():
            name = raw_name.rsplit("}", 1)[-1].lower()
            value = str(raw_value).strip()
            if name.startswith("on"):
                _error(
                    "SVG_EVENT_HANDLER", "SVG event-handler attributes are not allowed."
                )
            if name in {"href", "src"}:
                if value.startswith("#"):
                    continue
                if value.startswith("data:"):
                    _validate_data_uri(value, nested_depth=nested_depth)
                    continue
                _error(
                    "SVG_EXTERNAL_REFERENCE",
                    "SVG external and relative references are not allowed.",
                )
            if (
                re.search(r"javascript\s*:", value, re.IGNORECASE)
                or "@import" in value.lower()
            ):
                _error(
                    "SVG_ACTIVE_CONTENT",
                    "SVG script URLs and imported styles are not allowed.",
                )
            for reference in re.findall(
                r"url\(\s*['\"]?([^)'\"\s]+)", value, flags=re.IGNORECASE
            ):
                if not reference.startswith("#"):
                    _error(
                        "SVG_EXTERNAL_REFERENCE",
                        "SVG CSS may reference local fragments only.",
                    )

    width = _svg_dimension(root.attrib.get("width"))
    height = _svg_dimension(root.attrib.get("height"))
    if width is None or height is None:
        view_box = root.attrib.get("viewBox") or root.attrib.get("viewbox") or ""
        parts = re.split(r"[\s,]+", view_box.strip())
        if len(parts) == 4:
            try:
                width = width or float(parts[2])
                height = height or float(parts[3])
            except ValueError:
                pass
    if (
        width is None
        or height is None
        or not width.is_integer()
        or not height.is_integer()
    ):
        _error(
            "SVG_DIMENSIONS_MISSING",
            "SVG requires positive integer width/height or an integer viewBox size.",
        )
    return _dimensions(int(width), int(height))

def _validate_data_uri(value: str, *, nested_depth: int) -> None:
    match = re.fullmatch(
        r"data:image/(png|svg\+xml);base64,([A-Za-z0-9+/=]+)",
        value,
        flags=re.IGNORECASE,
    )
    if not match:
        _error(
            "SVG_DATA_URI_INVALID",
            "Only base64 PNG or sanitized SVG data URIs are allowed.",
        )
    try:
        decoded = base64.b64decode(match.group(2), validate=True)
    except (ValueError, binascii.Error):
        _error("SVG_DATA_URI_INVALID", "Embedded image data is not valid base64.")
    if len(decoded) > MAX_IMAGE_BYTES:
        _error("SVG_DATA_URI_TOO_LARGE", "Embedded image exceeds the size limit.")
    if match.group(1).lower() == "png":
        _png_dimensions(decoded)
    else:
        _validate_svg_bytes(decoded, nested_depth=nested_depth + 1)

def inspect_asset(path: Path) -> dict[str, Any]:
    if path.stat().st_size > MAX_IMAGE_BYTES:
        _error("IMAGE_TOO_LARGE", "Image file exceeds the size limit.")
    data = path.read_bytes()
    suffix = path.suffix.lower()
    if suffix == ".png":
        width, height = _png_dimensions(data)
        image_format = "png"
    elif suffix == ".svg":
        width, height = _validate_svg_bytes(data)
        image_format = "svg"
    else:
        _error("IMAGE_FORMAT_UNSUPPORTED", "Only SVG and PNG assets are supported.")
    return {
        "format": image_format,
        "width": width,
        "height": height,
        "sha256": "sha256:" + hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
    }
