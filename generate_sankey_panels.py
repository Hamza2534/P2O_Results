#!/usr/bin/env python3
import csv
import math
import os
import zlib
from dataclasses import dataclass
from typing import Dict, List, Tuple

SCENARIOS = ["BAU", "CDS", "RES", "RSS", "SCS"]
VARIANT = "CENTRAL"
ANNUAL_YEAR = 2044

COLLECTION_NODES = [
    "formal_collection_t",
    "informal_collection_t",
    "mixed_collection_t",
    "uncollected_t",
]
TREATMENT_NODES = [
    "closed_loop_mr_t",
    "open_loop_mr_t",
    "chemical_p2p_t",
    "chemical_p2f_t",
    "engineered_landfill_t",
    "thermal_treatment_t",
    "unsanitary_dumpsite_t",
]
LEAKAGE_NODES = ["aquatic_t", "terrestrial_t", "open_burning_t"]

NODE_ORDER = COLLECTION_NODES + TREATMENT_NODES + LEAKAGE_NODES
DISPLAY = {
    "formal_collection_t": "Formal collection",
    "informal_collection_t": "Informal collection",
    "mixed_collection_t": "Mixed collection",
    "uncollected_t": "Uncollected",
    "closed_loop_mr_t": "Closed-loop MR",
    "open_loop_mr_t": "Open-loop MR",
    "chemical_p2p_t": "Chemical P2P",
    "chemical_p2f_t": "Chemical P2F",
    "engineered_landfill_t": "Engineered landfill",
    "thermal_treatment_t": "Thermal treatment",
    "unsanitary_dumpsite_t": "Unsanitary dumpsite",
    "aquatic_t": "Aquatic leakage",
    "terrestrial_t": "Terrestrial leakage",
    "open_burning_t": "Open burning",
}
COLORS = {
    "formal_collection_t": (44, 123, 182),
    "informal_collection_t": (171, 217, 233),
    "mixed_collection_t": (116, 173, 209),
    "uncollected_t": (253, 174, 97),
    "closed_loop_mr_t": (49, 163, 84),
    "open_loop_mr_t": (161, 217, 155),
    "chemical_p2p_t": (123, 50, 148),
    "chemical_p2f_t": (194, 165, 207),
    "engineered_landfill_t": (99, 99, 99),
    "thermal_treatment_t": (230, 85, 13),
    "unsanitary_dumpsite_t": (252, 146, 114),
    "aquatic_t": (33, 113, 181),
    "terrestrial_t": (117, 107, 177),
    "open_burning_t": (203, 24, 29),
}

@dataclass
class NodeGeom:
    x: float
    y: float
    w: float
    h: float


def read_rows(path: str) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def get_annual_values(rows, scenario):
    for r in rows:
        if r["scenario"] == scenario and r["variant"] == VARIANT and int(float(r["year"])) == ANNUAL_YEAR:
            out = {}
            for k,v in r.items():
                try:
                    out[k]=float(v)
                except (TypeError, ValueError):
                    pass
            return out
    raise ValueError(f"No annual row for {scenario} {VARIANT} {ANNUAL_YEAR}")


def get_cumulative_values(rows, scenario):
    candidates = [r for r in rows if r["scenario"] == scenario and r["variant"] == VARIANT]
    if not candidates:
        raise ValueError(f"No cumulative rows for {scenario} {VARIANT}")
    r = max(candidates, key=lambda x: float(x["year"]))
    out = {}
    for k,v in r.items():
        try:
            out[k]=float(v)
        except (TypeError, ValueError):
            pass
    return out


def fmt_mt(v):
    return f"{v/1e6:.2f} Mt"


def rgba(rgb, a):
    return f"rgba({rgb[0]},{rgb[1]},{rgb[2]},{a})"


def compute_panel_geometry(values, x0, y0, w, h):
    column_nodes = [COLLECTION_NODES, TREATMENT_NODES, LEAKAGE_NODES]
    pad = 8
    max_sum = max(sum(values[n] for n in col) for col in column_nodes)
    max_nodes = max(len(c) for c in column_nodes)
    scale = (h - ((max_nodes - 1) * pad)) / max_sum if max_sum > 0 else 1.0

    xs = [x0 + 40, x0 + w / 2 - 14, x0 + w - 68]
    node_w = 28
    geom = {}
    for ci, col in enumerate(column_nodes):
        y = y0 + 40
        for n in col:
            nh = max(2.0, values[n] * scale)
            geom[n] = NodeGeom(xs[ci], y, node_w, nh)
            y += nh + pad
    return geom, scale


