#!/usr/bin/env python3

import csv
import hashlib
import math
import struct
from collections import Counter
from pathlib import Path


COMPONENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = COMPONENT_DIR.parents[1]

EXPECTED_MOCK_BOUNDS = {
    "luckfox-pico-ultra-w-envelope.stl": ((0, 0, 0), (50, 50, 15.10)),
    "sc3336-camera-b-envelope.stl": ((0, 0, 0), (25, 24, 25.95)),
    "pololu-4762-encoder-cable-envelope.stl": ((0, 0, 0), (120, 9, 2.90)),
    "adafruit-4755-bq24074-envelope.stl": ((0, 0, 0), (38.10, 33.02, 10.10)),
    "godiymodules-i2chub-envelope.stl": ((-3.0, 0, 0), (55.0, 30.0, 12.0)),
    "sherman-charging-interlock-rev-a-envelope.stl": (
        (0, 0, 0),
        (38.10, 24.13, 11.60),
    ),
}


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def read_stl(path: Path) -> list[tuple[tuple[float, float, float], ...]]:
    data = path.read_bytes()
    if data.startswith(b"solid"):
        vertices = []
        for line in data.decode("ascii").splitlines():
            fields = line.strip().split()
            if fields and fields[0] == "vertex":
                vertices.append(tuple(map(float, fields[1:4])))
        if not vertices or len(vertices) % 3:
            raise ValueError(f"Malformed ASCII STL: {path}")
        return [tuple(vertices[i : i + 3]) for i in range(0, len(vertices), 3)]

    if len(data) < 84:
        raise ValueError(f"Malformed binary STL: {path}")
    triangle_count = struct.unpack("<I", data[80:84])[0]
    if len(data) != 84 + triangle_count * 50:
        raise ValueError(f"Binary STL size mismatch: {path}")
    triangles = []
    for offset in range(84, len(data), 50):
        values = struct.unpack("<12fH", data[offset : offset + 50])
        triangles.append(
            (
                tuple(values[3:6]),
                tuple(values[6:9]),
                tuple(values[9:12]),
            )
        )
    return triangles


def validate_mock(path: Path, expected_bounds) -> None:
    triangles = read_stl(path)
    vertices = [vertex for triangle in triangles for vertex in triangle]
    minimum = tuple(min(vertex[axis] for vertex in vertices) for axis in range(3))
    maximum = tuple(max(vertex[axis] for vertex in vertices) for axis in range(3))
    for actual, expected in zip(minimum + maximum, sum(expected_bounds, ())):
        if not math.isclose(actual, expected, abs_tol=1e-4):
            raise ValueError(
                f"Unexpected bounds for {path.name}: {minimum}..{maximum}; "
                f"expected {expected_bounds[0]}..{expected_bounds[1]}"
            )

    def quantize(vertex):
        return tuple(round(value, 5) for value in vertex)

    edges = Counter()
    for triangle in triangles:
        for start, end in (
            (triangle[0], triangle[1]),
            (triangle[1], triangle[2]),
            (triangle[2], triangle[0]),
        ):
            edges[tuple(sorted((quantize(start), quantize(end))))] += 1
    bad_edges = [edge for edge, count in edges.items() if count != 2]
    if bad_edges:
        raise ValueError(f"Non-manifold edges in {path.name}: {len(bad_edges)}")


def validate_hashes(path: Path) -> None:
    for line in path.read_text(encoding="utf-8").splitlines():
        expected, relative_path = line.split("  ", 1)
        artifact = REPO_ROOT / relative_path
        actual = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"SHA-256 mismatch: {relative_path}")


def validate_power_board_manifest(path: Path) -> int:
    rows = read_manifest(path)
    names = [row["component"] for row in rows]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate component in power-board-manifest.csv")

    quantities = {}
    for row in rows:
        quantity = int(row["quantity"])
        if quantity <= 0:
            raise ValueError(f"Invalid power-board quantity for {row['component']}")
        model = COMPONENT_DIR / row["model"]
        if not model.is_file():
            raise FileNotFoundError(model)
        quantities[row["component"]] = quantity

    required = {
        "Adafruit BQ24074 charger #4755": 1,
        "Sherman charge-interlock Rev A": 1,
    }
    if quantities != required:
        raise ValueError("Power-board manifest must contain only the carried boards")
    for component, quantity in required.items():
        if quantities.get(component) != quantity:
            raise ValueError(
                f"Carried manifest must contain exactly {quantity} {component}"
            )
    if any("#4410" in component for component in quantities):
        raise ValueError("Bench-only Adafruit #4410 must not be carried")
    return len(rows)


def main() -> None:
    bom = read_manifest(REPO_ROOT / "docs/hardware/shopping-list.csv")
    manifest = read_manifest(COMPONENT_DIR / "manifest.csv")
    bom_rows = [(row["sku"], row["part"], row["quantity"]) for row in bom]
    model_rows = [
        (row["bom_sku"], row["component"], row["quantity"]) for row in manifest
    ]
    if bom_rows != model_rows:
        raise ValueError("Component manifest no longer matches the shopping list")

    for row in manifest:
        for field in ("primary_model", "alternate_model"):
            if row[field] and not (COMPONENT_DIR / row[field]).is_file():
                raise FileNotFoundError(row[field])

    step_files = sorted(COMPONENT_DIR.joinpath("step").glob("*.step"))
    step_files += sorted(COMPONENT_DIR.joinpath("step").glob("*.stp"))
    for path in step_files:
        data = path.read_bytes()
        if not data.startswith(b"ISO-10303-21;"):
            raise ValueError(f"Missing STEP header: {path.name}")
        if b"END-ISO-10303-21;" not in data[-4096:]:
            raise ValueError(f"Missing STEP terminator: {path.name}")

    for path in sorted(COMPONENT_DIR.joinpath("stl").glob("*.stl")):
        read_stl(path)
    for name, bounds in EXPECTED_MOCK_BOUNDS.items():
        validate_mock(COMPONENT_DIR / "stl" / name, bounds)

    validate_hashes(COMPONENT_DIR / "SHA256SUMS")
    power_board_rows = validate_power_board_manifest(
        COMPONENT_DIR / "power-board-manifest.csv"
    )
    print(
        f"Validated {len(manifest)} BOM rows, {len(step_files)} STEP/STP files, "
        f"{len(list(COMPONENT_DIR.joinpath('stl').glob('*.stl')))} STL files, "
        f"6 manifold mock envelopes, and {power_board_rows} carried power boards."
    )


if __name__ == "__main__":
    main()
