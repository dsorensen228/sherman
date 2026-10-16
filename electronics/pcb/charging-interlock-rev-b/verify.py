#!/usr/bin/env python3
"""Independent physical and exported-copper verification, separate from generator.

Reads KiCad S-expressions using sexpdata and Gerber/Excellon using Gerbonara.
Shapely reconstructs copper islands without trusting Gerber net attributes.
Manufacturer dimensions and the expected circuit are independent inputs.
"""

import argparse
import hashlib
import json
import math
import warnings
from collections import defaultdict
from pathlib import Path

import sexpdata
from gerbonara import LayerStack
from gerbonara import graphic_primitives as gp
from gerbonara.utils import MM
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
NAME = "charging-interlock-rev-b"
TOL = 0.003
EXPECTED = json.loads((HERE / "expected-circuit.json").read_text())
EXPECTED.pop("provenance")


def children(tree, tag):
    return [e for e in tree if isinstance(e, list) and e and str(e[0]) == tag]


def child(tree, tag, default=None):
    return next(iter(children(tree, tag)), default)


def read_board(path):
    tree = sexpdata.loads(Path(path).read_text())
    global_nets = {e[1]: e[2] for e in children(tree, "net")}
    pads = {}
    footprints = {}
    mounts = []
    for fp in children(tree, "footprint"):
        props = {p[1]: p[2] for p in children(fp, "property")}
        ref = props.get("Reference", "")
        at = child(fp, "at", [None, 0, 0])
        fx, fy = at[1:3]
        angle = math.radians(at[3] if len(at) > 3 else 0)
        footprints[ref] = fp
        for pad in children(fp, "pad"):
            a = child(pad, "at")
            px, py = a[1:3]
            x = fx + px * math.cos(angle) + py * math.sin(angle)
            y = fy - px * math.sin(angle) + py * math.cos(angle)
            drill = child(pad, "drill")[1]
            if str(pad[2]) == "np_thru_hole":
                mounts.append((x, y, drill))
                continue
            net = child(pad, "net")
            name = (
                net[-1]
                if net and isinstance(net[-1], str)
                else global_nets.get(net[1], "")
                if net
                else ""
            )
            # Rev A represents deliberately unused outputs as empty nets.
            if ref == "U1" and str(pad[1]) in ("8", "11") and not name:
                name = "NC" + str(pad[1])
            size = child(pad, "size")[1:3]
            pads[(ref, str(pad[1]))] = {
                "x": x,
                "y": y,
                "net": name,
                "drill": drill,
                "size": size,
            }
    return tree, pads, footprints, mounts


def circuit_errors(pads):
    want = {(r, p): n for r, ns in EXPECTED.items() for p, n in ns.items()}
    actual = {k: v["net"] for k, v in pads.items()}
    return [
        f"Circuit mismatch {k}: {actual.get(k)} != {want.get(k)}"
        for k in sorted(actual.keys() | want.keys())
        if actual.get(k) != want.get(k)
    ]


def pin_orientation_errors(pads):
    """Manufacturer TOP view: notch left, 1..7 bottom, 14..8 top."""
    errors = []
    u = {int(n): v for (r, n), v in pads.items() if r == "U1"}
    if set(u) != set(range(1, 15)):
        return ["U1 must have fourteen physical pads"]
    x0 = min(p["x"] for p in u.values())
    y0 = min(p["y"] for p in u.values())
    for n in range(1, 15):
        col = n - 1 if n <= 7 else 14 - n
        desired = (x0 + col * 2.54, y0 + (7.62 if n <= 7 else 0))
        if math.dist((u[n]["x"], u[n]["y"]), desired) > 1e-4:
            errors.append(
                f"U1 physical pin {n} is mirrored/misplaced; manufacturer top-view position {desired}"
            )
    return errors


