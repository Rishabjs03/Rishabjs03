#!/usr/bin/env python3
"""
Build wordmark.svg: a pixel-font "RISHAB / AGARWAL" wordmark inside a dark
terminal window. Pixels cascade in left-to-right (one-shot CSS keyframes, then
freeze), a tagline types itself in underneath, and a prompt with a blinking
cursor sits in the status bar.

No photo needed and no third-party service -- everything lives in this file so
GitHub renders it via <img> with the animation intact. Set STATIC=1 to emit a
frozen frame (handy for previews).

Sized to sit beside info-card.svg: 370px wide, same height.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "wordmark.svg")
STATIC = bool(os.environ.get("STATIC"))

# Shared terminal theme (keep in sync with the other generators)
BG, BG2, FRAME = "#0d1117", "#131a24", "#30363d"
MUTED, TEXT, ACCENT, GREEN = "#7d8590", "#e6edf3", "#22d3ee", "#39d353"

W, H = 370, 300
PAD, TITLEBAR_H, STATUS_H = 20, 30, 30
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

LINES = ["RISHAB", "AGARWAL"]
TAGLINE = "building intelligent web experiences"

# 5x7 pixel glyphs
GLYPHS = {
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "I": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "G": [".####", "#....", "#....", "#.###", "#...#", "#...#", ".####"],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
}
GLYPH_W, GLYPH_H, GLYPH_GAP = 5, 7, 1


def word_columns(word):
    return len(word) * GLYPH_W + (len(word) - 1) * GLYPH_GAP


def pixels(word):
    """Yield (col, row) for every lit pixel in the word."""
    x0 = 0
    for ch in word:
        for r, row in enumerate(GLYPHS[ch]):
            for c, bit in enumerate(row):
                if bit == "#":
                    yield x0 + c, r
        x0 += GLYPH_W + GLYPH_GAP


art_w = W - 2 * PAD
max_cols = max(word_columns(w) for w in LINES)
step = art_w / max_cols
cell = step * 0.82
row_gap = step * 1.2
words_h = len(LINES) * GLYPH_H * step + (len(LINES) - 1) * row_gap

status_line_y = H - STATUS_H
content_h = words_h + 34 + 8                       # wordmark + tagline block
art_top = TITLEBAR_H + (status_line_y - TITLEBAR_H - content_h) / 2 + 4
tag_y = art_top + words_h + 34
assert tag_y + 8 < status_line_y, "wordmark content overflows the canvas"

COL_T, ROW_T, DUR = 0.035, 0.05, 0.45
wm_total = max_cols * COL_T + (len(LINES) * GLYPH_H + 3) * ROW_T + DUR
TYPE_START = round(wm_total, 2)
TYPE_DUR = round(len(TAGLINE) * 0.04, 2)

css = "" if STATIC else (
    "@keyframes px{0%{opacity:0;transform:translateY(-5px)}100%{opacity:1;transform:translateY(0)}}"
    f".p{{opacity:0;animation:px {DUR}s cubic-bezier(.2,.8,.2,1) both}}"
    "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}"
    ".k{animation:blink 1s step-end infinite}"
)

p = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
    f"<style>{css}</style>",
    "<defs>",
    f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient>',
    f'<linearGradient id="ink" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{ACCENT}"/><stop offset="1" stop-color="{GREEN}"/></linearGradient>',
    "</defs>",
    f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>',
    f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
]
for i, dot in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
    p.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dot}"/>')
p.append(f'<text x="{W/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" text-anchor="middle">rishab@github: ~$ ./hello.sh</text>')

y = art_top
for li, word in enumerate(LINES):
    fill = "url(#ink)" if li == 0 else TEXT
    x_off = PAD + (art_w - word_columns(word) * step) / 2  # center each word
    for c, r in pixels(word):
        gx, gy = x_off + c * step, y + r * step
        delay = c * COL_T + (li * (GLYPH_H + 1) + r) * ROW_T
        anim = "" if STATIC else f' class="p" style="animation-delay:{delay:.3f}s"'
        p.append(f'<rect{anim} x="{gx:.2f}" y="{gy:.2f}" width="{cell:.2f}" height="{cell:.2f}" rx="1.6" fill="{fill}"/>')
    y += GLYPH_H * step + row_gap

# tagline: typed in with a clip wipe after the wordmark lands
tag_w = len(TAGLINE) * 12 * 0.6 + 14
tag_x = (W - tag_w) / 2
tag = (f'<text x="{tag_x:.1f}" y="{tag_y:.1f}" font-size="12" fill="{MUTED}">'
       f'<tspan fill="{GREEN}">&gt;</tspan> {TAGLINE}</text>')
if STATIC:
    p.append(tag)
else:
    p.append(f'<clipPath id="tw"><rect x="{tag_x - 2:.1f}" y="{tag_y - 14:.1f}" height="20" width="0">'
             f'<animate attributeName="width" from="0" to="{tag_w + 4:.1f}" begin="{TYPE_START}s" dur="{TYPE_DUR}s" fill="freeze"/>'
             f"</rect></clipPath>")
    p.append(f'<g clip-path="url(#tw)">{tag}</g>')

# status bar
sy = status_line_y + 19
p.append(f'<line x1="0" y1="{status_line_y}" x2="{W}" y2="{status_line_y}" stroke="{FRAME}"/>')
p.append(f'<text x="{PAD}" y="{sy}" fill="{MUTED}" font-size="12">rishab@github:~$ <tspan fill="{TEXT}">whoami</tspan></text>')
cursor_x = PAD + len("rishab@github:~$ whoami ") * 12 * 0.6
p.append(f'<rect class="k" x="{cursor_x:.1f}" y="{sy - 11}" width="7" height="13" fill="{TEXT}"/>')
p.append("</svg>")

svg = "".join(p)
with open(OUT, "w") as f:
    f.write(svg)
print(f"wrote {os.path.relpath(OUT)} ({len(svg)} bytes; {W}x{H}; typing starts at {TYPE_START}s)")
