#!/usr/bin/env python3
"""Build Rev B from official KiCad footprints; run with KiCad's bundled Python.

KiCad owns footprint transforms and fabrication export. Independent validation
is in verify.py; this script does not certify its own output.
"""

import csv
import json
import math
import re
import uuid
from pathlib import Path

import pcbnew as k
import router
import wx

APP = wx.App(False)
HERE = Path(__file__).resolve().parent
NAME = "charging-interlock-rev-b"
DESIGN = json.loads((HERE / "design.json").read_text())


def v(x, y):
    return k.VECTOR2I(k.FromMM(x), k.FromMM(y))


def xy(p):
    return [round(k.ToMM(p.x), 6), round(k.ToMM(p.y), 6)]


def line(board, a, b, layer, width=0.15):
    s = k.PCB_SHAPE()
    s.SetShape(k.SHAPE_T_SEGMENT)
    s.SetStart(v(*a))
    s.SetEnd(v(*b))
    s.SetLayer(layer)
    s.SetWidth(k.FromMM(width))
    board.Add(s)


def text(board, value, x, y, size=0.9, layer=k.F_SilkS):
    t = k.PCB_TEXT(board)
    t.SetText(value)
    t.SetPosition(v(x, y))
    t.SetTextSize(v(size, size))
    t.SetTextThickness(k.FromMM(0.15))
    t.SetLayer(layer)
    board.Add(t)


def prune_tails(board):
    """Remove a router's dead-end segments; preserve pads, vias and T-junctions."""

    def connected(point, track, tracks):
        px, py = xy(point)
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                if pad.GetNetname() == track.GetNetname() and pad.HitTest(point):
                    return True
        for other in tracks:
            if other == track or other.GetNetname() != track.GetNetname():
                continue
            if isinstance(other, k.PCB_VIA):
                if point == other.GetPosition():
                    return True
            elif other.GetLayer() == track.GetLayer():
                ax, ay = xy(other.GetStart())
                bx, by = xy(other.GetEnd())
                seg = router.Segment("", "", ax, ay, bx, by, 0)
                if router.sq_distance_point_segment(px, py, seg) < 1e-10:
                    return True
        return False

    while True:
        tracks = list(board.GetTracks())
        dead = []
        for t in tracks:
            if isinstance(t, k.PCB_VIA):
                continue
            # Only trim very short routing tails, never a substantive routed span.
            if k.ToMM(t.GetLength()) <= 0.254001 and (
                not connected(t.GetStart(), t, tracks)
                or not connected(t.GetEnd(), t, tracks)
            ):
                dead.append(t)
        if not dead:
            break
        for t in dead:
            board.Remove(t)


def stable_ids(board):
    """Stable board serialization; electrical/physical checks remain independent."""

    def identify(item, key):
        item.SetUuid(
            k.KIID(str(uuid.uuid5(uuid.NAMESPACE_URL, "sherman-rev-b/" + key)))
        )

    for fp in board.GetFootprints():
        ref = fp.GetReference()
        identify(fp, "footprint/" + ref)
        for p in fp.Pads():
            identify(p, "pad/" + ref + "/" + p.GetNumber())
        for i, g in enumerate(fp.GraphicalItems()):
            identify(g, f"graphic/{ref}/{i}")
        for f in fp.GetFields():
            identify(f, "field/" + ref + "/" + f.GetName())
    for i, g in enumerate(board.GetDrawings()):
        identify(g, f"board-drawing/{i}")
    for i, t in enumerate(board.GetTracks()):
        identify(t, f"track/{i}")


