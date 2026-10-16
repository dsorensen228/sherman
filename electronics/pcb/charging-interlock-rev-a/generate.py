#!/usr/bin/env python3
"""Generate and verify the Sherman charge-interlock Rev A PCB.

The board is intentionally simple and through-hole.  This file is the editable
source of truth for placement, net assignment, routing, KiCad PCB source, and
the fabrication package.  Files carrying a GENERATED header must not be hand
edited.
"""

from __future__ import annotations

import csv
import heapq
import json
import math
import shutil
import zipfile
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path


HERE = Path(__file__).resolve().parent
FAB = HERE / "fabrication"
NAME = "charging-interlock-rev-a"
MM_PER_MIL = 0.0254
BOARD_W = 1500
BOARD_H = 950
GRID = 10
EDGE_KEEPOUT = 50
CLEARANCE = 12  # 0.3048 mm
ROUTER_MARGIN = 10  # Covers diagonal-grid corner cutting; not a fab requirement.
SIGNAL_WIDTH = 16  # 0.4064 mm
SUPPLY_WIDTH = 24  # 0.6096 mm
VIA_DIAMETER = 50  # 1.27 mm
VIA_DRILL = 24  # 0.6096 mm
LAYERS = ("F.Cu", "B.Cu")


@dataclass(frozen=True)
class Pad:
    ref: str
    number: str
    x: int
    y: int
    net: str
    diameter: int = 64
    drill: int = 32
    square: bool = False


@dataclass(frozen=True)
class Component:
    ref: str
    value: str
    footprint: str
    pads: tuple[Pad, ...]
    description: str


@dataclass(frozen=True)
class Segment:
    net: str
    layer: str
    x1: int
    y1: int
    x2: int
    y2: int
    width: int


@dataclass(frozen=True)
class Via:
    net: str
    x: int
    y: int


def p(ref: str, number: int | str, x: int, y: int, net: str, *, header: bool = False) -> Pad:
    return Pad(
        ref,
        str(number),
        x,
        y,
        net,
        diameter=70 if header else 64,
        drill=40 if header else 32,
        square=str(number) == "1",
    )


def build_components() -> list[Component]:
    # U1 is viewed from the component side.  Pin 1 is the lower-left square pad;
    # the package notch is at the left end.  Q1 follows onsemi 2N3904BU E-B-C.
    u1_pads = tuple(
        [p("U1", pin, 400 + (pin - 1) * 100, 320, net) for pin, net in enumerate(
            ("GP3", "CHARGE_ABSENT", "RAIL_EN", "GP12", "CHARGE_ABSENT", "SLEEP_EN", "GND"), 1
        )]
        + [p("U1", pin, 1000 - (pin - 8) * 100, 620, net) for pin, net in enumerate(
            ("NC8", "GND", "GND", "NC11", "GND", "GND", "3V3"), 8
        )]
    )
    return [
        Component("U1", "SN74HC08N", "DIP-14_W7.62mm_Socket", u1_pads, "Quad 2-input AND gate, TI SN74HC08N"),
        Component("Q1", "2N3904BU", "TO-92_Inline", (
            p("Q1", 1, 1000, 520, "GND"),
            p("Q1", 2, 1100, 520, "QBASE"),
            p("Q1", 3, 1200, 520, "CHARGE_ABSENT"),
        ), "onsemi 2N3904BU; pin 1 E, 2 B, 3 C"),
        Component("C1", "100nF", "C_Disc_D5.0mm_W2.5mm_P2.54mm", (
            p("C1", 1, 330, 650, "3V3"), p("C1", 2, 330, 550, "GND")
        ), "100 nF X7R bypass capacitor"),
        Component("R1", "10k", "R_Axial_Vertical_P2.54mm", (
            p("R1", 1, 150, 720, "3V3"), p("R1", 2, 250, 720, "CHARGE_ABSENT")
        ), "CHARGE_ABSENT pull-up"),
        Component("R2", "47k", "R_Axial_Vertical_P2.54mm", (
            p("R2", 1, 1000, 700, "VBUS"), p("R2", 2, 1100, 700, "QBASE")
        ), "VBUS-to-Q1 base resistor"),
        Component("R3", "100k", "R_Axial_Vertical_P2.54mm", (
            p("R3", 1, 1200, 700, "QBASE"), p("R3", 2, 1300, 700, "GND")
        ), "Q1 base-emitter pull-down"),
        Component("R4", "10k", "R_Axial_Vertical_P2.54mm", (
            p("R4", 1, 250, 550, "GP3"), p("R4", 2, 150, 550, "GND")
        ), "GP3 request pull-down"),
        Component("R5", "10k", "R_Axial_Vertical_P2.54mm", (
            p("R5", 1, 250, 400, "RAIL_EN"), p("R5", 2, 150, 400, "GND")
        ), "Motor-gate output pull-down"),
        Component("R6", "10k", "R_Axial_Vertical_P2.54mm", (
            p("R6", 1, 250, 250, "GP12"), p("R6", 2, 150, 250, "GND")
        ), "GP12 request pull-down"),
        Component("R7", "4.7k", "R_Axial_Vertical_P2.54mm", (
            p("R7", 1, 1100, 220, "SLEEP_EN"), p("R7", 2, 1200, 220, "GND")
        ), "DRV8833 sleep output pull-down"),
        Component("J1", "PICO", "PinHeader_1x05_P2.54mm_Vertical", tuple(
            p("J1", pin, 250 + (pin - 1) * 100, 820, net, header=True)
            for pin, net in enumerate(("3V3", "GND", "GP3", "GP12", "CHARGE_ABSENT"), 1)
        ), "Pico harness: 3V3, GND, GP3, GP12, CHARGE_ABSENT/GP6"),
        Component("J2", "CHARGER", "PinHeader_1x03_P2.54mm_Vertical", tuple(
            p("J2", pin, 1050 + (pin - 1) * 100, 820, net, header=True)
            for pin, net in enumerate(("VBUS", "CHARGE_ABSENT", "GND"), 1)
        ), "Adafruit #4755 harness: VBUS, PGOOD, GND"),
        Component("J3", "OUTPUTS", "PinHeader_1x03_P2.54mm_Vertical", tuple(
            p("J3", pin, 550 + (pin - 1) * 100, 110, net, header=True)
            for pin, net in enumerate(("RAIL_EN", "SLEEP_EN", "GND"), 1)
        ), "Outputs: #2808-M CTRL, DRV8833 SLP, GND"),
    ]


