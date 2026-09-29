#!/usr/bin/env python3
"""
Render data/contributions.json as a self-contained, animated GitHub-style
contribution heatmap SVG (contrib-heatmap.svg).

53 weeks x 7 days of rounded boxes inside a dark terminal window. Boxes reveal
once with a diagonal cascade (CSS keyframes inside the SVG -- GitHub renders
<img> SVGs with their embedded CSS/SMIL, so no JS or external CSS is needed),
then freeze. A Less->More legend and a stats footer (total, streaks, best day)
sit underneath.

Run by .github/workflows/update-profile-art.yml after fetch_contributions.py.
"""
import datetime
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
IN_PATH = os.path.join(HERE, "..", "data", "contributions.json")
OUT_PATH = os.path.join(HERE, "..", "contrib-heatmap.svg")

# Shared terminal theme (keep in sync with make_info_card.py / make_wordmark_svg.py)
BG = "#0d1117"
BG2 = "#131a24"
FRAME = "#30363d"
MUTED = "#7d8590"
TEXT = "#e6edf3"
ACCENT = "#22d3ee"
GREEN = "#39d353"
GOLD = "#f2cc60"
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

CELL, GAP = 12, 3
STEP = CELL + GAP
PAD = 22
LEFT_LABEL_W = 30
TOP_LABEL_H = 20
TITLEBAR_H = 30
STATS_H = 88

COL_T, ROW_T, CELL_DUR = 0.018, 0.045, 0.42  # one-shot reveal timing

STATIC = bool(os.environ.get("STATIC"))


def level_for(count):
    for lvl, ceiling in enumerate((0, 5, 15, 30, 50)):
        if count <= ceiling:
            return lvl
    return 5


def build_grid(days):
    """Columns are weeks (Sun..Sat); pad the first week so weekdays line up."""
    first = datetime.date.fromisoformat(days[0]["date"])
    col = [None] * ((first.weekday() + 1) % 7)
    grid = []
    for d in days:
        date = datetime.date.fromisoformat(d["date"])
        while len(col) < (date.weekday() + 1) % 7:
            col.append(None)
        col.append((d["date"], d["count"], level_for(d["count"])))
        if len(col) == 7:
            grid.append(col)
            col = []
    if col:
        grid.append(col + [None] * (7 - len(col)))
    return grid


def month_labels(grid):
    labels, seen = [], set()
    for ci, column in enumerate(grid):
        for cell in column:
            if cell is None:
                continue
            date = datetime.date.fromisoformat(cell[0])
            key = (date.year, date.month)
            if key not in seen and date.day <= 7:
                seen.add(key)
                labels.append((ci, date.strftime("%b")))
            break
    return labels


def render(data):
    grid = build_grid(data["days"])
    art_w, art_h = len(grid) * STEP, 7 * STEP
    w = PAD + LEFT_LABEL_W + art_w + PAD
    h = TITLEBAR_H + TOP_LABEL_H + art_h + STATS_H + PAD
    grid_top, grid_left = TITLEBAR_H + TOP_LABEL_H, PAD + LEFT_LABEL_W

    css = "" if STATIC else (
        "@keyframes cell{0%{opacity:0;transform:translateY(-6px)}100%{opacity:1;transform:translateY(0)}}"
        f".c{{opacity:0;animation:cell {CELL_DUR:.2f}s cubic-bezier(.2,.8,.2,1) both}}"
    )

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        f"<style>{css}</style>",
        f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
        f'<rect width="{w}" height="{h}" rx="12" fill="url(#bg)"/>',
        f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12" fill="none" stroke="{FRAME}"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{w}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]
    for i, dot in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        p.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dot}"/>')
    p.append(f'<text x="{w/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" text-anchor="middle">'
             'rishab@github: ~/contributions --graph</text>')

    for ci, label in month_labels(grid):
        p.append(f'<text x="{grid_left + ci*STEP}" y="{TITLEBAR_H + 14}" fill="{MUTED}" font-size="10">{label}</text>')
    for wi, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        p.append(f'<text x="{PAD}" y="{grid_top + wi*STEP + CELL*0.78:.1f}" fill="{MUTED}" font-size="9">{name}</text>')

    for ci, column in enumerate(grid):
        gx = grid_left + ci * STEP
        for ri, cell in enumerate(column):
            if cell is None:
                continue
            date_s, count, lvl = cell
            gy = grid_top + ri * STEP
            anim = "" if STATIC else f' class="c" style="animation-delay:{ci*COL_T + ri*ROW_T:.3f}s"'
            s = "" if count == 1 else "s"
            p.append(f'<rect{anim} x="{gx}" y="{gy}" width="{CELL}" height="{CELL}" rx="2.5" fill="{PALETTE[lvl]}">'
                     f"<title>{date_s}: {count} contribution{s}</title></rect>")

    # legend
    leg_y = grid_top + art_h + 6
    lx = w - PAD - len(PALETTE) * CELL - 34
    p.append(f'<text x="{lx - 6}" y="{leg_y + CELL*0.8:.1f}" fill="{MUTED}" font-size="10" text-anchor="end">Less</text>')
    for color in PALETTE:
        p.append(f'<rect x="{lx}" y="{leg_y}" width="{CELL-1}" height="{CELL-1}" rx="2.2" fill="{color}"/>')
        lx += CELL
    p.append(f'<text x="{lx + 4}" y="{leg_y + CELL*0.8:.1f}" fill="{MUTED}" font-size="10">More</text>')

    # stats footer
    sep_y = leg_y + CELL + 14
    p.append(f'<line x1="0" y1="{sep_y}" x2="{w}" y2="{sep_y}" stroke="{FRAME}"/>')
    cs, ls = data["current_streak"]["length"], data["longest_streak"]["length"]
    best, rng = data["best_day"], data["range"]
    ly = sep_y + 24
    p.append(f'<text x="{PAD}" y="{ly}" font-size="13" fill="{GREEN}"><tspan font-weight="700">'
             f'{data["total_contributions"]:,}</tspan><tspan fill="{MUTED}"> contributions in the last year</tspan></text>')
    p.append(f'<text x="{w - PAD}" y="{ly}" font-size="12" fill="{MUTED}" text-anchor="end">{rng["start"]} &#8594; {rng["end"]}</text>')
    ly += 24
    p.append(f'<text x="{PAD}" y="{ly}" font-size="13" fill="{MUTED}">current streak '
             f'<tspan fill="{ACCENT}" font-weight="700">{cs} days</tspan>   &#183;   longest '
             f'<tspan fill="{ACCENT}" font-weight="700">{ls} days</tspan></text>')
    p.append(f'<text x="{w - PAD}" y="{ly}" font-size="12" fill="{MUTED}" text-anchor="end">best day '
             f'<tspan fill="{GOLD}" font-weight="700">{best["count"]}</tspan> on {best["date"]}</text>')
    p.append("</svg>")
    return "".join(p)


if __name__ == "__main__":
    with open(IN_PATH) as f:
        data = json.load(f)
    svg = render(data)
    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"wrote {os.path.relpath(OUT_PATH)} ({len(svg)} bytes)")
