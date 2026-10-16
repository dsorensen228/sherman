"""Grid router derived from Rev A; correctness is gated by independent KiCad DRC.
Unused outputs are physical copper obstacles. Never use this module as the
fabrication exporter or acceptance authority.
"""

import heapq
import math
from collections import defaultdict
from dataclasses import dataclass

GRID = 10
EDGE_KEEPOUT = 50
CLEARANCE = 12
ROUTER_MARGIN = 8
SIGNAL_WIDTH = 16
SUPPLY_WIDTH = 24
VIA_DIAMETER = 50
VIA_DRILL = 24
LAYERS = ("F.Cu", "B.Cu")
BOARD_W = 1500
BOARD_H = 950
MOUNTS = ((100, 100), (1400, 100), (100, 850), (1400, 850))
PADS = ()


@dataclass(frozen=True)
class Pad:
    ref: str
    number: str
    x: int
    y: int
    net: str
    diameter: float


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
    return orientation(p1, q1, p2) != orientation(p1, q1, q2) and orientation(
        p2, q2, p1
    ) != orientation(p2, q2, q1)


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
        "GND_ESCAPE",
        "RAIL_EN",
        "SLEEP_EN",
        "GP3",
        "GP12",
        "3V3",
        "VBUS",
        "QBASE",
        "CHARGE_ABSENT",
        "GND",
    )
    terminal_priority = {
        "CHARGE_ABSENT": ("J1.5", "J2.2", "R1.2", "U1.5", "U1.2", "Q1.3"),
    }

    def allowed(
        net: str, layer: str, x: int, y: int, width: int, changing_layer: bool = False
    ) -> bool:
        if (
            x < EDGE_KEEPOUT
            or x > BOARD_W - EDGE_KEEPOUT
            or y < EDGE_KEEPOUT
            or y > BOARD_H - EDGE_KEEPOUT
        ):
            return False
        for mx, my in MOUNTS:
            if math.hypot(x - mx, y - my) < 87 + CLEARANCE + ROUTER_MARGIN + width / 2:
                return False
        for pad in PADS:
            if changing_layer and math.hypot(x - pad.x, y - pad.y) < 45:
                return False
            if pad.net == net:
                continue
            if (
                math.hypot(x - pad.x, y - pad.y)
                < pad.diameter / 2 + CLEARANCE + ROUTER_MARGIN + width / 2
            ):
                return False
        for segment in segments:
            if segment.net == net or (segment.layer != layer and not changing_layer):
                continue
            probe = Segment(net, layer, x, y, x, y, width)
            if (
                segment_distance(probe, segment)
                < width / 2 + segment.width / 2 + CLEARANCE + ROUTER_MARGIN
            ):
                return False
        for via in vias:
            if via.net == net:
                continue
            if (
                math.hypot(x - via.x, y - via.y)
                < width / 2 + VIA_DIAMETER / 2 + CLEARANCE + ROUTER_MARGIN
            ):
                return False
        return True

    def astar(
        net: str,
        starts: set[tuple[int, int, int]],
        targets: set[tuple[int, int, int]],
        width: int,
    ) -> list[tuple[int, int, int]]:
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
            (GRID, 0, float(GRID)),
            (-GRID, 0, float(GRID)),
            (0, GRID, float(GRID)),
            (0, -GRID, float(GRID)),
            (GRID, GRID, GRID * math.sqrt(2)),
            (GRID, -GRID, GRID * math.sqrt(2)),
            (-GRID, GRID, GRID * math.sqrt(2)),
            (-GRID, -GRID, GRID * math.sqrt(2)),
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
            neighbors = [(x + dx, y + dy, layer_index, step) for dx, dy, step in moves]
            neighbors.append((x, y, 1 - layer_index, 120.0))
            for nx, ny, next_layer, step_cost in neighbors:
                candidate = (nx, ny, next_layer)
                changing = next_layer != layer_index
                if (
                    candidate not in targets
                    and candidate not in starts
                    and not allowed(
                        net,
                        LAYERS[next_layer],
                        nx,
                        ny,
                        width if not changing else VIA_DIAMETER,
                        changing,
                    )
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
            for x, y in reached_xy
            for tx, ty in target_xy
        )
        raise RuntimeError(
            f"unable to route {net}; explored={len(cost)}, nearest={nearest}"
        )

    for net in route_order:
        print("Routing", net, flush=True)
        if net == "GND_ESCAPE":
            net = "GND"
            terminals = [
                next(p for p in pads_by_net[net] if (p.ref, p.number) == key)
                for key in (("J1", "2"), ("R4", "2"))
            ]
        else:
            terminals = pads_by_net[net]
        if net in terminal_priority:
            order = {
                endpoint: index for index, endpoint in enumerate(terminal_priority[net])
            }
            terminals = sorted(
                terminals, key=lambda pad: order[f"{pad.ref}.{pad.number}"]
            )
        width = SUPPLY_WIDTH if net in {"GND", "3V3", "VBUS"} else SIGNAL_WIDTH
        tree = {
            (terminals[0].x, terminals[0].y, 0),
            (terminals[0].x, terminals[0].y, 1),
        }
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
                        segments.append(
                            Segment(
                                net,
                                LAYERS[run_start[2]],
                                run_start[0],
                                run_start[1],
                                previous_node[0],
                                previous_node[1],
                                width,
                            )
                        )
                    vias.append(Via(net, node[0], node[1]))
                    run_start = node
                    direction = None
                    previous_node = node
                    continue
                new_direction = (
                    node[0] - previous_node[0],
                    node[1] - previous_node[1],
                    node[2],
                )
                if direction is not None and new_direction != direction:
                    segments.append(
                        Segment(
                            net,
                            LAYERS[run_start[2]],
                            run_start[0],
                            run_start[1],
                            previous_node[0],
                            previous_node[1],
                            width,
                        )
                    )
                    run_start = previous_node
                direction = new_direction
                previous_node = node
            if previous_node != run_start:
                segments.append(
                    Segment(
                        net,
                        LAYERS[run_start[2]],
                        run_start[0],
                        run_start[1],
                        previous_node[0],
                        previous_node[1],
                        width,
                    )
                )
    return segments, vias