COMPONENTS = build_components()
PADS = tuple(pad for component in COMPONENTS for pad in component.pads)
MOUNTS = ((100, 100), (1400, 100), (100, 850), (1400, 850))
NETS = tuple(sorted({pad.net for pad in PADS if not pad.net.startswith("NC")}))


def sq_distance_point_segment(px: float, py: float, segment: Segment) -> float:
    ax, ay, bx, by = segment.x1, segment.y1, segment.x2, segment.y2
    vx, vy = bx - ax, by - ay
    if vx == 0 and vy == 0:
        return (px - ax) ** 2 + (py - ay) ** 2
    t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy)))
    dx, dy = px - (ax + t * vx), py - (ay + t * vy)
    return dx * dx + dy * dy


def orientation(a: tuple[int, int], b: tuple[int, int], c: tuple[int, int]) -> int:
    value = (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1])
    return 0 if value == 0 else (1 if value > 0 else 2)


def segments_intersect(a: Segment, b: Segment) -> bool:
    p1, q1 = (a.x1, a.y1), (a.x2, a.y2)
    p2, q2 = (b.x1, b.y1), (b.x2, b.y2)
    return (
        orientation(p1, q1, p2) != orientation(p1, q1, q2)
        and orientation(p2, q2, p1) != orientation(p2, q2, q1)
    )


def segment_distance(a: Segment, b: Segment) -> float:
    if segments_intersect(a, b):
        return 0.0
    distances = (
        sq_distance_point_segment(a.x1, a.y1, b),
        sq_distance_point_segment(a.x2, a.y2, b),
        sq_distance_point_segment(b.x1, b.y1, a),
        sq_distance_point_segment(b.x2, b.y2, a),
    )
    return math.sqrt(min(distances))


