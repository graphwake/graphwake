"""Builds assets/hero-light.svg and profile/hero-dark.svg.

The hero replays three pushes to GET /orders/{id}. A breaking change lights the routes to the teams subscribed to the
endpoint; a non-breaking one lights nothing. Pure CSS animation inside the SVG, because GitHub renders README images
as <img> (no script, no external fonts), so Geist is embedded. With reduced motion the first scene shows, static.

Run: python3 scripts/build_hero.py <path to doc-sync>
"""

import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC_SYNC = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT.parent / "doc-sync")
FONT_DIR = DOC_SYNC / "landing-page/node_modules/next/dist/next-devtools/server/font"

# Tokens from landing-page/src/app/globals.css and brand/README.md.
THEMES = {
    "light": dict(ground="#f4f6f5", surface="#ffffff", ink="#1b2430", muted="#5b6573", faint="#8a93a0",
                  line="#d9dee3", route="#2f5bea", route_soft="#e6ecfd", removed="#c8323c", removed_soft="#fbe9ea",
                  changed="#8f5a0b", changed_soft="#fbf1e2", row="#f4f6f5"),
    "dark": dict(ground="#0a0d14", surface="#111622", ink="#edf0f5", muted="#9aa4b2", faint="#6b7584",
                 line="#262e3d", route="#6e8bff", route_soft="#18214a", removed="#ff6b73", removed_soft="#3a1519",
                 changed="#f0b357", changed_soft="#33240d", row="#161c2a"),
}

W, H = 960, 420
LOOP = 13.5  # seconds, three scenes
SCENES = 3

TEAMS = [("search", 3), ("checkout", 4), ("inventory", 2), ("mobile-app", 6), ("storefront", 5)]
CHANGES = [  # (sign, field, label, kind, breaking)
    ("−", "total", "removed", "removed", True),
    ("+", "discounts", "added", "added", False),
    ("~", "currency", "now required", "changed", True),
]
# scene -> (change index, notified team indexes, caption, status)
PLAY = [
    (0, [1, 3], "Breaking. Sent to checkout and mobile-app: 10 people.", "total was removed"),
    (1, [], "Not breaking. A new optional field stays quiet.", "discounts was added"),
    (2, [1, 3, 4], "Breaking. Sent to checkout, mobile-app and storefront: 15 people.", "currency is now required"),
]

ORIGIN = (392, 222)
CHIP_X, CHIP_W, CHIP_H = 640, 288, 44
CHIP_YS = [84 + i * 58 for i in range(len(TEAMS))]


def font_face(family: str, file: str) -> str:
    data = base64.b64encode((FONT_DIR / file).read_bytes()).decode()
    return (f"@font-face{{font-family:'{family}';font-weight:100 900;"
            f"src:url(data:font/woff2;base64,{data}) format('woff2');}}")


def keyframes(name: str, active: list[int], on: float = 1, off: float = 0, delay: float = 0) -> str:
    """Opacity-style keyframes: `on` during the scenes in `active`, `off` otherwise."""
    span = 100 / SCENES
    stops = []
    for s in range(SCENES):
        start = s * span
        v = on if s in active else off
        stops += [(start + 0.01, None), (start + 2 + delay, v), (start + span - 3, v), (start + span - 0.5, off)]
    frames = [f"0%{{opacity:{off}}}"]
    for pct, v in stops:
        if v is not None:
            frames.append(f"{pct:.2f}%{{opacity:{v}}}")
    frames.append(f"100%{{opacity:{off}}}")
    return f"@keyframes {name}{{{''.join(frames)}}}"


def draw_keyframes(name: str, active: list[int]) -> str:
    """Route draw-in: dash offset 1 -> 0 shortly after the scene starts, then fade."""
    span = 100 / SCENES
    frames = ["0%{stroke-dashoffset:1;opacity:0}"]
    for s in range(SCENES):
        start = s * span
        if s in active:
            frames += [f"{start + 4:.2f}%{{stroke-dashoffset:1;opacity:1}}",
                       f"{start + 10:.2f}%{{stroke-dashoffset:0;opacity:1}}",
                       f"{start + span - 3:.2f}%{{stroke-dashoffset:0;opacity:1}}",
                       f"{start + span - 0.5:.2f}%{{stroke-dashoffset:0;opacity:0}}",
                       f"{start + span - 0.4:.2f}%{{stroke-dashoffset:1;opacity:0}}"]
    frames.append("100%{stroke-dashoffset:1;opacity:0}")
    return f"@keyframes {name}{{{''.join(frames)}}}"