def build_links(values):
    links = []
    collected_total = sum(values[n] for n in COLLECTION_NODES[:-1])
    post_aquatic = max(0.0, values["aquatic_t"] - values.get("uncollected_to_water_t", 0.0))
    post_terr = max(0.0, values["terrestrial_t"] - values.get("uncollected_to_land_t", 0.0))
    post_burn = max(0.0, values["open_burning_t"] - values.get("uncollected_to_burn_t", 0.0))
    post_total = post_aquatic + post_terr + post_burn

    for c in COLLECTION_NODES[:-1]:
        share = values[c] / collected_total if collected_total > 0 else 0.0
        for t in TREATMENT_NODES:
            v = values[t] * share
            if v > 0:
                links.append((c, t, v, COLORS[c]))

    uncol = "uncollected_t"
    uc_map = {
        "aquatic_t": values.get("uncollected_to_water_t", 0.0),
        "terrestrial_t": values.get("uncollected_to_land_t", 0.0),
        "open_burning_t": values.get("uncollected_to_burn_t", 0.0),
    }
    for k, v in uc_map.items():
        if v > 0:
            links.append((uncol, k, v, COLORS[uncol]))

    for t in TREATMENT_NODES:
        tv = values[t]
        if tv <= 0:
            continue
        if post_total <= 0:
            continue
        for k, part in [("aquatic_t", post_aquatic), ("terrestrial_t", post_terr), ("open_burning_t", post_burn)]:
            v = tv * (part / post_total)
            if v > 0:
                links.append((t, k, v, COLORS[t]))
    return links


def sankey_panel_svg(values, title, x0, y0, w, h):
    geom, scale = compute_panel_geometry(values, x0, y0, w, h)
    links = build_links(values)

    out_off = {n: 0.0 for n in NODE_ORDER}
    in_off = {n: 0.0 for n in NODE_ORDER}

    elements = []
    elements.append(f'<text x="{x0+20}" y="{y0+24}" font-size="18" font-weight="700">{title}</text>')

    def link_path(sg: NodeGeom, tg: NodeGeom, sy0, sy1, ty0, ty1):
        x1 = sg.x + sg.w
        x2 = tg.x
        c = max(40, (x2 - x1) * 0.35)
        return (
            f"M {x1:.2f},{sy0:.2f} C {x1+c:.2f},{sy0:.2f} {x2-c:.2f},{ty0:.2f} {x2:.2f},{ty0:.2f} "
            f"L {x2:.2f},{ty1:.2f} C {x2-c:.2f},{ty1:.2f} {x1+c:.2f},{sy1:.2f} {x1:.2f},{sy1:.2f} Z"
        )

    for s, t, v, c in links:
        thick = max(1.5, v * scale)
        sg, tg = geom[s], geom[t]
        sy0 = sg.y + out_off[s]
        sy1 = sy0 + thick
        ty0 = tg.y + in_off[t]
        ty1 = ty0 + thick
        out_off[s] += thick
        in_off[t] += thick
        path = link_path(sg, tg, sy0, sy1, ty0, ty1)
        elements.append(f'<path d="{path}" fill="{rgba(c,0.35)}" stroke="none"/>')

    total_leak = sum(values[n] for n in LEAKAGE_NODES)
    for n in NODE_ORDER:
        g = geom[n]
        rgb = COLORS[n]
        elements.append(f'<rect x="{g.x:.2f}" y="{g.y:.2f}" width="{g.w:.2f}" height="{g.h:.2f}" fill="rgb({rgb[0]},{rgb[1]},{rgb[2]})" stroke="#333" stroke-width="0.4"/>')
        lbl = f"{DISPLAY[n]} ({fmt_mt(values[n])})"
        if n in LEAKAGE_NODES and total_leak > 0:
            lbl += f" [{values[n]/total_leak*100:.1f}%]"
        tx = g.x + g.w + 6 if n in COLLECTION_NODES + TREATMENT_NODES else g.x - 6
        anchor = "start" if n in COLLECTION_NODES + TREATMENT_NODES else "end"
        elements.append(f'<text x="{tx:.2f}" y="{g.y + g.h/2 + 3:.2f}" font-size="10" text-anchor="{anchor}">{lbl}</text>')

    return "\n".join(elements)


def write_svg(path, scenario, annual_vals, cum_vals):
    width, height = 1800, 980
    panel_w = (width - 60) / 2
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect x="0" y="0" width="100%" height="100%" fill="white"/>',
        f'<text x="30" y="30" font-size="22" font-weight="700">{scenario} pathway Sankey (variant = CENTRAL)</text>',
        sankey_panel_svg(annual_vals, f"Annual snapshot ({ANNUAL_YEAR})", 20, 50, panel_w, 900),
        sankey_panel_svg(cum_vals, "Cumulative total (simulation horizon)", 20 + panel_w + 20, 50, panel_w, 900),
        '</svg>'
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