def envelopes(pads, mounts):
    """Maximum body sizes, including socket, independent of KiCad courtyards.
    TI 4040049/E: PDIP body 19.69 x 6.60; TE 2199298/A: socket 17.78 x 10
    (use 17.98 x 10.20 tolerance envelope). onsemi 135AN/O: lead-centered
    outline max 5.20 wide, 2.66 rounded projection, 2.06 flat projection.
    KEMET spec: 3.81 x 2.54. Yageo MFR-25: body diameter 2.4 +/-0.2.
    Samtec TSW: 2.54 pitch, 2.54 nominal insulator width (allow 2.70).
    """
    result = {}

    def pos(ref, n="1"):
        p = pads[ref, n]
        return p["x"], p["y"]

    ux = [p["x"] for (r, n), p in pads.items() if r == "U1"]
    uy = [p["y"] for (r, n), p in pads.items() if r == "U1"]
    cx = (min(ux) + max(ux)) / 2
    cy = (min(uy) + max(uy)) / 2
    result["U1"] = unary_union(
        [
            box(cx - 19.69 / 2, cy - 6.6 / 2, cx + 19.69 / 2, cy + 6.6 / 2),
            box(cx - 17.98 / 2, cy - 5.1, cx + 17.98 / 2, cy + 5.1),
        ]
    )
    # Derive local lead axis from E to C so Rev A is checked too.
    e, b, c = pos("Q1"), pos("Q1", "2"), pos("Q1", "3")
    dx, dy = c[0] - e[0], c[1] - e[1]
    a = math.degrees(math.atan2(dy, dx))
    local = box(-2.6, -2.66, 2.6, 2.06)
    result["Q1"] = affinity.translate(
        affinity.rotate(local, a, origin=(0, 0)), b[0], b[1]
    )
    a, b = pos("C1"), pos("C1", "2")
    cx = (a[0] + b[0]) / 2
    cy = (a[1] + b[1]) / 2
    shape = box(-1.905, -1.27, 1.905, 1.27)
    result["C1"] = affinity.translate(
        affinity.rotate(
            shape, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])), origin=(0, 0)
        ),
        cx,
        cy,
    )
    for r in ["R" + str(i) for i in range(1, 8)]:
        result[r] = Point(*pos(r)).buffer(1.3, quad_segs=64)
    for r in ("J1", "J2", "J3"):
        ps = [p for (ref, _), p in pads.items() if ref == r]
        xs = [p["x"] for p in ps]
        ys = [p["y"] for p in ps]
        result[r] = box(min(xs) - 1.35, min(ys) - 1.35, max(xs) + 1.35, max(ys) + 1.35)
    for i, (x, y, _) in enumerate(mounts, 1):
        result["H" + str(i)] = Point(x, y).buffer(2.2, quad_segs=64)
    return result


def mechanical_errors(pads, mounts):
    shapes = envelopes(pads, mounts)
    errors = []
    gaps = []
    expected_mounts = [
        (2.54, 2.54, 2.2),
        (35.56, 2.54, 2.2),
        (2.54, 21.59, 2.2),
        (35.56, 21.59, 2.2),
    ]
    if len(mounts) != 4 or any(
        not any(math.dist(m, expected) < 1e-4 for m in mounts)
        for expected in expected_mounts
    ):
        errors.append("Mounting hole positions/diameters differ from original board")

    for i, (a, pa) in enumerate(shapes.items()):
        if not box(0, 0, 38.1, 24.13).covers(pa):
            errors.append(f"{a} body extends outside board")
        for b, pb in list(shapes.items())[i + 1 :]:
            gap = pa.distance(pb)
            gaps.append((gap, a, b))
            if pa.intersects(pb) or gap < 0.5 - TOL:
                errors.append(
                    f"Body/fastener clearance {a} to {b}: {gap:.4f} mm < 0.5 mm"
                )
        for (ref, pin), p in pads.items():
            if ref == a:
                continue
            # Assembly access: every foreign lead hole must be outside body + 0.25mm.
            gap = pa.distance(Point(p["x"], p["y"])) - p["drill"] / 2
            if gap < 0.25 - TOL:
                errors.append(
                    f"{a} obstructs {ref}.{pin} lead hole ({gap:.4f} mm clearance)"
                )
    return errors, sorted(gaps), shapes