def route_board() -> tuple[list[Segment], list[Via]]:
    pads_by_net: dict[str, list[Pad]] = defaultdict(list)
    for pad in PADS:
        if not pad.net.startswith("NC"):
            pads_by_net[pad.net].append(pad)

    segments: list[Segment] = []
    vias: list[Via] = []
    route_order = (
        "CHARGE_ABSENT", "GND", "3V3", "GP3", "GP12", "RAIL_EN",
        "SLEEP_EN", "QBASE", "VBUS",
    )
    terminal_priority = {
        "CHARGE_ABSENT": ("J1.5", "J2.2", "R1.2", "U1.5", "U1.2", "Q1.3"),
    }

    def allowed(net: str, layer: str, x: int, y: int, width: int, changing_layer: bool = False) -> bool:
        if x < EDGE_KEEPOUT or x > BOARD_W - EDGE_KEEPOUT or y < EDGE_KEEPOUT or y > BOARD_H - EDGE_KEEPOUT:
            return False
        for mx, my in MOUNTS:
            if math.hypot(x - mx, y - my) < 44 + CLEARANCE + ROUTER_MARGIN + width / 2:
                return False
        for pad in PADS:
            if pad.net == net or pad.net.startswith("NC"):
                continue
            if math.hypot(x - pad.x, y - pad.y) < pad.diameter / 2 + CLEARANCE + ROUTER_MARGIN + width / 2:
                return False
        for segment in segments:
            if segment.net == net or (segment.layer != layer and not changing_layer):
                continue
            probe = Segment(net, layer, x, y, x, y, width)
            if segment_distance(probe, segment) < width / 2 + segment.width / 2 + CLEARANCE + ROUTER_MARGIN:
                return False
        for via in vias:
            if via.net == net:
                continue
            if math.hypot(x - via.x, y - via.y) < width / 2 + VIA_DIAMETER / 2 + CLEARANCE + ROUTER_MARGIN:
                return False
        return True

    def astar(net: str, starts: set[tuple[int, int, int]], targets: set[tuple[int, int, int]], width: int) -> list[tuple[int, int, int]]:
        target_xy = {(x, y) for x, y, _ in targets}
        queue: list[tuple[float, int, tuple[int, int, int]]] = []
        previous: dict[tuple[int, int, int], tuple[int, int, int] | None] = {}
        cost: dict[tuple[int, int, int], float] = {}
        serial = 0

        def heuristic(x: int, y: int) -> float:
            return min(abs(x - tx) + abs(y - ty) for tx, ty in target_xy)

        for start in starts:
            previous[start] = None
            cost[start] = 0.0
            heapq.heappush(queue, (heuristic(start[0], start[1]), serial, start))
            serial += 1

        moves = (
            (GRID, 0, float(GRID)), (-GRID, 0, float(GRID)),
            (0, GRID, float(GRID)), (0, -GRID, float(GRID)),
            (GRID, GRID, GRID * math.sqrt(2)), (GRID, -GRID, GRID * math.sqrt(2)),
            (-GRID, GRID, GRID * math.sqrt(2)), (-GRID, -GRID, GRID * math.sqrt(2)),
        )
        while queue:
            _, _, node = heapq.heappop(queue)
            if node in targets:
                path: list[tuple[int, int, int]] = []
                cursor: tuple[int, int, int] | None = node
                while cursor is not None:
                    path.append(cursor)
                    cursor = previous[cursor]
                return list(reversed(path))
            x, y, layer_index = node
            layer = LAYERS[layer_index]
            neighbors = [(x + dx, y + dy, layer_index, step) for dx, dy, step in moves]
            neighbors.append((x, y, 1 - layer_index, 120.0))
            for nx, ny, next_layer, step_cost in neighbors:
                candidate = (nx, ny, next_layer)
                changing = next_layer != layer_index
                if candidate not in targets and candidate not in starts and not allowed(
                    net, LAYERS[next_layer], nx, ny, width if not changing else VIA_DIAMETER, changing
                ):
                    continue
                turn_penalty = 0.0
                parent = previous.get(node)
                if parent is not None and not changing:
                    old_dx, old_dy = x - parent[0], y - parent[1]
                    new_dx, new_dy = nx - x, ny - y
                    if (old_dx, old_dy) != (new_dx, new_dy):
                        turn_penalty = 4.0
                new_cost = cost[node] + step_cost + turn_penalty
                if new_cost >= cost.get(candidate, float("inf")):
                    continue
                cost[candidate] = new_cost
                previous[candidate] = node
                heapq.heappush(queue, (new_cost + heuristic(nx, ny), serial, candidate))
                serial += 1
        reached_xy = {(x, y) for x, y, _ in cost}
        nearest = min(
            (abs(x - tx) + abs(y - ty), (x, y), (tx, ty))
            for x, y in reached_xy for tx, ty in target_xy
        )
        raise RuntimeError(
            f"unable to route {net}; explored={len(cost)}, nearest={nearest}"
        )

    for net in route_order:
        terminals = pads_by_net[net]
        if net in terminal_priority:
            order = {endpoint: index for index, endpoint in enumerate(terminal_priority[net])}
            terminals = sorted(terminals, key=lambda pad: order[f"{pad.ref}.{pad.number}"])
        width = SUPPLY_WIDTH if net in {"GND", "3V3", "VBUS"} else SIGNAL_WIDTH
        tree = {(terminals[0].x, terminals[0].y, 0), (terminals[0].x, terminals[0].y, 1)}
        connected_pads = {terminals[0]}
        for terminal in terminals[1:]:
            targets = set(tree)
            starts = {(terminal.x, terminal.y, 0), (terminal.x, terminal.y, 1)}
            try:
                path = astar(net, starts, targets, width)
            except RuntimeError as exc:
                raise RuntimeError(
                    f"{exc}; failed terminal {terminal.ref}.{terminal.number} "
                    f"at ({terminal.x}, {terminal.y}), tree nodes={len(tree)}"
                ) from exc
            connected_pads.add(terminal)
            tree.update(path)

            run_start = path[0]
            previous_node = path[0]
            direction: tuple[int, int, int] | None = None
            for node in path[1:]:
                if node[2] != previous_node[2]:
                    if previous_node != run_start:
                        segments.append(Segment(net, LAYERS[run_start[2]], run_start[0], run_start[1], previous_node[0], previous_node[1], width))
                    vias.append(Via(net, node[0], node[1]))
                    run_start = node
                    direction = None
                    previous_node = node
                    continue
                new_direction = (node[0] - previous_node[0], node[1] - previous_node[1], node[2])
                if direction is not None and new_direction != direction:
                    segments.append(Segment(net, LAYERS[run_start[2]], run_start[0], run_start[1], previous_node[0], previous_node[1], width))
                    run_start = previous_node
                direction = new_direction
                previous_node = node
            if previous_node != run_start:
                segments.append(Segment(net, LAYERS[run_start[2]], run_start[0], run_start[1], previous_node[0], previous_node[1], width))
    return segments, vias


