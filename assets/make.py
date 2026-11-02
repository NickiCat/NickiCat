#!/usr/bin/env python3
"""Draws the README's SVGs: GitHub strips scripts and CSS from a README, but an SVG in <img> keeps its animations.

Text becomes outlines, so the look doesn't depend on the viewer's fonts. Needs fontTools and Pillow;
run with the folder holding Inter, Manrope and JetBrains Mono TTFs:
    python3 assets/make.py <fonts dir>
"""
import base64
import io
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from PIL import Image

HERE = Path(__file__).resolve().parent
FONTS = Path(sys.argv[1])
INK, MIST, FOG, FROST = "#ffffff", "#c7d3ea", "#9da7ba", "#d1e4fa"
VIOLET, TEAL, CANVAS, CARD = "#663af3", "#269684", "#05060f", "#0a0d1b"
EDGE = "#222938"
_fonts = {}


def font(name):
    if name not in _fonts:
        f = TTFont(FONTS / f"{name}.ttf")
        _fonts[name] = (f, f.getGlyphSet(), f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm)
    return _fonts[name]


def width(s, size, name, ls=0.0):
    _, _, cmap, hmtx, em = font(name)
    return sum(hmtx[cmap.get(ord(c), ".notdef")][0] * size / em + ls for c in s) - ls