def hex_color(rgb):
    return '#%02x%02x%02x' % rgb


def escape_pdf(s: str) -> str:
    return s.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')


def write_pdf(path, scenario, annual_vals, cum_vals):
    # Minimal vector PDF with rectangles, straight ribbon polygons, and text.
    W, H = 1800, 980
    panel_w = (W - 60) / 2

    def panel_ops(values, x0, y0, w, h):
        geom, scale = compute_panel_geometry(values, x0, y0, w, h)
        links = build_links(values)
        out_off = {n: 0.0 for n in NODE_ORDER}
        in_off = {n: 0.0 for n in NODE_ORDER}
        ops = []
        for s, t, v, c in links:
            thick = max(1.5, v * scale)
            sg, tg = geom[s], geom[t]
            y1 = sg.y + out_off[s]
            y2 = y1 + thick
            z1 = tg.y + in_off[t]
            z2 = z1 + thick
            out_off[s] += thick
            in_off[t] += thick
            x1 = sg.x + sg.w
            x2 = tg.x
            r,g,b = [x/255 for x in c]
            ops.append(f"{r:.3f} {g:.3f} {b:.3f} rg")
            ops.append("0.35 ca 0.35 CA")
            ops.append(f"{x1:.2f} {H-y1:.2f} m {x2:.2f} {H-z1:.2f} l {x2:.2f} {H-z2:.2f} l {x1:.2f} {H-y2:.2f} l h f")
            ops.append("1 ca 1 CA")
        total_leak = sum(values[n] for n in LEAKAGE_NODES)
        for n in NODE_ORDER:
            g = geom[n]
            r,gc,b = [x/255 for x in COLORS[n]]
            ops.append(f"{r:.3f} {gc:.3f} {b:.3f} rg")
            ops.append(f"{g.x:.2f} {H-(g.y+g.h):.2f} {g.w:.2f} {g.h:.2f} re f")
            ops.append("0 0 0 rg")
            lbl = f"{DISPLAY[n]} ({fmt_mt(values[n])})"
            if n in LEAKAGE_NODES and total_leak > 0:
                lbl += f" [{values[n]/total_leak*100:.1f}%]"
            tx = g.x + g.w + 6 if n in COLLECTION_NODES + TREATMENT_NODES else g.x - 180
            ty = H-(g.y + g.h/2 + 3)
            ops.append("BT /F1 9 Tf")
            ops.append(f"1 0 0 1 {tx:.2f} {ty:.2f} Tm ({escape_pdf(lbl)}) Tj ET")
        return ops

    ops = ["1 1 1 rg 0 0 1800 980 re f", "0 0 0 rg", "BT /F1 16 Tf 1 0 0 1 30 950 Tm (" + escape_pdf(f"{scenario} pathway Sankey (variant = CENTRAL)") + ") Tj ET"]
    ops += ["BT /F1 13 Tf 1 0 0 1 40 905 Tm (" + escape_pdf(f"Annual snapshot ({ANNUAL_YEAR})") + ") Tj ET"]
    ops += panel_ops(annual_vals, 20, 50, panel_w, 900)
    ops += ["BT /F1 13 Tf 1 0 0 1 930 905 Tm (" + escape_pdf("Cumulative total (simulation horizon)") + ") Tj ET"]
    ops += panel_ops(cum_vals, 20 + panel_w + 20, 50, panel_w, 900)
    content = "\n".join(ops).encode("latin-1", "replace")

    objs = []
    def add_obj(data: bytes):
        objs.append(data)
        return len(objs)

    font_obj = add_obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    content_obj = add_obj(b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream")
    page_obj = add_obj(f"<< /Type /Page /Parent 4 0 R /MediaBox [0 0 {W} {H}] /Contents {content_obj} 0 R /Resources << /Font << /F1 {font_obj} 0 R >> >> >>".encode())
    pages_obj = add_obj(f"<< /Type /Pages /Kids [{page_obj} 0 R] /Count 1 >>".encode())
    catalog_obj = add_obj(f"<< /Type /Catalog /Pages {pages_obj} 0 R >>".encode())

    out = bytearray(b"%PDF-1.4\n")
    xref = [0]
    for i, o in enumerate(objs, start=1):
        xref.append(len(out))
        out.extend(f"{i} 0 obj\n".encode())
        out.extend(o)
        out.extend(b"\nendobj\n")
    xref_pos = len(out)
    out.extend(f"xref\n0 {len(objs)+1}\n".encode())
    out.extend(b"0000000000 65535 f \n")
    for off in xref[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode())
    out.extend(f"trailer\n<< /Size {len(objs)+1} /Root {catalog_obj} 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode())
    with open(path, "wb") as f:
        f.write(out)


def write_png(path, scenario, annual_vals, cum_vals):
    # Lightweight raster fallback (600 dpi equivalent metadata stored as pHYs).
    W, H = 1800, 980
    pixels = bytearray([255, 255, 255] * W * H)

    def set_px(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            pixels[i:i+3] = bytes(c)

    def rect(x, y, w, h, c):
        x0, y0 = int(max(0, x)), int(max(0, y))
        x1, y1 = int(min(W, x + w)), int(min(H, y + h))
        for yy in range(y0, y1):
            row = (yy * W + x0) * 3
            pixels[row:row + (x1 - x0) * 3] = bytes(c) * (x1 - x0)

    def polygon(points, c):
        ys = [p[1] for p in points]
        y_min, y_max = int(max(0, min(ys))), int(min(H-1, max(ys)))
        for y in range(y_min, y_max + 1):
            xs = []
            for i in range(len(points)):
                x1,y1 = points[i]
                x2,y2 = points[(i+1)%len(points)]
                if y1 == y2:
                    continue
                if (y >= min(y1,y2)) and (y < max(y1,y2)):
                    x = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                    xs.append(x)
            xs.sort()
            for i in range(0, len(xs), 2):
                if i+1 >= len(xs):
                    break
                xa, xb = int(max(0, xs[i])), int(min(W-1, xs[i+1]))
                for x in range(xa, xb+1):
                    set_px(x, y, c)

    def draw_panel(values, x0, y0, w, h):
        geom, scale = compute_panel_geometry(values, x0, y0, w, h)
        links = build_links(values)
        out_off = {n: 0.0 for n in NODE_ORDER}
        in_off = {n: 0.0 for n in NODE_ORDER}
        for s,t,v,c in links:
            thick = max(1.5, v*scale)
            sg,tg = geom[s], geom[t]
            sy0 = sg.y + out_off[s]; sy1 = sy0 + thick
            ty0 = tg.y + in_off[t]; ty1 = ty0 + thick
            out_off[s] += thick; in_off[t] += thick
            x1,x2 = sg.x+sg.w, tg.x
            cc = tuple(int(0.65*255 + 0.35*ch) for ch in c)
            polygon([(x1,sy0),(x2,ty0),(x2,ty1),(x1,sy1)], cc)
        for n in NODE_ORDER:
            g = geom[n]
            rect(g.x,g.y,g.w,g.h,COLORS[n])

    panel_w = (W - 60) / 2
    draw_panel(annual_vals, 20, 50, panel_w, 900)
    draw_panel(cum_vals, 20 + panel_w + 20, 50, panel_w, 900)

    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)
        raw.extend(pixels[y*stride:(y+1)*stride])

    def chunk(tag, data):
        import struct
        return struct.pack('!I', len(data)) + tag + data + struct.pack('!I', zlib.crc32(tag + data) & 0xffffffff)

    import struct
    png = bytearray(b"\x89PNG\r\n\x1a\n")
    png.extend(chunk(b'IHDR', struct.pack('!IIBBBBB', W, H, 8, 2, 0, 0, 0)))
    ppm = int(600 / 0.0254)  # 600 dpi
    png.extend(chunk(b'pHYs', struct.pack('!IIB', ppm, ppm, 1)))
    png.extend(chunk(b'IDAT', zlib.compress(bytes(raw), level=9)))
    png.extend(chunk(b'IEND', b''))
    with open(path, 'wb') as f:
        f.write(png)


def main():
    annual_rows = read_rows("annual_pathway_diagnostics.csv")
    cumulative_rows = read_rows("cumulative_pathway_diagnostics.csv")
    out_dir = os.path.join("figures", "sankey")
    os.makedirs(out_dir, exist_ok=True)

    for scn in SCENARIOS:
        a = get_annual_values(annual_rows, scn)
        c = get_cumulative_values(cumulative_rows, scn)
        base = os.path.join(out_dir, f"{scn.lower()}_central_annual{ANNUAL_YEAR}_vs_cumulative_sankey")
        write_svg(base + ".svg", scn, a, c)
        write_pdf(base + ".pdf", scn, a, c)
        write_png(base + ".png", scn, a, c)
    print(f"Wrote Sankey files to {out_dir}")


if __name__ == "__main__":
    main()
