"""Bounded raster container checks; these never establish visual quality."""
from __future__ import annotations

import struct
import zlib
from pathlib import Path


def valid_png(data: bytes) -> bool:
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return False
    offset, seen_header, seen_data = 8, False, False
    compressed = bytearray()
    while offset + 12 <= len(data):
        size = int.from_bytes(data[offset:offset + 4], "big")
        end = offset + 12 + size
        if end > len(data):
            return False
        kind, body = data[offset + 4:offset + 8], data[offset + 8:end - 4]
        if zlib.crc32(kind + body) & 0xffffffff != int.from_bytes(data[end - 4:end], "big"):
            return False
        if not seen_header and kind != b"IHDR":
            return False
        if kind == b"IHDR":
            if seen_header or len(body) != 13:
                return False
            width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", body)
            if not 0 < width <= 8192 or not 0 < height <= 8192 or depth not in {1, 2, 4, 8, 16} or color not in {0, 2, 3, 4, 6} or compression or filtering or interlace not in {0, 1}:
                return False
            seen_header = True
        elif kind == b"IDAT":
            compressed.extend(body)
            seen_data = True
        elif kind == b"IEND":
            if size or end != len(data) or not seen_data:
                return False
            decoder = zlib.decompressobj()
            decoded = decoder.decompress(bytes(compressed), 100 * 1024 * 1024 + 1)
            return bool(decoded) and len(decoded) <= 100 * 1024 * 1024 and decoder.eof and not decoder.unused_data
        offset = end
    return False


def valid_raster(path: Path) -> bool:
    try:
        if not 0 < path.stat().st_size <= 25 * 1024 * 1024:
            return False
        data = path.read_bytes()
        if path.suffix.lower() == ".png":
            return valid_png(data)
        if path.suffix.lower() in {".jpg", ".jpeg"}:
            return data.startswith(b"\xff\xd8\xff") and data.endswith(b"\xff\xd9") and b"\xff\xda" in data and any(bytes((255, marker)) in data for marker in (192, 193, 194))
        if path.suffix.lower() == ".webp":
            return len(data) >= 20 and data[:4] == b"RIFF" and data[8:12] == b"WEBP" and int.from_bytes(data[4:8], "little") + 8 == len(data) and data[12:16] in {b"VP8 ", b"VP8L", b"VP8X"} and int.from_bytes(data[16:20], "little") <= len(data) - 20
    except (OSError, ValueError, zlib.error):
        return False
    return False