def primitive_shape(p):
    if isinstance(p, gp.Circle):
        return Point(p.x, p.y).buffer(p.r, quad_segs=64)
    if isinstance(p, gp.Line):
        return LineString([(p.x1, p.y1), (p.x2, p.y2)]).buffer(
            p.width / 2, quad_segs=64
        )
    if isinstance(p, gp.Rectangle):
        return affinity.rotate(
            box(p.x - p.w / 2, p.y - p.h / 2, p.x + p.w / 2, p.y + p.h / 2),
            p.rotation,
            origin=(p.x, p.y),
            use_radians=True,
        )
    if isinstance(p, (gp.Arc, gp.ArcPoly)):
        a = p.to_arc_poly() if isinstance(p, gp.Arc) else p
        return Polygon(a.approximate_arcs(max_error=0.0005).outline)
    raise TypeError(type(p))


def layer_shape(layer):
    shape = Polygon()
    dark = []
    for o in layer.objects:
        for p in o.to_primitives(unit=MM):
            if p.polarity_dark:
                dark.append(primitive_shape(p))
            else:
                shape = unary_union([shape, *dark]).difference(primitive_shape(p))
                dark = []
    return unary_union([shape, *dark])


class UnionFind:
    def __init__(self):
        self.parents = {}

    def root(self, k):
        self.parents.setdefault(k, k)
        if self.parents[k] != k:
            self.parents[k] = self.root(self.parents[k])
        return self.parents[k]

    def join(self, a, b):
        self.parents[self.root(a)] = self.root(b)


