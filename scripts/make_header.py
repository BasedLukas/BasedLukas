"""Generate the animated terminal header (assets/header-dark.svg and header-light.svg).

Run:  uv run --with fonttools --with brotli scripts/make_header.py

Edit WHOAMI and LINES below to change the text. The font is subset to the
characters used and embedded, because GitHub shows the SVG as an image and an
image cannot load web fonts.
"""

import base64
import io
from html import escape
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "scripts/fonts/JetBrainsMono-Regular.ttf"

PROMPT = "lukas@latent_space:~$ "
WHOAMI = "technical founder · computer programming and machine learning expert"
# (command, [(output line, [(text, colour role), ...]), ...])
LINES = [
    ("whoami", [[(WHOAMI, "fg")]]),
    ("cat skills.txt", [
        [("founder     ", "key"), ("building products and companies as a technical founder", "fg")],
        [("leadership  ", "key"), ("leading engineering teams and owning technical direction", "fg")],
        [("web apps    ", "key"), ("full-stack web applications, APIs and cloud infrastructure", "fg")],
        [("pipelines   ", "key"), ("data pipelines that move and transform data reliably at scale", "fg")],
        [("scraping    ", "key"), ("crawlers and extractors for messy, JavaScript-heavy websites", "fg")],
        [("processing  ", "key"), ("cleaning, deduplicating and enriching large datasets", "fg")],
        [("modelling   ", "key"), ("training and evaluating statistical and machine learning models", "fg")],
    ]),
]
THEMES = {
    "dark": dict(bg="#0b0a08", fg="#f4e3c1", prompt="#ffb340", key="#8fd3c8", dim="#7d6f57", rule="#2a251c"),
    "light": dict(bg="#fbf6ea", fg="#2b2418", prompt="#a35d00", key="#1f6f66", dim="#9b8d73", rule="#e8dfcb"),
}

W, X, SIZE = 800, 28, 14
CW = SIZE * 0.6  # JetBrains Mono advance width is 600/1000 em
LINE_H = 24
TYPE_SPEED = 0.075  # seconds per typed character


def font_face(text: str) -> str:
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = []
    font = TTFont(FONT)
    sub = subset.Subsetter(opts)
    sub.populate(text=text)
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    data = base64.b64encode(buf.getvalue()).decode()
    return f"@font-face{{font-family:'JBM';src:url(data:font/woff2;base64,{data}) format('woff2');}}"


def build(theme: dict, face: str) -> str:
    defs, body = [], []
    t, y = 0.5, 74
    for i, (cmd, outputs) in enumerate(LINES):
        n = len(cmd)
        dur = (n + 1) * TYPE_SPEED
        widths = ";".join(f"{(len(PROMPT) + k) * CW + 6:.1f}" for k in range(n + 1))
        times = ";".join(f"{k / (n + 1):.3f}" for k in range(n + 1))
        defs.append(
            f'<clipPath id="c{i}"><rect x="{X - 4}" y="{y - 17}" height="24" width="0">'
            f'<animate attributeName="width" values="{widths}" keyTimes="{times}" calcMode="discrete" '
            f'begin="{t:.2f}s" dur="{dur:.3f}s" fill="freeze"/></rect></clipPath>'
        )
        body.append(
            f'<text x="{X}" y="{y}" clip-path="url(#c{i})"><tspan fill="{theme["prompt"]}">{escape(PROMPT)}</tspan>'
            f'<tspan x="{X + len(PROMPT) * CW:.1f}" fill="{theme["fg"]}">{escape(cmd)}</tspan></text>'
        )
        t += dur + 0.3
        y += LINE_H
        for parts in outputs:
            spans, col = "", 0
            for txt, role in parts:  # explicit x per segment so column padding survives whitespace collapsing
                spans += f'<tspan x="{X + col * CW:.1f}" fill="{theme[role]}">{escape(txt.rstrip())}</tspan>'
                col += len(txt)
            body.append(
                f'<text x="{X}" y="{y}" opacity="0">{spans}'
                f'<set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/></text>'
            )
            t += 0.12
            y += LINE_H
        t += 0.45
        y += 8
    body.append(
        f'<text x="{X}" y="{y}" opacity="0" fill="{theme["prompt"]}">{escape(PROMPT)}'
        f'<set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/></text>'
    )
    body.append(
        f'<rect x="{X + len(PROMPT) * CW:.1f}" y="{y - 14}" width="9" height="18" opacity="0" fill="{theme["prompt"]}">'
        f'<animate attributeName="opacity" values="1;0" dur="1.06s" begin="{t:.2f}s" repeatCount="indefinite" calcMode="discrete"/></rect>'
    )
    h = y + 22
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" '
        f'xml:space="preserve" role="img" aria-labelledby="title">\n'
        f"<title id=\"title\">{escape(WHOAMI)}</title>\n"
        f"<style>{face} text{{font-family:'JBM',ui-monospace,Menlo,monospace;font-size:{SIZE}px;}}</style>\n"
        f"<defs>{''.join(defs)}</defs>\n"
        f'<rect width="{W}" height="{h}" rx="10" fill="{theme["bg"]}"/>\n'
        f'<text x="{X}" y="32" style="font-size:12px" fill="{theme["dim"]}">tty1</text>\n'
        f'<text x="{W - X}" y="32" style="font-size:12px" text-anchor="end" fill="{theme["dim"]}">loreley.one</text>\n'
        f'<rect x="{X}" y="44" width="{W - 2 * X}" height="1" fill="{theme["rule"]}"/>\n'
        + "\n".join(body)
        + "\n</svg>\n"
    )


def main() -> None:
    chars = PROMPT + "tty1loreley.one"
    for cmd, outputs in LINES:
        chars += cmd + "".join(txt for parts in outputs for txt, _ in parts)
    face = font_face(chars)
    for name, theme in THEMES.items():
        out = ROOT / f"assets/header-{name}.svg"
        out.write_text(build(theme, face))
        print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