def build():
    board = k.BOARD()
    settings = board.GetDesignSettings()
    settings.SetCopperLayerCount(2)
    settings.m_MinClearance = k.FromMM(0.3048)
    settings.m_TrackMinWidth = k.FromMM(0.4064)
    settings.m_CopperEdgeClearance = k.FromMM(0.508)
    settings.m_HoleClearance = k.FromMM(0.3048)
    settings.m_HoleToHoleMin = k.FromMM(0.3048)
    settings.m_MinThroughDrill = k.FromMM(0.6)
    settings.m_ViasMinSize = k.FromMM(1.27)
    settings.m_ViasMinAnnularWidth = k.FromMM(0.3)
    settings.m_SolderMaskExpansion = k.FromMM(0.08)
    settings.m_SolderMaskMinWidth = k.FromMM(0.1)
    nets = {}
    for name in sorted({n for c in DESIGN["components"] for n in c["nets"]}):
        nets[name] = k.NETINFO_ITEM(board, name)
        board.Add(nets[name])
    footprints = {}
    records = []
    routing_pads = []
    stubs = []
    for c in DESIGN["components"]:
        fp = k.FootprintLoad(
            str(HERE / "vendor" / f"{c['library']}.pretty"), c["footprint"]
        )
        if fp is None:
            raise RuntimeError(c["footprint"])
        fp.SetReference(c["ref"])
        fp.SetValue(c["value"])
        board.Add(fp)
        fp.SetPosition(v(*c["at"]))
        fp.SetOrientationDegrees(c["rotation"])
        fp.SetFPID(k.LIB_ID(c["library"], c["footprint"]))
        fp.Value().SetVisible(False)
        if c["ref"] == "U1":
            model = k.FP_3DMODEL()
            model.m_Filename = (
                "${KICAD10_3DMODEL_DIR}/Package_DIP.3dshapes/DIP-14_W7.62mm.step"
            )
            model.m_Offset.z = 5.1
            fp.Add3DModel(model)
        for pad in fp.Pads():
            number = int(pad.GetNumber())
            net = c["nets"][number - 1]
            pad.SetNet(nets[net])
            pos = xy(pad.GetPosition())
            size = xy(pad.GetSize())
            drill = xy(pad.GetDrillSize())
            records.append(
                {
                    "ref": c["ref"],
                    "pin": str(number),
                    "net": net,
                    "x_mm": pos[0],
                    "y_mm": pos[1],
                    "size_mm": size,
                    "drill_mm": drill,
                }
            )
            # Conservative circular routing obstacles enclose rectangular/oval pads.
            diameter = (
                max(size) if pad.GetShape() == k.PAD_SHAPE_CIRCLE else math.hypot(*size)
            ) / 0.0254
            snapped = [round(value / 0.254) * 10 for value in pos]
            routing_pads.append(
                router.Pad(c["ref"], str(number), *snapped, net, diameter)
            )
            if any(abs(pos[i] - snapped[i] * 0.0254) > 1e-6 for i in range(2)):
                stubs.append((net, pos, [n * 0.0254 for n in snapped]))
        ref = fp.Reference()
        ref.SetTextAngle(k.EDA_ANGLE(0, k.DEGREES_T))
        ref.SetTextSize(v(0.9, 0.9))
        ref.SetTextThickness(k.FromMM(0.15))
        x, y = c["at"]
        if c["ref"] == "U1":
            ref.SetPosition(v(17.78, 11.43))
        elif c["ref"] == "Q1":
            ref.SetPosition(v(31.24, 8.128))
        elif c["ref"] == "C1":
            ref.SetPosition(v(11.41, 1.778))
        elif c["ref"] == "R2":
            ref.SetPosition(v(33.85, 17.78))
        elif c["ref"] == "R3":
            ref.SetPosition(v(35.56, 18.8))
        elif c["ref"] in ("R1", "R4", "R5", "R6"):
            ref.SetPosition(v(0.8, y))
        elif c["ref"].startswith("R"):
            ref.SetPosition(v(x + 1.27, y - 1.9))
        elif c["ref"] == "J3":
            ref.SetPosition(v(20.32, 5.3))
        elif c["ref"] == "J1":
            ref.SetPosition(v(12.192, 19.05))
        else:
            ref.SetPosition(v(23.622, 20.32))
        footprints[c["ref"]] = fp
    for i, (x, y) in enumerate(DESIGN["mounts_mm"], 1):
        fp = k.FootprintLoad(
            str(HERE / "vendor/MountingHole.pretty"), "MountingHole_2.2mm_M2"
        )
        fp.SetReference("H" + str(i))
        board.Add(fp)
        fp.SetPosition(v(x, y))
        fp.Value().SetVisible(False)
        fp.Reference().SetVisible(False)
        fp.SetFPID(k.LIB_ID("MountingHole", "MountingHole_2.2mm_M2"))
    w, h = DESIGN["board_mm"]
    for a, b in zip([(0, 0), (w, 0), (w, h), (0, h)], [(w, 0), (w, h), (0, h), (0, 0)]):
        line(board, a, b, k.Edge_Cuts, 0.05)
    text(board, "SHERMAN", 18.0, 18.55, 0.8)
    text(board, "REV B", 21.2, 22.0, 0.8)
    for c, labels, y in [
        ("J1", ["3V3", "G", "G3", "12", "CA"], 23.368),
        ("J2", ["VB", "PG", "G"], 23.368),
        ("J3", ["R", "S", "G"], 0.55),
    ]:
        x = next(d["at"][0] for d in DESIGN["components"] if d["ref"] == c)
        for i, label in enumerate(labels):
            text(board, label, x + i * 2.54, y, 0.8)
    router.PADS = tuple(routing_pads)
    print("Routing 9 nets from standard-footprint pad positions...", flush=True)
    segments, vias = router.route_board()
    for s in segments:
        t = k.PCB_TRACK(board)
        t.SetStart(v(s.x1 * 0.0254, s.y1 * 0.0254))
        t.SetEnd(v(s.x2 * 0.0254, s.y2 * 0.0254))
        t.SetWidth(k.FromMM(s.width * 0.0254))
        t.SetLayer(k.F_Cu if s.layer == "F.Cu" else k.B_Cu)
        t.SetNet(nets[s.net])
        board.Add(t)
    for net, start, end in stubs:
        for layer in (k.F_Cu, k.B_Cu):
            t = k.PCB_TRACK(board)
            t.SetStart(v(*start))
            t.SetEnd(v(*end))
            t.SetWidth(k.FromMM(0.4064))
            t.SetLayer(layer)
            t.SetNet(nets[net])
            board.Add(t)
    # Through-hole pads already connect both layers; never drill a redundant via into a pad.
    pad_points = {(p.x, p.y) for p in routing_pads}
    unique_vias = {(a.net, a.x, a.y) for a in vias if (a.x, a.y) not in pad_points}
    for net, x, y in sorted(unique_vias):
        via = k.PCB_VIA(board)
        via.SetPosition(v(x * 0.0254, y * 0.0254))
        via.SetWidth(k.FromMM(1.27))
        via.SetDrill(k.FromMM(0.6096))
        via.SetViaType(k.VIATYPE_THROUGH)
        via.SetLayerPair(k.F_Cu, k.B_Cu)
        via.SetNet(nets[net])
        board.Add(via)
    prune_tails(board)
    stable_ids(board)
    board.SetFileName(str(HERE / f"{NAME}.kicad_pcb"))
    k.SaveBoard(str(HERE / f"{NAME}.kicad_pcb"), board)
    # KiCad 10's SWIG binding does not expose PCB_POINT methods. Normalize only
    # the non-electrical F.Fab datum UUID emitted by the native serializer.
    path = HERE / f"{NAME}.kicad_pcb"
    pattern = r'(\(point\s+\(at [^\n]+\)\s+\(size [^\n]+\)\s+\(layer [^\n]+\)\s+\(uuid ")[^"]+("\))'
    path.write_text(
        re.sub(
            pattern,
            lambda m: m[1] + str(uuid.uuid5(uuid.NAMESPACE_URL, m[1])) + m[2],
            path.read_text(),
        )
    )

    (HERE / "pad-map.json").write_text(
        json.dumps(sorted(records, key=lambda p: (p["ref"], int(p["pin"]))), indent=2)
        + "\n"
    )
    with (HERE / "netlist.csv").open("w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["net", "endpoint", "pin"])
        for r in sorted(records, key=lambda p: (p["ref"], int(p["pin"]))):
            writer.writerow([r["net"], r["ref"], r["pin"]])
    with (HERE / "bom.csv").open("w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(
            ["reference", "quantity", "value", "manufacturer_part", "footprint"]
        )
        for c in DESIGN["components"]:
            writer.writerow(
                [
                    c["ref"],
                    1,
                    c["value"],
                    c["part"],
                    c["library"] + ":" + c["footprint"],
                ]
            )
        writer.writerow(
            [
                "U1-SOCKET",
                1,
                "14-pin DIP socket",
                "TE 1-2199298-3",
                "Included in U1 assembly envelope",
            ]
        )
    print(
        f"Saved {len(segments)} tracks, {len(unique_vias)} vias; KiCad DRC is required.",
        flush=True,
    )


if __name__ == "__main__":
    build()