def gerber_errors(folder, pads, mounts):
    errors = []
    # KiCad puts legal G90 after the header; Gerbonara warns but parses correctly.
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore", message=".*G90 header statement.*", category=SyntaxWarning
        )
        stack = LayerStack.open(folder)
    if set(stack.graphic_layers) != {
        ("top", "copper"),
        ("bottom", "copper"),
        ("top", "mask"),
        ("bottom", "mask"),
        ("top", "silk"),
        ("mechanical", "outline"),
    }:
        errors.append("Unexpected Gerber layer set")
    uf = UnionFind()
    polys = {}
    shapes = {}
    points = {}
    net_at = {}
    for side in ("top", "bottom"):
        layer = stack[side, "copper"]
        shapes[side] = layer_shape(layer)
        polys[side] = (
            list(shapes[side].geoms)
            if hasattr(shapes[side], "geoms")
            else [shapes[side]]
        )
        for i in range(len(polys[side])):
            uf.root((side, i))
        for o in layer.objects:
            endpoint = o.attrs.get(".P") if isinstance(o.attrs, dict) else None
            if endpoint:
                key = tuple(endpoint[:2])
                point = (o.x, -o.y)
                if (
                    key not in pads
                    or math.dist(point, (pads[key]["x"], pads[key]["y"])) > 1e-4
                ):
                    errors.append(f"Exported {side} pad position mismatch {key}")
                if side == "top":
                    points[key] = point

    def island(side, x, y):
        hits = [
            i for i, p in enumerate(polys[side]) if p.buffer(1e-7).covers(Point(x, y))
        ]
        if len(hits) != 1:
            raise AssertionError(f"{side} copper missing/ambiguous at {(x, y)}: {hits}")
        return side, hits[0]

    if len(pads) != 44:
        errors.append(f"Expected 44 component pads; board has {len(pads)}")
    drills = []
    for obj in stack.drill_pth.objects:
        x, y = obj.x, obj.y
        diam = obj.tool.diameter
        drills.append((x, y, diam, "PTH"))
        uf.join(island("top", x, y), island("bottom", x, y))
    npth = [(o.x, o.y, o.tool.diameter, "NPTH") for o in stack.drill_npth.objects]
    for x, y, d in mounts:
        if not any(
            math.dist((x, -y), (a, b)) < 1e-4 and abs(d - c) < 1e-4
            for a, b, c, _ in npth
        ):
            errors.append("Mounting drill export mismatch")
    if len(npth) != 4:
        errors.append("Expected four NPTH mounting holes")
    for key, p in pads.items():
        if not any(
            math.dist((p["x"], -p["y"]), (x, y)) < 1e-4 and abs(d - p["drill"]) < 1e-4
            for x, y, d, _ in drills
        ):
            errors.append(f"Pad drill missing/incorrect {key}")
        root = uf.root(island("top", p["x"], -p["y"]))
        net = p["net"]
        net_at.setdefault(root, set()).add(net)
    if any(len(ns) != 1 for ns in net_at.values()):
        errors.append("Different circuit nets are shorted in exported copper")
    net_roots = defaultdict(set)
    for root, names in net_at.items():
        for name in names:
            net_roots[name].add(root)
    for net, roots in net_roots.items():
        if len(roots) != 1:
            errors.append(f"Exported copper has open net {net}")
    min_copper = float("inf")
    for side, items in polys.items():
        for i, a in enumerate(items):
            ra = uf.root((side, i))
            if ra not in net_at:
                errors.append(f"Isolated {side} copper island with no circuit endpoint")
            for j, b in enumerate(items[i + 1 :], i + 1):
                if uf.root((side, j)) == ra:
                    continue
                gap = a.distance(b)
                min_copper = min(min_copper, gap)
                if gap < 0.3048 - TOL:
                    errors.append(
                        f"Exported {side} copper clearance {gap:.5f} < 0.3048 mm"
                    )
        region = box(0, -24.13, 38.1, 0)
        if not region.buffer(-0.508 + TOL).covers(shapes[side]):
            errors.append(f"Exported {side} copper too close to board edge")
        for x, y, _ in mounts:
            gap = shapes[side].distance(Point(x, -y)) - 2.2
            if gap < 0.3048 - TOL:
                errors.append(
                    f"Exported {side} copper under mounting-head keepout: {gap:.4f}"
                )
        mask = layer_shape(stack[side, "mask"])
        for key, p in pads.items():
            if not mask.covers(Point(p["x"], -p["y"]).buffer(p["drill"] / 2)):
                errors.append(f"Mask obstructs lead hole {side} {key}")
    min_drill = float("inf")
    all_drills = drills + npth
    for i, (x, y, d, _) in enumerate(all_drills):
        for a, b, c, _ in all_drills[i + 1 :]:
            gap = math.dist((x, y), (a, b)) - (d + c) / 2
            min_drill = min(min_drill, gap)
            if gap < 0.3048 - TOL:
                errors.append(f"Exported drills collide / too close: {gap:.5f} mm")
    # Outline is measured from line center coordinates, not stroke extents.
    coords = []
    for o in stack["mechanical", "outline"].objects:
        for p in o.to_primitives(unit=MM):
            if not isinstance(p, gp.Line):
                raise TypeError("Unexpected board edge primitive")
            coords += [(p.x1, p.y1), (p.x2, p.y2)]
    if len(coords) != 8 or any(
        abs(a - b) > 1e-4
        for a, b in zip(
            (
                min(x for x, y in coords),
                min(y for x, y in coords),
                max(x for x, y in coords),
                max(y for x, y in coords),
            ),
            (0, -24.13, 38.1, 0),
        )
    ):
        errors.append("Exported outline does not retain Rev A size")
    return errors, {
        "copper_layers": 2,
        "component_pads": len(pads),
        "electrical_nets": len(net_roots),
        "plated_drills": len(drills),
        "mounting_drills": len(npth),
        "minimum_copper_clearance_mm": round(min_copper, 5),
        "minimum_drill_clearance_mm": round(min_drill, 5),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=HERE / f"{NAME}.kicad_pcb")
    ap.add_argument("--fabrication", type=Path, default=HERE / "fabrication")
    ap.add_argument("--mechanical-only", action="store_true")
    args = ap.parse_args()
    _, pads, _, mounts = read_board(args.board)
    errors = circuit_errors(pads) + pin_orientation_errors(pads)
    me, gaps, _ = mechanical_errors(pads, mounts)
    errors += me
    stats = {}
    if not args.mechanical_only:
        ge, stats = gerber_errors(args.fabrication, pads, mounts)
        errors += ge
    result = dict(
        status="FAIL" if errors else "PASS",
        board_sha256=hashlib.sha256(args.board.read_bytes()).hexdigest(),
        errors=errors,
        minimum_body_clearance_mm=round(gaps[0][0], 5),
        closest_body_pair=list(gaps[0][1:]),
        **stats,
    )
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    main()