def glyphs(s, x, y, size, name, ls=0.0):
    """One (path, x before, x after) per character that has ink or not."""
    _, gs, cmap, hmtx, em = font(name)
    k = size / em
    out = []
    for c in s:
        g = cmap.get(ord(c), ".notdef")
        pen = SVGPathPen(gs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
        gs[g].draw(TransformPen(pen, (k, 0, 0, -k, x, y)))
        nx = x + hmtx[g][0] * k + ls
        out.append((pen.getCommands(), x, nx))
        x = nx
    return out


def text(s, x, y, size, name="Inter-Regular", fill=FOG, anchor="start", ls=0.0, extra=""):
    if anchor != "start":
        x -= width(s, size, name, ls) * (0.5 if anchor == "middle" else 1)
    d = "".join(g[0] for g in glyphs(s, x, y, size, name, ls))
    return f'<path d="{d}" fill="{fill}" {extra}/>'


def icon(x, y, s):
    """The app's icon, s wide."""
    k = s / 100
    return (f'<g transform="translate({x} {y}) scale({k})"><rect x="3" y="3" width="94" height="94" rx="24" fill="#0b0b0b" '
            'stroke="#2c2c2c" stroke-width="3"/><rect x="31" y="14" width="38" height="72" rx="9" fill="none" stroke="#eee" '
            'stroke-width="4"/><circle cx="50" cy="23" r="2.6" fill="#eee"/><rect x="43" y="74" width="14" height="3.6" '
            'rx="1.8" fill="#eee"/></g>')


def svg(w, h, alt, style, body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
            f'aria-label="{alt}"><title>{alt}</title><style>{style}'
            '@media (prefers-reduced-motion: reduce){*{animation:none!important}}</style>'
            f'<defs><linearGradient id="ice" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#d8ecf8"/>'
            f'<stop offset="1" stop-color="#98c0ef"/></linearGradient>{defs}</defs>{body}</svg>\n')


def save(name, content):
    (HERE / name).write_text(content, encoding="utf-8")
    print(name, f"{len(content) // 1024} KiB")


BACKDROP = ('<radialGradient id="v" cx=".8" cy="0" r=".75"><stop offset="0" stop-color="#663af3" stop-opacity=".30"/>'
            '<stop offset="1" stop-color="#663af3" stop-opacity="0"/></radialGradient>'
            '<radialGradient id="t" cx="0" cy="1" r=".65"><stop offset="0" stop-color="#269684" stop-opacity=".20"/>'
            '<stop offset="1" stop-color="#269684" stop-opacity="0"/></radialGradient>')


def hero():
    W, H, SIDE, CYCLE = 860, 400, 180, 14
    line = "Hi. What are u search in my profile?"
    chars = glyphs(line, SIDE + 36, 212, 23, "Inter-Medium")
    step = 0.07
    typed, stops = "", [f"0%{{transform:translateX({chars[0][1]:.1f}px)}}"]
    for i, (d, _, nx) in enumerate(chars):
        if d:
            typed += f'<path class="ch" style="animation-delay:{0.6 + i * step:.2f}s" d="{d}" fill="{FROST}"/>'
        stops.append(f"{(0.6 + (i + 1) * step) / CYCLE * 100:.2f}%{{transform:translateX({nx:.1f}px)}}")
    stops.append(f"100%{{transform:translateX({chars[-1][2]:.1f}px)}}")
    items = ["Profile", "What I do", "Projects", "Stack", "Secrets"]
    side = "".join(text(n, 34, 124 + i * 42, 14, "Inter-Regular", MIST) for i, n in enumerate(items))
    pills = "".join(f"{p}%{{transform:translateY({i * 42}px)}}" for p, i in
                    ((0, 0), (16, 0), (20, 1), (36, 1), (40, 2), (56, 2), (60, 3), (76, 3), (80, 4), (96, 4), (100, 0)))
    style = (".ch{animation:ch %ds linear infinite both}@keyframes ch{0%%{opacity:0}.4%%{opacity:1}92%%{opacity:1}93%%,100%%{opacity:0}}"
             ".cur{animation:cur %ds step-end infinite}@keyframes cur{%s}"
             ".blink{animation:bl 1s step-end infinite}@keyframes bl{50%%{opacity:0}}"
             ".pill{animation:pill 20s ease-in-out infinite}@keyframes pill{%s}"
             ".toast{animation:toast %ds cubic-bezier(.2,.8,.2,1) infinite both}"
             "@keyframes toast{0%%,30%%{transform:translateX(340px)}35%%,78%%{transform:none}84%%,100%%{transform:translateX(340px)}}"
             ".dot{animation:dot 2s ease-in-out infinite}@keyframes dot{50%%{opacity:.25}}"
             ".knob{animation:knob %ds ease-in-out infinite}@keyframes knob{0%%,48%%{transform:none}52%%,96%%{transform:translateX(-18px)}100%%{transform:none}}"
             ".track{animation:track %ds step-end infinite}@keyframes track{50%%{fill:#2f343e}96%%{fill:%s}}"
             ".state{animation:state %ds step-end infinite}@keyframes state{50%%{opacity:0}96%%{opacity:1}}"
             ".off{animation:off %ds step-end infinite}@keyframes off{0%%{opacity:0}50%%{opacity:1}96%%{opacity:0}}"
             % (CYCLE, CYCLE, "".join(stops), pills, CYCLE, CYCLE, CYCLE, VIOLET, CYCLE, CYCLE))
    body = f'''<clipPath id="w"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="16"/></clipPath>
<g clip-path="url(#w)"><rect width="{W}" height="{H}" fill="{CANVAS}"/><rect width="{W}" height="{H}" fill="url(#v)"/><rect width="{W}" height="{H}" fill="url(#t)"/>
<path d="M0 50.5H{W}M{SIDE}.5 50V{H}" stroke="{EDGE}"/>
{text("NickiCat — profile", W / 2, 31, 14, "Inter-Medium", MIST, "middle")}
<circle cx="{W - 28}" cy="26" r="11" fill="#1a1f2d"/><path d="M{W - 32} 22l8 8m0-8l-8 8" stroke="{INK}" stroke-width="1.8" stroke-linecap="round"/>
{icon(18, 66, 22)}{text("NickiCat", 48, 83, 15, "Manrope-Medium", FROST)}
<rect class="pill" x="12" y="102" width="{SIDE - 24}" height="36" rx="9" fill="#141927"/>{side}
{text("v0.0.1", 18, H - 20, 11, "JetBrainsMono-Regular", FOG)}
<rect x="64" y="{H - 34}" width="34" height="19" rx="5" fill="#231a4d"/>{text("DEV", 81, H - 20, 10, "JetBrainsMono-Bold", "#b9a6ff", "middle")}
{text("GITHUB PROFILE", SIDE + 36, 92, 12, "JetBrainsMono-Regular", FOG, ls=2)}
{text("NickiCat", SIDE + 34, 168, 66, "Manrope-Medium", "url(#ice)", ls=-2)}
{typed}<g class="cur"><rect class="blink" x="2" y="194" width="2" height="24" fill="{FROST}"/></g>
<rect x="{SIDE + 36}" y="250" width="{W - SIDE - 72}" height="108" rx="14" fill="{CARD}" fill-opacity=".85" stroke="{EDGE}"/>
<circle class="dot" cx="{SIDE + 58}" cy="280" r="4.5" fill="{TEAL}"/>
{text("NickiCat", SIDE + 74, 285, 15, "Inter-Medium", INK)}
<g class="state">{text("online", W - 70, 285, 13, "Inter-Regular", TEAL, "end")}</g>
<g class="off">{text("touching grass", W - 70, 285, 13, "Inter-Regular", FOG, "end")}</g>
<path d="M{SIDE + 56} 304.5H{W - 56}" stroke="{EDGE}"/>
{text("Full mode (through debugging): clusters, pipelines, cats", SIDE + 56, 336, 13.5, "Inter-Regular", MIST)}
<rect class="track" x="{W - 104}" y="320" width="46" height="24" rx="12" fill="{VIOLET}"/><circle class="knob" cx="{W - 70}" cy="332" r="9.5" fill="{INK}"/>
<g class="toast"><rect x="{W - 318}" y="66" width="298" height="72" rx="13" fill="#10142a" stroke="#34405a"/>
{icon(W - 306, 80, 44)}{text("BMO", W - 250, 94, 13, "Inter-SemiBold", INK)}{text("now", W - 34, 94, 11, "Inter-Regular", FOG, "end")}
{text("Someone opened your profile!", W - 250, 115, 12.5, "Inter-Regular", MIST)}</g></g>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="16" fill="none" stroke="{TEAL}" stroke-width="1.5"/>'''
    save("hero.svg", svg(W, H, "NickiCat: an app window with the line: Hi. What are u search in my profile?", style, body, BACKDROP))


def nav():
    for name, label, primary in (("what", "What are u search?", True), ("about", "What I do", False), ("projects", "Projects", False),
                                 ("stack", "Stack", False), ("desk", "Desk", False)):
        w = round(width(label, 14, "Inter-Medium")) + 40
        fill, ink = (VIOLET, INK) if primary else ("#0d1120", FROST)
        stroke = "none" if primary else "#34405a"
        sweep = ('<linearGradient id="s" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                 '<stop offset=".5" stop-color="#fff" stop-opacity=".28"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
                 f'<clipPath id="c"><rect width="{w}" height="38" rx="19"/></clipPath>') if primary else ""
        shine = f'<g clip-path="url(#c)"><rect class="sh" x="-60" width="60" height="38" fill="url(#s)"/></g>' if primary else ""
        style = f".sh{{animation:sh 4s ease-in-out infinite}}@keyframes sh{{0%,55%{{transform:translateX(0)}}100%{{transform:translateX({w + 70}px)}}}}" if primary else ""
        body = (f'<rect x=".5" y=".5" width="{w - 1}" height="37" rx="18.5" fill="{fill}" stroke="{stroke}"/>{shine}'
                f'{text(label, w / 2, 24, 14, "Inter-Medium", ink, "middle")}')
        save(f"nav-{name}.svg", svg(w, 38, label, style, body, sweep))


def jpeg(im, q=74):
    buf = io.BytesIO()
    im.convert("RGB").save(buf, "JPEG", quality=q, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def phone():
    W, BAR, SW, SH = 280, 44, 264, 520
    pics = HERE.parent / "pictures"
    # The whole photo, its wall stretched up and down to the screen's shape.
    photo = Image.open(pics / "Calculator_on_sk8.jpg")
    photo = photo.resize((396, round(photo.height * 396 / photo.width)), Image.LANCZOS)
    gap = (780 - photo.height) // 2
    screen = Image.new("RGB", (396, 780))
    screen.paste(photo.crop((0, 0, 396, 12)).resize((396, gap + 1), Image.BICUBIC), (0, 0))
    screen.paste(photo.crop((0, photo.height - 12, 396, photo.height)).resize((396, 780 - gap - photo.height), Image.BICUBIC), (0, gap + photo.height))
    screen.paste(photo, (0, gap))
    rabbit = Image.open(pics / "Uuu_rabbit.jpg").crop((170, 0, 510, 669)).resize((396, 780), Image.LANCZOS)
    a, b, top = jpeg(screen), jpeg(rabbit), 8 + BAR
    h = SH + BAR + 16
    style = (f".feed{{animation:feed 10s infinite}}@keyframes feed{{0%,40%{{transform:translateY(0)}}"
             f"46%,90%{{transform:translateY(-{SH}px);animation-timing-function:cubic-bezier(.4,0,.2,1)}}96%,100%{{transform:translateY(-{2 * SH}px)}}}}"
             ".wh{animation:wh 10s infinite}@keyframes wh{0%,36%,50%,86%,100%{opacity:0}40%,46%,90%,96%{opacity:1}}"
             ".mk{animation:mk 1s linear infinite}@keyframes mk{from{transform:translateY(-3px)}to{transform:translateY(3px)}}")
    def page(ref, y, who, says):
        return (f'<use href="#{ref}" y="{y}"/><rect x="8" y="{y + SH - 66}" width="{SW}" height="66" fill="#000" fill-opacity=".45"/>'
                + text(who, 22, y + SH - 40, 13, "Inter-SemiBold", INK) + text(says, 22, y + SH - 20, 12, "Inter-Regular", "#e7ecf5"))
    x = 8
    defs = (f'<image id="a" x="{x}" width="{SW}" height="{SH}" preserveAspectRatio="xMidYMid slice" href="{a}"/>'
            f'<image id="b" x="{x}" width="{SW}" height="{SH}" preserveAspectRatio="xMidYMid slice" href="{b}"/>'
            f'<clipPath id="s"><rect x="{x}" y="{top}" width="{SW}" height="{SH}" rx="6"/></clipPath>')
    tb = [f'<path d="M24 {top - 28}l-6 6 6 6" fill="none" stroke="{FOG}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
          f'<path d="M42 {top - 21}l7-6 7 6v7h-14z" fill="none" stroke="{FOG}" stroke-width="1.6" stroke-linejoin="round"/>',
          text("my feed", W / 2 + 8, top - 18, 13, "Inter-Medium", MIST, "middle"),
          f'<circle cx="{W - 26}" cy="{top - 22}" r="9" fill="#1a1f2d"/><path d="M{W - 29} {top - 25}l6 6m0-6l-6 6" stroke="{INK}" stroke-width="1.5" stroke-linecap="round"/>']
    body = (f'<rect x="1" y="1" width="{W - 2}" height="{h - 2}" rx="15" fill="{CANVAS}" stroke="{TEAL}" stroke-width="1.5"/>{"".join(tb)}'
            f'<g clip-path="url(#s)"><g class="feed">{page("a", top, "@calculator_on_sk8", "Wheel down for the next one")}'
            f'{page("b", top + SH, "@uuu_rabbit", "What are u search here?")}{page("a", top + 2 * SH, "@calculator_on_sk8", "Wheel down for the next one")}</g></g>'
            f'<g class="wh"><rect x="{W - 58}" y="{top + 14}" width="36" height="52" rx="18" fill="#05060f" fill-opacity=".8" stroke="{MIST}"/>'
            f'<rect class="mk" x="{W - 42}" y="{top + 26}" width="4" height="12" rx="2" fill="{INK}"/></g>')
    save("phone.svg", svg(W, h, "A phone window: the mouse wheel flicks a feed between a calculator on a skateboard and a rabbit", style, body, defs))


def card():
    W, H = 860, 156
    style = (".dot{animation:dot 2s ease-in-out infinite}@keyframes dot{50%{opacity:.25}}"
             ".ar{animation:ar 1.6s ease-in-out infinite}@keyframes ar{50%{transform:translateX(4px)}}")
    body = f'''<clipPath id="w"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="16"/></clipPath>
<g clip-path="url(#w)"><rect width="{W}" height="{H}" fill="{CANVAS}"/><rect width="{W}" height="{H}" fill="url(#v)"/><rect width="{W}" height="{H}" fill="url(#t)"/></g>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="16" fill="none" stroke="#34405a"/>
{icon(28, 30, 96)}{text("SeamDroid", 150, 72, 40, "Manrope-Medium", "url(#ice)", ls=-1)}
{text("Android screen mirroring for Linux and Windows", 150, 101, 16, "Manrope-Medium", INK)}
{text("Screen · notifications · clipboard · audio · webcam", 150, 126, 13, "Inter-Regular", FOG)}
<rect x="{W - 150}" y="58" width="122" height="40" rx="20" fill="{VIOLET}"/>{text("Open", W - 112, 83, 14, "Inter-Medium", INK, "middle")}
<path class="ar" d="M{W - 82} 78h16m-6-6l6 6-6 6" fill="none" stroke="{INK}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'''
    save("card-seamdroid.svg", svg(W, H, "SeamDroid: Android screen mirroring for Linux and Windows. Open the site", style, body, BACKDROP))


def chips(file, alt, rows):
    W, pad, rowh = 860, 24, 48
    H = pad * 2 + rowh * len(rows) - 10
    body, n = [f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="16" fill="{CANVAS}" stroke="#34405a"/>'], 0
    style = ".c{animation:c 6s ease-in-out infinite both}@keyframes c{0%,12%,100%{stroke:#34405a}5%{stroke:#98c0ef}}"
    for r, (label, items) in enumerate(rows):
        y = pad + r * rowh
        body.append(text(label, pad + 4, y + 23, 11, "JetBrainsMono-Regular", FOG, ls=1.5))
        x = 150
        for item in items:
            w = width(item, 13, "Inter-Medium") + 26
            body.append(f'<rect class="c" style="animation-delay:{n * .35:.2f}s" x="{x}" y="{y}" width="{w:.0f}" height="36" rx="18" fill="#0d1120" stroke="#34405a"/>')
            body.append(text(item, x + 13, y + 23, 13, "Inter-Medium", FROST))
            x += w + 8
            n += 1
    save(file, svg(W, H, alt, style, "".join(body)))


hero()
nav()
phone()
card()
chips("stack.svg", "Stack: VMware vSphere, ESXi, Kubernetes, OpenShift, Talos, Ceph, Helm, GitLab CI, Docker, Harbor, Ansible, Puppet, Grafana, VictoriaMetrics, Vault, Rust, Python, TypeScript, Kotlin, Java, Bash", [
    ("PLATFORM", ["VMware vSphere", "ESXi", "Kubernetes", "OpenShift", "Talos", "Ceph"]),
    ("DELIVERY", ["Helm", "GitLab CI", "Docker", "Harbor", "Ansible", "Puppet"]),
    ("WATCHING", ["Grafana", "VictoriaMetrics", "Vault"]),
    ("CODE", ["Rust", "Python", "TypeScript", "Kotlin", "Java", "Bash"]),
])
chips("desk.svg", "Desk: CachyOS, Hyprland, Noctalia", [("DAILY", ["CachyOS", "Hyprland", "Noctalia"])])
