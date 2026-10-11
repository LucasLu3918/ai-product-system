"""Bounded structural inspection for MPEG-4 audio publication candidates."""

from __future__ import annotations

from dataclasses import dataclass

MAX_M4A_BYTES = 8 * 1024 * 1024
M4A_BRANDS = {b"M4A ", b"M4B ", b"M4P "}
CONTAINER_ATOMS = {b"moov", b"trak", b"mdia", b"minf", b"stbl", b"udta", b"ilst", b"edts", b"dinf"}


class M4AInspectionError(ValueError):
    """The file is too large or is not a structurally valid M4A audio file."""


@dataclass(frozen=True)
class M4AInspection:
    metadata: bytes
    major_brand: bytes


def _boxes(data: bytes, start: int, end: int):
    offset = start
    while offset < end:
        if end - offset < 8:
            raise M4AInspectionError("truncated MP4 atom header")
        size = int.from_bytes(data[offset:offset + 4], "big")
        atom_type = data[offset + 4:offset + 8]
        header_size = 8
        if size == 1:
            if end - offset < 16:
                raise M4AInspectionError("truncated extended MP4 atom header")
            size = int.from_bytes(data[offset + 8:offset + 16], "big")
            header_size = 16
        elif size == 0:
            size = end - offset
        if size < header_size or size > end - offset:
            raise M4AInspectionError("invalid MP4 atom size")
        yield atom_type, offset + header_size, offset + size
        offset += size


def inspect_m4a(data: bytes) -> M4AInspection:
    """Validate a bounded M4A container and return moov bytes for text scanning."""
    if len(data) > MAX_M4A_BYTES:
        raise M4AInspectionError("M4A exceeds the 8 MiB publication limit")
    top = list(_boxes(data, 0, len(data)))
    if not top or top[0][0] != b"ftyp":
        raise M4AInspectionError("M4A must start with an ftyp atom")
    _, ftyp_start, ftyp_end = top[0]
    ftyp = data[ftyp_start:ftyp_end]
    if len(ftyp) < 8 or (len(ftyp) - 8) % 4:
        raise M4AInspectionError("invalid ftyp atom")
    brands = {ftyp[:4], *(ftyp[index:index + 4] for index in range(8, len(ftyp), 4))}
    major = ftyp[:4]
    if not (brands & M4A_BRANDS):
        raise M4AInspectionError("file extension does not match an M4A-compatible brand")
    atoms = {atom_type for atom_type, _, _ in top}
    if b"moov" not in atoms or b"mdat" not in atoms:
        raise M4AInspectionError("M4A requires both moov and mdat atoms")
    metadata = b"\n".join(data[start:end] for atom_type, start, end in top if atom_type == b"moov")
    return M4AInspection(metadata=metadata, major_brand=major)


def metadata_text(data: bytes) -> str:
    """Keep readable metadata bytes and separators; discard binary atom fields."""
    decoded = data.decode("utf-8", errors="ignore").replace("\x00", " ")
    return "".join(char if char.isprintable() or char in "\r\n\t" else " " for char in decoded)