def route_path(i: int) -> str:
    ox, oy = ORIGIN
    ty = CHIP_YS[i] + CHIP_H / 2
    mx = (ox + CHIP_X) / 2
    return f"M{ox} {oy} C {mx} {oy}, {mx} {ty}, {CHIP_X} {ty}"


def notified_in(team: int) -> list[int]:
    return [s for s, (_, teams, _, _) in enumerate(PLAY) if team in teams]


def build(theme: str) -> str:
    t = THEMES[theme]
    css = [
        font_face("Geist", "geist-latin.woff2"),
        font_face("Geist Mono", "geist-mono-latin.woff2"),
        ".sans{font-family:'Geist',system-ui,sans-serif}",
        ".mono{font-family:'Geist Mono',ui-monospace,monospace}",
        f".anim{{animation-duration:{LOOP}s;animation-iteration-count:infinite;animation-timing-function:ease-out}}",
    ]
    body = []

    # Frame
    body.append(f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="18" fill="{t["surface"]}" '
                f'stroke="{t["line"]}"/>')

    # Status line: a live dot, then which push is replaying.
    css.append("@keyframes blink{0%,100%{opacity:1}50%{opacity:.35}}")
    css.append(".dot{animation:blink 1.6s ease-in-out infinite}")
    body.append(f'<circle class="dot" cx="40" cy="44" r="5" fill="{t["route"]}"/>')
    body.append(f'<text x="56" y="49" class="sans" font-size="15" fill="{t["muted"]}">Replaying recent pushes to'
                f' <tspan class="mono" fill="{t["ink"]}">orders-api</tspan></text>')
    for s, (_, _, _, status) in enumerate(PLAY):
        name = f"st{s}"
        css.append(keyframes(name, [s]))
        css.append(f".{name}{{opacity:{1 if s == 0 else 0};animation-name:{name}}}")
        body.append(f'<text x="{W - 32}" y="49" text-anchor="end" class="sans anim {name}" font-size="15" '
                    f'fill="{t["muted"]}">Push {s + 1} of 3: {status}</text>')

    # Diff card
    dx, dy, dw = 32, 84, 360
    body.append(f'<rect x="{dx}" y="{dy}" width="{dw}" height="276" rx="12" fill="{t["ground"]}" '
                f'stroke="{t["line"]}"/>')
    body.append(f'<text x="{dx + 20}" y="{dy + 34}" class="mono" font-size="14" fill="{t["muted"]}">'
                f'openapi.json  v1.4 to v1.5</text>')
    body.append(f'<text x="{dx + 20}" y="{dy + 70}" class="mono" font-size="20" font-weight="500" '
                f'fill="{t["ink"]}">GET /orders/{{id}}</text>')
    body.append(f'<line x1="{dx}" y1="{dy + 92}" x2="{dx + dw}" y2="{dy + 92}" stroke="{t["line"]}"/>')
    tone = {"removed": (t["removed"], t["removed_soft"]), "changed": (t["changed"], t["changed_soft"]),
            "added": (t["muted"], t["row"])}
    for r, (sign, field, label, kind, breaking) in enumerate(CHANGES):
        ry = dy + 108 + r * 54
        fg, soft = tone[kind]
        scenes = [s for s, (ci, _, _, _) in enumerate(PLAY) if ci == r]
        name = f"row{r}"
        css.append(keyframes(name, scenes))
        css.append(f".{name}{{opacity:{1 if 0 in scenes else 0};animation-name:{name}}}")
        body.append(f'<rect class="anim {name}" x="{dx + 10}" y="{ry}" width="{dw - 20}" height="44" rx="8" '
                    f'fill="{soft}" stroke="{fg}" stroke-opacity=".5"/>')
        body.append(f'<text x="{dx + 26}" y="{ry + 28}" class="mono" font-size="17" fill="{fg}">'
                    f'{sign} {field}</text>')
        tag = "breaking" if breaking else "safe"
        body.append(f'<text x="{dx + dw - 26}" y="{ry + 28}" text-anchor="end" class="sans" font-size="14" '
                    f'fill="{t["muted"]}">{label}, {tag}</text>')

    # Routes: idle hairlines always, live strokes draw in when a breaking change reaches the team.
    for i in range(len(TEAMS)):
        d = route_path(i)
        body.append(f'<path d="{d}" fill="none" stroke="{t["line"]}" stroke-width="1.5"/>')
    for i in range(len(TEAMS)):
        scenes = notified_in(i)
        if not scenes:
            continue
        name = f"rt{i}"
        css.append(draw_keyframes(name, scenes))
        static = "stroke-dashoffset:0;opacity:1" if 0 in scenes else "opacity:0"
        css.append(f".{name}{{{static};animation-name:{name}}}")
        body.append(f'<path class="anim {name}" d="{route_path(i)}" pathLength="1" stroke-dasharray="1" '
                    f'fill="none" stroke="{t["route"]}" stroke-width="2.5" stroke-linecap="round"/>')
    ox, oy = ORIGIN
    body.append(f'<circle cx="{ox}" cy="{oy}" r="5" fill="{t["surface"]}" stroke="{t["route"]}" stroke-width="2"/>')

    # Team chips: idle chip, with a lit copy on top that fades in when the team is notified.
    for i, (team, people) in enumerate(TEAMS):
        y = CHIP_YS[i]
        scenes = notified_in(i)

        def chip(fill, stroke, width, note, note_fill):
            return (f'<rect x="{CHIP_X}" y="{y}" width="{CHIP_W}" height="{CHIP_H}" rx="22" fill="{fill}" '
                    f'stroke="{stroke}" stroke-width="{width}"/>'
                    f'<text x="{CHIP_X + 22}" y="{y + 28}" class="mono" font-size="16" fill="{t["ink"]}">{team}</text>'
                    f'<text x="{CHIP_X + CHIP_W - 22}" y="{y + 28}" text-anchor="end" class="sans" font-size="14" '
                    f'fill="{note_fill}">{note}</text>')

        body.append(chip(t["ground"], t["line"], 1, f"{people} people", t["faint"]))
        if scenes:
            name = f"chip{i}"
            css.append(keyframes(name, scenes, delay=6))
            css.append(f".{name}{{opacity:{1 if 0 in scenes else 0};animation-name:{name}}}")
            body.append(f'<g class="anim {name}">'
                        + chip(t["route_soft"], t["route"], 1.5, f"{people} people notified", t["route"]) + '</g>')

    # Caption
    for s, (_, _, caption, _) in enumerate(PLAY):
        name = f"cap{s}"
        css.append(keyframes(name, [s], delay=6))
        css.append(f".{name}{{opacity:{1 if s == 0 else 0};animation-name:{name}}}")
        body.append(f'<text x="32" y="{H - 28}" class="sans anim {name}" font-size="17" font-weight="500" '
                    f'fill="{t["ink"]}">{caption}</text>')
    body.append(f'<text x="{W - 32}" y="{H - 28}" text-anchor="end" class="sans" font-size="15" '
                f'fill="{t["faint"]}">Teams that don’t call it hear nothing.</text>')

    css.append("@media (prefers-reduced-motion:reduce){.anim,.dot{animation:none!important}}")
    title = ("A breaking change to GET /orders/{id} is routed only to the teams subscribed to it, "
             "checkout and mobile-app. A non-breaking addition notifies nobody.")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
            f'role="img" aria-label="{title}"><title>{title}</title>'
            f'<style>{"".join(css)}</style>{"".join(body)}</svg>\n')


if __name__ == "__main__":
    for theme in THEMES:
        out = ROOT / "assets" / f"hero-{theme}.svg"
        out.write_text(build(theme), encoding="utf-8")
        print(out, out.stat().st_size // 1024, "KB")