def validate(segments: list[Segment], vias: list[Via]) -> dict[str, int | float]:
    errors: list[str] = []

    for index, a in enumerate(PADS):
        if a.x - a.diameter / 2 < 0 or a.x + a.diameter / 2 > BOARD_W or a.y - a.diameter / 2 < 0 or a.y + a.diameter / 2 > BOARD_H:
            errors.append(f"pad outside board: {a.ref}.{a.number}")
        for b in PADS[index + 1:]:
            if math.hypot(a.x - b.x, a.y - b.y) < a.diameter / 2 + b.diameter / 2 + CLEARANCE and a.net != b.net:
                errors.append(f"pad clearance: {a.ref}.{a.number} to {b.ref}.{b.number}")

    for index, a in enumerate(segments):
        for b in segments[index + 1:]:
            if a.layer == b.layer and a.net != b.net:
                required = a.width / 2 + b.width / 2 + CLEARANCE
                actual = segment_distance(a, b)
                if actual + 1e-6 < required:
                    errors.append(f"track clearance {actual:.1f}<{required:.1f}: {a.net} to {b.net} on {a.layer}")
        for pad in PADS:
            if pad.net == a.net or pad.net.startswith("NC"):
                continue
            required = a.width / 2 + pad.diameter / 2 + CLEARANCE
            actual = math.sqrt(sq_distance_point_segment(pad.x, pad.y, a))
            if actual + 1e-6 < required:
                errors.append(f"track-pad clearance {actual:.1f}<{required:.1f}: {a.net} to {pad.ref}.{pad.number}")

    # Connectivity is checked on a 10-mil raster.  This recognizes T-junctions
    # where a later branch lands in the middle of an existing copper segment.
    adjacency: dict[tuple[str, int, int], set[tuple[str, int, int]]] = defaultdict(set)
    for segment in segments:
        dx, dy = segment.x2 - segment.x1, segment.y2 - segment.y1
        steps = max(abs(dx), abs(dy)) // GRID
        raster = [
            (segment.layer, segment.x1 + (dx // steps) * index, segment.y1 + (dy // steps) * index)
            for index in range(steps + 1)
        ] if steps else [(segment.layer, segment.x1, segment.y1)]
        for a, b in zip(raster, raster[1:]):
            adjacency[a].add(b)
            adjacency[b].add(a)
    for via in vias:
        a, b = ("F.Cu", via.x, via.y), ("B.Cu", via.x, via.y)
        adjacency[a].add(b)
        adjacency[b].add(a)
    for pad in PADS:
        if pad.net.startswith("NC"):
            continue
        a, b = ("F.Cu", pad.x, pad.y), ("B.Cu", pad.x, pad.y)
        adjacency[a].add(b)
        adjacency[b].add(a)
    for net in NETS:
        terminals = [("F.Cu", pad.x, pad.y) for pad in PADS if pad.net == net]
        reached = set()
        queue = deque([terminals[0]])
        while queue:
            node = queue.popleft()
            if node in reached:
                continue
            reached.add(node)
            queue.extend(adjacency[node] - reached)
        for terminal in terminals:
            if terminal not in reached:
                errors.append(f"unrouted net {net} at {terminal[1:]}")

    if errors:
        raise AssertionError("PCB verification failed:\n" + "\n".join(sorted(set(errors))))
    return {
        "board_width_mm": round(BOARD_W * MM_PER_MIL, 3),
        "board_height_mm": round(BOARD_H * MM_PER_MIL, 3),
        "components": len(COMPONENTS),
        "pads": len(PADS),
        "nets": len(NETS),
        "segments": len(segments),
        "vias": len(vias),
        "minimum_clearance_mm": round(CLEARANCE * MM_PER_MIL, 4),
        "signal_width_mm": round(SIGNAL_WIDTH * MM_PER_MIL, 4),
        "supply_width_mm": round(SUPPLY_WIDTH * MM_PER_MIL, 4),
    }


def mm(value: int | float) -> str:
    return f"{value * MM_PER_MIL:.4f}".rstrip("0").rstrip(".")


def kicad_text(text: str, x: int, y: int, *, size: float = 1.0, justify: str = "") -> str:
    justify_clause = f" (justify {justify})" if justify else ""
    return f'  (gr_text "{text}" (at {mm(x)} {mm(y)}) (layer "F.SilkS") (effects (font (size {size} {size}) (thickness 0.15)){justify_clause}))\n'


def write_kicad(segments: list[Segment], vias: list[Via]) -> None:
    net_numbers = {net: index for index, net in enumerate(NETS, 1)}
    lines = [
        "(kicad_pcb (version 20240108) (generator sherman_interlock_generator)\n",
        "  (general (thickness 1.6))\n",
        '  (paper "A4")\n',
        "  (layers\n",
        '    (0 "F.Cu" signal)\n    (31 "B.Cu" signal)\n',
        '    (36 "B.SilkS" user "b.silkscreen")\n    (37 "F.SilkS" user "f.silkscreen")\n',
        '    (44 "Edge.Cuts" user)\n  )\n',
        "  (setup (pad_to_mask_clearance 0))\n",
    ]
    for net, number in net_numbers.items():
        lines.append(f'  (net {number} "{net}")\n')

    for component in COMPONENTS:
        cx = sum(pad.x for pad in component.pads) / len(component.pads)
        cy = sum(pad.y for pad in component.pads) / len(component.pads)
        lines.append(f'  (footprint "Sherman:{component.footprint}" (layer "F.Cu") (at 0 0)\n')
        lines.append(f'    (property "Reference" "{component.ref}" (at {mm(cx)} {mm(cy - 55)}) (layer "F.SilkS") (effects (font (size 0.9 0.9) (thickness 0.15))))\n')
        lines.append(f'    (property "Value" "{component.value}" (at {mm(cx)} {mm(cy + 55)}) (layer "F.Fab") hide (effects (font (size 0.8 0.8) (thickness 0.12))))\n')
        for pad in component.pads:
            shape = "rect" if pad.square else "circle"
            lines.append(
                f'    (pad "{pad.number}" thru_hole {shape} (at {mm(pad.x)} {mm(pad.y)}) '
                f'(size {mm(pad.diameter)} {mm(pad.diameter)}) (drill {mm(pad.drill)}) '
                f'(layers "*.Cu" "*.Mask") (net {net_numbers.get(pad.net, 0)} "{pad.net if not pad.net.startswith("NC") else ""}"))\n'
            )
        if component.ref == "U1":
            lines.extend([
                f'    (fp_rect (start {mm(350)} {mm(275)}) (end {mm(1050)} {mm(665)}) (stroke (width 0.15) (type default)) (fill none) (layer "F.SilkS"))\n',
                f'    (fp_arc (start {mm(350)} {mm(430)}) (mid {mm(400)} {mm(470)}) (end {mm(350)} {mm(510)}) (stroke (width 0.15) (type default)) (fill none) (layer "F.SilkS"))\n',
            ])
        lines.append("  )\n")

    for segment in segments:
        lines.append(
            f'  (segment (start {mm(segment.x1)} {mm(segment.y1)}) (end {mm(segment.x2)} {mm(segment.y2)}) '
            f'(width {mm(segment.width)}) (layer "{segment.layer}") (net {net_numbers[segment.net]}))\n'
        )
    for via in vias:
        lines.append(
            f'  (via (at {mm(via.x)} {mm(via.y)}) (size {mm(VIA_DIAMETER)}) (drill {mm(VIA_DRILL)}) '
            f'(layers "F.Cu" "B.Cu") (net {net_numbers[via.net]}))\n'
        )
    lines.extend([
        f'  (gr_rect (start 0 0) (end {mm(BOARD_W)} {mm(BOARD_H)}) (stroke (width 0.1) (type default)) (fill none) (layer "Edge.Cuts"))\n',
        kicad_text("SHERMAN CHARGE INTERLOCK", 750, 910, size=0.85),
        kicad_text("REV A", 1370, 500, size=0.8),
        kicad_text("3V3  GND  GP3  GP12  CA", 450, 905, size=0.65),
        kicad_text("VBUS PGOOD GND", 1150, 905, size=0.65),
        kicad_text("RAIL  SLEEP  GND", 650, 55, size=0.65),
    ])
    for mx, my in MOUNTS:
        lines.append(
            f'  (footprint "Sherman:MountingHole_2.2mm" (layer "F.Cu") (at 0 0) '
            f'(pad "" np_thru_hole circle (at {mm(mx)} {mm(my)}) (size 2.2 2.2) (drill 2.2) (layers "*.Cu" "*.Mask")))\n'
        )
    lines.append(")\n")
    (HERE / f"{NAME}.kicad_pcb").write_text("".join(lines), encoding="utf-8")


def gerber_header(name: str) -> list[str]:
    return [
        f"G04 GENERATED by {Path(__file__).name}; do not hand edit*\n",
        f"G04 {name}*\n",
        "%FSLAX46Y46*%\n%MOMM*%\n%IPPOS*%\n%LPD*%\n",
    ]


def gerber_xy(x: int, y: int) -> str:
    return f"X{round(x * MM_PER_MIL * 1_000_000):010d}Y{round((BOARD_H - y) * MM_PER_MIL * 1_000_000):010d}"


def write_copper(path: Path, layer: str, segments: list[Segment], vias: list[Via]) -> None:
    lines = gerber_header(layer)
    apertures: dict[tuple[str, int], int] = {}
    next_d = 10
    for shape, size in sorted({("C", SIGNAL_WIDTH), ("C", SUPPLY_WIDTH), ("C", 64), ("C", 70), ("R", 64), ("R", 70), ("C", VIA_DIAMETER)}):
        apertures[(shape, size)] = next_d
        if shape == "C":
            lines.append(f"%ADD{next_d}C,{mm(size)}*%\n")
        else:
            lines.append(f"%ADD{next_d}R,{mm(size)}X{mm(size)}*%\n")
        next_d += 1
    current = None
    for pad in PADS:
        key = ("R" if pad.square else "C", pad.diameter)
        d = apertures[key]
        if d != current:
            lines.append(f"D{d}*\n")
            current = d
        lines.append(f"{gerber_xy(pad.x, pad.y)}D03*\n")
    d = apertures[("C", VIA_DIAMETER)]
    if d != current:
        lines.append(f"D{d}*\n")
        current = d
    for via in vias:
        lines.append(f"{gerber_xy(via.x, via.y)}D03*\n")
    for segment in (item for item in segments if item.layer == layer):
        d = apertures[("C", segment.width)]
        if d != current:
            lines.append(f"D{d}*\n")
            current = d
        lines.append(f"{gerber_xy(segment.x1, segment.y1)}D02*\n{gerber_xy(segment.x2, segment.y2)}D01*\n")
    lines.append("M02*\n")
    path.write_text("".join(lines), encoding="ascii")


def write_mask(path: Path, side: str) -> None:
    lines = gerber_header(f"{side} solder mask")
    sizes = sorted({pad.diameter + 12 for pad in PADS})
    apertures = {size: index + 10 for index, size in enumerate(sizes)}
    for size, d in apertures.items():
        lines.append(f"%ADD{d}C,{mm(size)}*%\n")
    for pad in PADS:
        lines.append(f"D{apertures[pad.diameter + 12]}*\n{gerber_xy(pad.x, pad.y)}D03*\n")
    lines.append("M02*\n")
    path.write_text("".join(lines), encoding="ascii")


FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01110"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
}


def silk_text(lines: list[str], text: str, center_x: int, bottom_y: int, *, cell: int = 9) -> None:
    width = sum((5 + 1) * cell for _ in text) - cell
    left = center_x - width // 2
    for char_index, char in enumerate(text.upper()):
        glyph = FONT.get(char)
        if glyph is None:
            continue
        x0 = left + char_index * 6 * cell
        for row, bitmap in enumerate(glyph):
            for column, bit in enumerate(bitmap):
                if bit == "1":
                    # Gerber Y increases upward while the board source uses a
                    # top-view, screen-style Y axis.  gerber_xy() performs the
                    # axis conversion, so rows progress directly here.
                    lines.append(f"{gerber_xy(x0 + column * cell, bottom_y + row * cell)}D03*\n")


def write_silkscreen(path: Path) -> None:
    lines = gerber_header("Front silkscreen")
    lines.append("%ADD10C,0.1524*%\nD10*\n")
    # Two-character functional abbreviations remain legible at 0.1-inch pitch;
    # long adjacent words merged in prototype renders and are therefore kept
    # in the assembly drawing/connector table instead of the production silk.
    for label, x in zip(("3V", "G", "G3", "12", "CA"), (250, 350, 450, 550, 650)):
        silk_text(lines, label, x, 880, cell=6)
    for label, x in zip(("VB", "PG", "G"), (1050, 1150, 1250)):
        silk_text(lines, label, x, 880, cell=6)
    for label, x in zip(("R", "S", "G"), (550, 650, 750)):
        silk_text(lines, label, x, 15, cell=6)
    silk_text(lines, "REV-A", 1360, 440, cell=7)
    silk_text(lines, "U1", 700, 450, cell=8)
    silk_text(lines, "Q1", 1110, 555, cell=7)
    # U1 body, notch, and pin-1 mark.
    lines.extend([
        f"{gerber_xy(350, 275)}D02*\n{gerber_xy(1050, 275)}D01*\n",
        f"{gerber_xy(1050, 275)}D02*\n{gerber_xy(1050, 665)}D01*\n",
        f"{gerber_xy(1050, 665)}D02*\n{gerber_xy(350, 665)}D01*\n",
        f"{gerber_xy(350, 665)}D02*\n{gerber_xy(350, 525)}D01*\n",
        f"{gerber_xy(350, 415)}D02*\n{gerber_xy(350, 275)}D01*\n",
    ])
    lines.append("%ADD11C,0.762*%\nD11*\n")
    lines.append(f"{gerber_xy(365, 305)}D03*\n")
    lines.append("M02*\n")
    path.write_text("".join(lines), encoding="ascii")


def write_outline(path: Path) -> None:
    lines = gerber_header("Board outline")
    lines.append("%ADD10C,0.1*%\nD10*\n")
    corners = ((0, 0), (BOARD_W, 0), (BOARD_W, BOARD_H), (0, BOARD_H), (0, 0))
    lines.append(f"{gerber_xy(*corners[0])}D02*\n")
    for corner in corners[1:]:
        lines.append(f"{gerber_xy(*corner)}D01*\n")
    lines.append("M02*\n")
    path.write_text("".join(lines), encoding="ascii")


def write_drills(vias: list[Via]) -> None:
    plated: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for pad in PADS:
        plated[pad.drill].append((pad.x, pad.y))
    for via in vias:
        plated[VIA_DRILL].append((via.x, via.y))
    lines = ["M48\n; GENERATED; plated through holes\nMETRIC,TZ\n"]
    for tool, drill in enumerate(sorted(plated), 1):
        lines.append(f"T{tool:02d}C{mm(drill)}\n")
    lines.append("%\n")
    for tool, drill in enumerate(sorted(plated), 1):
        lines.append(f"T{tool:02d}\n")
        for x, y in plated[drill]:
            lines.append(f"X{mm(x)}Y{mm(BOARD_H-y)}\n")
    lines.append("M30\n")
    (FAB / f"{NAME}-PTH.drl").write_text("".join(lines), encoding="ascii")

    lines = ["M48\n; GENERATED; non-plated mounting holes\nMETRIC,TZ\nT01C2.2\n%\nT01\n"]
    lines.extend(f"X{mm(x)}Y{mm(BOARD_H-y)}\n" for x, y in MOUNTS)
    lines.append("M30\n")
    (FAB / f"{NAME}-NPTH.drl").write_text("".join(lines), encoding="ascii")


def write_csvs() -> None:
    with (HERE / "bom.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("references", "quantity", "value", "footprint", "manufacturer_part", "notes"))
        grouped: dict[tuple[str, str, str, str], list[str]] = defaultdict(list)
        manufacturer = {
            "U1": "Texas Instruments SN74HC08N",
            "Q1": "onsemi 2N3904BU",
            "C1": "KEMET C315C104K5R5TA or equivalent X7R",
        }
        for component in COMPONENTS:
            if component.ref.startswith("J"):
                part = "2.54 mm breakaway male header"
            elif component.ref.startswith("R"):
                part = "1% axial through-hole resistor"
            else:
                part = manufacturer.get(component.ref, "")
            key = (component.value, component.footprint, part, component.description)
            grouped[key].append(component.ref)
        grouped[("14-pin DIP socket", "DIP-14_W7.62mm_Socket", "TE 1-2199298-3", "Socket for U1; install socket, then IC")].append("U1-SOCKET")
        for (value, footprint, part, notes), refs in grouped.items():
            writer.writerow((" ".join(refs), len(refs), value, footprint, part, notes))

    with (HERE / "netlist.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("net", "endpoint", "pin", "function"))
        functions = {
            "J1.1": "Pico physical pin 36 / 3V3(OUT)", "J1.2": "Pico physical pin 23 / GND",
            "J1.3": "Pico physical pin 5 / GP3", "J1.4": "Pico physical pin 16 / GP12",
            "J1.5": "Pico physical pin 9 / GP6 input-only observer",
            "J2.1": "Adafruit #4755 VBUS", "J2.2": "Adafruit #4755 PGOOD",
            "J2.3": "Adafruit #4755 GND", "J3.1": "Pololu #2808-M CTRL",
            "J3.2": "DRV8833 SLP/nSLEEP", "J3.3": "Driver/power-gate GND",
        }
        for component in COMPONENTS:
            for pad in component.pads:
                writer.writerow((pad.net, component.ref, pad.number, functions.get(f"{component.ref}.{pad.number}", component.description)))


def write_assembly_svg(segments: list[Segment], vias: list[Via]) -> None:
    scale = 20
    width = BOARD_W * MM_PER_MIL * scale
    height = BOARD_H * MM_PER_MIL * scale
    def sx(x: int) -> float: return x * MM_PER_MIL * scale
    def sy(y: int) -> float: return (BOARD_H - y) * MM_PER_MIL * scale
    colors = {"F.Cu": "#d24737", "B.Cu": "#2a62b8"}
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" viewBox="0 0 {width:.1f} {height:.1f}">',
        '<rect width="100%" height="100%" fill="#e8f0e5"/>',
        f'<rect x="1" y="1" width="{width-2:.1f}" height="{height-2:.1f}" rx="4" fill="#2e7147" stroke="#111" stroke-width="2"/>',
    ]
    for segment in segments:
        svg.append(
            f'<line x1="{sx(segment.x1):.1f}" y1="{sy(segment.y1):.1f}" x2="{sx(segment.x2):.1f}" y2="{sy(segment.y2):.1f}" '
            f'stroke="{colors[segment.layer]}" stroke-width="{max(2.0, segment.width*MM_PER_MIL*scale):.1f}" opacity="0.65"/>'
        )
    for via in vias:
        svg.append(f'<circle cx="{sx(via.x):.1f}" cy="{sy(via.y):.1f}" r="5" fill="#d8a533" stroke="#333"/>')
    for component in COMPONENTS:
        if component.ref == "U1":
            svg.append(f'<rect x="{sx(350):.1f}" y="{sy(665):.1f}" width="{sx(700):.1f}" height="{sy(275)-sy(665):.1f}" rx="8" fill="#202226" stroke="#eee"/>')
        for pad in component.pads:
            fill = "#f7d358" if pad.square else "#d8a533"
            svg.append(f'<circle cx="{sx(pad.x):.1f}" cy="{sy(pad.y):.1f}" r="9" fill="{fill}" stroke="#222" stroke-width="2"/>')
        cx = sum(pad.x for pad in component.pads) / len(component.pads)
        cy = sum(pad.y for pad in component.pads) / len(component.pads)
        svg.append(f'<text x="{sx(cx):.1f}" y="{sy(cy)-14:.1f}" fill="white" font-family="sans-serif" font-weight="bold" font-size="15" text-anchor="middle">{component.ref}</text>')
    for mx, my in MOUNTS:
        svg.append(f'<circle cx="{sx(mx):.1f}" cy="{sy(my):.1f}" r="22" fill="#e8f0e5" stroke="#bbb" stroke-width="3"/>')
    labels = [
        ("PICO: 3V3  GND  GP3  GP12  CA", 450, 930),
        ("CHARGER: VBUS  PGOOD  GND", 1150, 930),
        ("OUTPUTS: RAIL  SLEEP  GND", 650, 25),
        ("SHERMAN CHARGE INTERLOCK — REV A", 850, 755),
    ]
    for label, x, y in labels:
        svg.append(f'<text x="{sx(x):.1f}" y="{sy(y):.1f}" fill="white" font-family="sans-serif" font-size="13" text-anchor="middle">{label}</text>')
    svg.append("</svg>\n")
    (HERE / "assembly.svg").write_text("\n".join(svg), encoding="utf-8")


def write_job(stats: dict[str, int | float]) -> None:
    files = [
        (f"{NAME}-F_Cu.gtl", "Copper,L1,Top"),
        (f"{NAME}-B_Cu.gbl", "Copper,L2,Bot"),
        (f"{NAME}-F_Mask.gts", "SolderMask,Top"),
        (f"{NAME}-B_Mask.gbs", "SolderMask,Bot"),
        (f"{NAME}-F_Silkscreen.gto", "Legend,Top"),
        (f"{NAME}-Edge_Cuts.gm1", "Profile"),
        (f"{NAME}-PTH.drl", "Plated,Drill"),
        (f"{NAME}-NPTH.drl", "NonPlated,Drill"),
    ]
    job = {
        "Header": {"GenerationSoftware": {"Vendor": "Sherman", "Application": Path(__file__).name, "Version": "Rev A"}, "CreationDate": "2026-09-01"},
        "GeneralSpecs": {"ProjectId": {"Name": NAME, "Revision": "A"}, "Size": {"X": stats["board_width_mm"], "Y": stats["board_height_mm"]}, "LayerNumber": 2},
        "FilesAttributes": [{"Path": filename, "FileFunction": function} for filename, function in files],
        "MaterialStackup": [{"Type": "Copper", "Notes": "1 oz outer copper"}, {"Type": "Dielectric", "Material": "FR4", "Thickness": 1.6}],
    }
    (FAB / f"{NAME}-job.gbrjob").write_text(json.dumps(job, indent=2) + "\n", encoding="utf-8")


def write_fabrication(segments: list[Segment], vias: list[Via], stats: dict[str, int | float]) -> None:
    FAB.mkdir(parents=True, exist_ok=True)
    for entry in FAB.iterdir():
        if entry.is_file():
            entry.unlink()
    write_copper(FAB / f"{NAME}-F_Cu.gtl", "F.Cu", segments, vias)
    write_copper(FAB / f"{NAME}-B_Cu.gbl", "B.Cu", segments, vias)
    write_mask(FAB / f"{NAME}-F_Mask.gts", "Front")
    write_mask(FAB / f"{NAME}-B_Mask.gbs", "Back")
    write_silkscreen(FAB / f"{NAME}-F_Silkscreen.gto")
    write_outline(FAB / f"{NAME}-Edge_Cuts.gm1")
    write_drills(vias)
    write_job(stats)
    zip_path = HERE / f"{NAME}-gerbers.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(FAB.iterdir()):
            info = zipfile.ZipInfo(path.name, date_time=(2026, 9, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())


def main() -> None:
    segments, vias = route_board()
    stats = validate(segments, vias)
    write_kicad(segments, vias)
    write_csvs()
    write_assembly_svg(segments, vias)
    write_fabrication(segments, vias, stats)
    (HERE / "verification.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
