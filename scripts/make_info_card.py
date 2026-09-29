#!/usr/bin/env python3
"""
Build info-card.svg: a neofetch-style "system info" card about me -- the story
a stats widget can't tell (what I'm doing now, where I've been, what I build
with). Lines fade and slide in with a short stagger (one-shot CSS keyframes),
then hold. A neofetch-style colour strip closes the card.

Edit FIELDS below to update the content, then re-run. Set STATIC=1 to emit a
frozen frame. Sized to sit beside wordmark.svg: 490px wide, same height.
"""
import html
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "info-card.svg")
STATIC = bool(os.environ.get("STATIC"))

BG, BG2, FRAME = "#0d1117", "#131a24", "#30363d"
MUTED, TEXT, ACCENT, GREEN, GOLD = "#7d8590", "#e6edf3", "#22d3ee", "#39d353", "#f2cc60"
SWATCHES = ["#ff5f56", "#ffbd2e", "#27c93f", "#22d3ee", "#a371f7", "#f778ba", "#e6edf3", "#7d8590"]

W, H = 490, 300
PAD, TITLEBAR_H = 20, 30
FONT_SIZE, LINE_H = 12, 18
CHAR_W = FONT_SIZE * 0.6            # monospace advance, used to keep lines inside the card
LABEL_W = 11 * CHAR_W               # value column starts here
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

USER_HOST = "rishab@github"
# (label, value, colour). Empty label = continuation line.
FIELDS = [
    ("Role", "AI Engineer & Full Stack Developer", TEXT),
    ("Now", "AI Engineer @ Array Education (2026 →)", TEXT),
    ("", "└ end-to-end AI Video Studio for career content", MUTED),
    ("Prev", "NAWKOUT · AI-powered CEO CRM, concept → prod", TEXT),
    ("", "AskGuru.ai · chatbot architecture + UI/UX", TEXT),
    ("Stack", "Next.js · TypeScript · Python · LangChain", TEXT),
    ("", "Claude API · Supabase · Postgres · MongoDB", TEXT),
    ("Building", "Gemini-Supermemory · MacClaw", TEXT),
    ("Focus", "agentic systems · AI products · web platforms", TEXT),
    ("Web", "rishabjs.xyz", GREEN),
]

max_value_chars = int((W - 2 * PAD - LABEL_W) / CHAR_W)
for label, value, _ in FIELDS:
    assert len(value) <= max_value_chars, f"too long ({len(value)} > {max_value_chars}): {value!r}"

STAGGER, DUR = 0.09, 0.45
css = "" if STATIC else (
    "@keyframes in{0%{opacity:0;transform:translateX(-10px)}100%{opacity:1;transform:translateX(0)}}"
    f".l{{opacity:0;animation:in {DUR}s cubic-bezier(.2,.8,.2,1) both}}"
)

p = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
    f"<style>{css}</style>",
    f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
    f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>',
    f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
]
for i, dot in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
    p.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dot}"/>')
p.append(f'<text x="{W/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" text-anchor="middle">rishab@github: ~$ neofetch</text>')

line_no = 0


def line(inner, x=PAD):
    global line_no
    y = TITLEBAR_H + 22 + line_no * LINE_H
    anim = "" if STATIC else f' class="l" style="animation-delay:{line_no * STAGGER:.2f}s"'
    p.append(f'<text{anim} x="{x}" y="{y}" font-size="{FONT_SIZE}" xml:space="preserve">{inner}</text>')
    line_no += 1
    return y


line(f'<tspan fill="{ACCENT}" font-weight="700">{USER_HOST}</tspan>')
line(f'<tspan fill="{MUTED}">{"─" * len(USER_HOST)}</tspan>')
for label, value, colour in FIELDS:
    lab = f'<tspan fill="{GOLD}" font-weight="700">{html.escape(label)}</tspan>' if label else ""
    val = f'<tspan x="{PAD + LABEL_W:.1f}" fill="{colour}">{html.escape(value)}</tspan>'
    line(lab + val)

# neofetch colour strip
sw_y = TITLEBAR_H + 22 + line_no * LINE_H - 4
sw = 22
assert sw_y + 12 <= H - 10, "info card content overflows the canvas"
anim = "" if STATIC else f' class="l" style="animation-delay:{line_no * STAGGER:.2f}s"'
p.append(f"<g{anim}>")
for i, colour in enumerate(SWATCHES):
    p.append(f'<rect x="{PAD + i*sw}" y="{sw_y}" width="{sw}" height="12" fill="{colour}"/>')
p.append("</g></svg>")

svg = "".join(p)
with open(OUT, "w") as f:
    f.write(svg)
print(f"wrote {os.path.relpath(OUT)} ({len(svg)} bytes; {W}x{H}; {line_no} lines)")
