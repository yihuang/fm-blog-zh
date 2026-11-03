#!/usr/bin/env python3
"""Generate the figures for the abstract-interpretation article."""
import math, os, subprocess

W = 900
PAPER = "#FBF7F0"
PANEL = "#FFFCF7"
INK = "#23272E"
MUTED = "#7A7468"
LINE = "#D8CFBF"
BLUE = "#3D5A80"
BLUE_DARK = "#2C4257"
BLUE_LIGHT = "#A9BCD0"
SKY = "#E9F0F6"
RED = "#BF4A32"
RED_DARK = "#8E3324"
RED_LIGHT = "#EBC2B6"
GREEN = "#2F7D6B"
AMBER = "#D8A84E"
AMBER_LIGHT = "#F0DEBB"

SANS = "PingFang SC, Hiragino Sans GB, Noto Sans CJK SC, sans-serif"
SERIF = "Songti SC, STSong, Noto Serif CJK SC, serif"
MONO = "SFMono-Regular, Menlo, Consolas, monospace"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class SVG:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.parts, self.defs, self.nmark = [], [], 0

    def add(self, s):
        self.parts.append(s)

    def marker(self, color):
        key = "m%d" % self.nmark
        self.nmark += 1
        self.defs.append(
            f'<marker id="{key}" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{color}"/></marker>')
        return key

    def text(self, x, y, s, size=18, fill=INK, anchor="start", family=SANS,
             weight="normal", style="normal", spacing=0, opacity=1):
        if size < 14:
            size *= 1.15
        extra = ""
        if spacing:
            extra += f' letter-spacing="{spacing}"'
        if opacity != 1:
            extra += f' opacity="{opacity}"'
        if style != "normal":
            extra += f' font-style="{style}"'
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" '
                 f'font-size="{size}" font-weight="{weight}" fill="{fill}" '
                 f'text-anchor="{anchor}"{extra}>{esc(s)}</text>')

    def rect(self, x, y, w, h, rx=0, fill="none", stroke="none", sw=1,
             dash=None, opacity=1):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        o = f' opacity="{opacity}"' if opacity != 1 else ""
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                 f'rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}{o}/>')

    def circle(self, cx, cy, r, fill="none", stroke="none", sw=1, dash=None,
               opacity=1):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        o = f' opacity="{opacity}"' if opacity != 1 else ""
        self.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" '
                 f'stroke="{stroke}" stroke-width="{sw}"{d}{o}/>')

    def ellipse(self, cx, cy, rx, ry, fill="none", stroke="none", sw=1,
                dash=None, opacity=1):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        o = f' opacity="{opacity}"' if opacity != 1 else ""
        self.add(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" '
                 f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}{o}/>')

    def path(self, d, fill="none", stroke="none", sw=1, dash=None, opacity=1,
             cap="round", join="round"):
        da = f' stroke-dasharray="{dash}"' if dash else ""
        o = f' opacity="{opacity}"' if opacity != 1 else ""
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
                 f'stroke-linecap="{cap}" stroke-linejoin="{join}"{da}{o}/>')

    def arrow(self, p1, p2, curve=0, r1=0, r2=0, color=INK, sw=2, dash=None,
              opacity=1, head=True):
        (x1, y1), (x2, y2) = p1, p2
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        cx, cy = mx + nx * curve, my + ny * curve
        v1 = (cx - x1, cy - y1)
        l1 = math.hypot(*v1) or 1
        v2 = (x2 - cx, y2 - cy)
        l2 = math.hypot(*v2) or 1
        sx, sy = x1 + v1[0] / l1 * r1, y1 + v1[1] / l1 * r1
        ex, ey = x2 - v2[0] / l2 * r2, y2 - v2[1] / l2 * r2
        key = self.marker(color)
        da = f' stroke-dasharray="{dash}"' if dash else ""
        o = f' opacity="{opacity}"' if opacity != 1 else ""
        m = f' marker-end="url(#{key})"' if head else ""
        self.add(f'<path d="M {sx:.1f} {sy:.1f} Q {cx:.1f} {cy:.1f} {ex:.1f} {ey:.1f}" '
                 f'fill="none" stroke="{color}" stroke-width="{sw}" '
                 f'stroke-linecap="round"{da}{o}{m}/>')

    def line(self, p1, p2, color=INK, sw=2, dash=None, opacity=1):
        self.path(f"M {p1[0]:.1f} {p1[1]:.1f} L {p2[0]:.1f} {p2[1]:.1f}",
                  stroke=color, sw=sw, dash=dash, opacity=opacity)

    def poly(self, pts, color=INK, sw=2, dash=None, opacity=1, fill="none",
             close=False):
        d = f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"
        for p in pts[1:]:
            d += f" L {p[0]:.1f} {p[1]:.1f}"
        if close:
            d += " Z"
        self.path(d, fill=fill, stroke=color, sw=sw, dash=dash, opacity=opacity)

    def arc(self, x1, x2, y, h, color=INK, sw=2, dash=None, opacity=1,
            head=False):
        key = self.marker(color) if head else None
        d = (f"M {x1:.1f} {y:.1f} Q {(x1+x2)/2:.1f} {y-h:.1f} {x2:.1f} {y:.1f}")
        m = f' marker-end="url(#{key})"' if head else ""
        da = f' stroke-dasharray="{dash}"' if dash else ""
        o = f' opacity="{opacity}"' if opacity != 1 else ""
        self.add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" '
                 f'stroke-linecap="round"{da}{o}{m}/>')

    def render(self):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w*2}" '
                f'height="{self.h*2}" viewBox="0 0 {self.w} {self.h}" '
                f'text-rendering="geometricPrecision">'
                f'<defs>{"".join(self.defs)}</defs>'
                f'<rect width="{self.w}" height="{self.h}" fill="{PAPER}"/>'
                f'{"".join(self.parts)}</svg>')

    def save(self, name):
        os.makedirs("images/src", exist_ok=True)
        svg = self.render()
        with open(f"images/src/{name}.svg", "w", encoding="utf-8") as f:
            f.write(svg)
        subprocess.run(["magick", "-density", "192", f"images/src/{name}.svg",
                        "-resize", "1800x", "-strip", "-depth", "8",
                        "-dither", "None", "-colors", "256",
                        f"images/{name}.png"], check=True)
        print("wrote", name)


def kicker(s, txt):
    s.text(40, 38, txt, size=13, fill=MUTED, spacing=2.4, weight="600")


def title(s, t, sub=None):
    s.text(40, 82, t, size=30, fill=INK, weight="700")
    if sub:
        s.text(40, 114, sub, size=16.5, fill=MUTED)


def panel(s, x, y, w, h, stroke="#E8DFCF", fill=PANEL):
    s.rect(x, y, w, h, rx=16, fill=fill, stroke=stroke, sw=1.2)


def chip(s, x, y, w, h, txt, fill=PANEL, stroke=LINE, tcol=INK, size=15,
         weight="600", family=SANS, rx=10):
    s.rect(x, y, w, h, rx=rx, fill=fill, stroke=stroke, sw=1.4)
    s.text(x + w / 2, y + h / 2 + size * 0.36, txt, size=size, fill=tcol,
           anchor="middle", weight=weight, family=family)


# ------------------------------------------------------------------ 01
def fig_abstraction():
    s = SVG(W, 480)
    kicker(s, "01 · 从集合到元素")
    title(s, "一族状态，一个摘要", "α 往上，γ 往下；Σ ⊆ γ(α(Σ))")
    panel(s, 40, 150, 340, 250)
    panel(s, 520, 150, 340, 250)
    s.text(58, 178, "具体域 P(State)", size=13, fill=MUTED, weight="600")
    s.text(538, 178, "抽象域 A（一个格）", size=13, fill=MUTED, weight="600")

    # concrete blob = a set of states
    cx, cy = 210, 270
    pts = [(158, 296), (140, 262), (158, 232), (200, 220), (246, 230),
           (266, 262), (250, 298), (212, 310)]
    d = f"M {pts[0][0]} {pts[0][1]}"
    for p in pts[1:]:
        d += (f" C {(p[0]+pts[0][0])/2:.0f} {p[1]-8:.0f} "
              f"{p[0]} {p[1]} {p[0]} {p[1]}")
    s.path(d, fill=SKY, stroke=BLUE, sw=2.2)
    dots = [(174, 258), (226, 250), (240, 272), (228, 292), (200, 300),
            (172, 284), (252, 258), (160, 272)]
    for x, y in dots:
        s.circle(x, y, 3.2, fill=BLUE, stroke="none")
    s.text(212, 280, "Σ", size=18, fill=BLUE_DARK, anchor="middle", weight="700")

    # gamma(alpha(S)) dashed hull
    s.ellipse(cx, cy, 106, 88, stroke=BLUE, sw=1.8, dash="7 6", opacity=0.8)
    s.text(58, 380, "Σ = 可达状态集合；虚线 = γ(α(Σ))", size=12, fill=MUTED)

    # abstract element: number line with interval
    y = 268
    s.line((536, y), (844, y), color=LINE, sw=2)
    for k in range(0, 10):
        x = 536 + k * 34.2
        s.line((x, y - 5), (x, y + 5), color=MUTED, sw=1.4)
        s.text(x, y + 26, str(k), size=11, fill=MUTED, anchor="middle", family=MONO)
    a, b = 536 + 3 * 34.2, 536 + 6 * 34.2
    s.line((a, y), (b, y), color=RED, sw=8, opacity=0.85)
    s.line((a, y - 12), (a, y + 12), color=RED, sw=2.4)
    s.line((b, y - 12), (b, y + 12), color=RED, sw=2.4)
    s.text((a + b) / 2, y - 26, "a = [3, 6]", size=13.5, fill=RED, anchor="middle",
           weight="600", family=MONO)
    s.text(690, y + 64, "一个元素，代表一族状态", size=12.5, fill=MUTED, anchor="middle")

    # arrows
    s.arrow((382, 218), (518, 218), curve=-24, color=BLUE, sw=2.2)
    s.text(450, 200, "α", size=22, fill=BLUE, anchor="middle", weight="700")
    s.arrow((518, 336), (382, 336), curve=24, color=MUTED, sw=1.8, dash="6 5")
    s.text(450, 382, "γ", size=22, fill=MUTED, anchor="middle", weight="700")

    s.text(40, 444, "抽象只能变大：Σ ⊆ γ(α(Σ))。α 取最小上界，γ 把抽象元素解释回具体集合。",
           size=14.5, fill=INK)
    s.save("ai-01-abstraction")


# ------------------------------------------------------------------ 02
def fig_square():
    s = SVG(W, 540)
    kicker(s, "02 · 健全性")
    title(s, "局部健全，全局健全", "每条语句都盖住，整个程序就盖住")

    s.text(205, 160, "具体：状态集合", size=12, fill=MUTED, anchor="middle")
    s.text(675, 160, "抽象：摘要", size=12, fill=MUTED, anchor="middle")
    chip(s, 110, 180, 190, 52, "Σ", fill=SKY, stroke=BLUE, tcol=BLUE_DARK,
         size=19, family=MONO)
    chip(s, 110, 340, 190, 52, "f(Σ)", fill=SKY, stroke=BLUE, tcol=BLUE_DARK,
         size=19, family=MONO)
    chip(s, 560, 180, 230, 52, "α(Σ)", fill=PANEL, stroke=RED, tcol=RED,
         size=19, family=MONO)
    chip(s, 560, 340, 230, 52, "f#(α(Σ))", fill=PANEL, stroke=RED, tcol=RED,
         size=19, family=MONO)

    s.arrow((205, 232), (205, 338), color=BLUE, sw=2, r2=4)
    s.text(186, 292, "f", size=20, fill=BLUE, anchor="end", weight="700", family=MONO)
    s.arrow((675, 232), (675, 338), color=RED, sw=2, r2=4)
    s.text(694, 292, "f#", size=20, fill=RED, weight="700", family=MONO)

    s.arrow((302, 206), (556, 206), color=BLUE, sw=1.8, r1=4)
    s.text(430, 194, "α", size=19, fill=BLUE, anchor="middle", weight="700")
    s.arrow((302, 368), (556, 368), color=BLUE, sw=1.8, r1=4)
    s.text(430, 356, "α", size=19, fill=BLUE, anchor="middle", weight="700")

    s.rect(40, 414, 820, 104, rx=14, fill="#F6F1E7", stroke="#E4D9C6", sw=1.2)
    s.text(60, 442, "从局部到全局", size=13, fill=MUTED, weight="700", spacing=2)
    s.text(60, 470, "局部健全：α(f(Σ)) ⊑ f#(α(Σ))，每条语句的抽象转移都盖住具体转移。",
           size=14.5, fill=GREEN)
    s.text(60, 498, "归纳：若 Σ_n ⊆ γ(a_n)，则 f(Σ_n) ⊆ γ(f#(a_n))；取并之后，仍然覆盖。",
           size=14.5, fill=INK)
    s.save("ai-02-square")


# ------------------------------------------------------------------ 03
def fig_lattices():
    s = SVG(W, 600)
    kicker(s, "03 · 两个格")
    title(s, "有限高度与无限高度", "终止性不是幸运，是格的形状")

    # left: sign lattice
    s.rect(40, 148, 400, 410, rx=14, fill=PANEL, stroke="#E8DFCF", sw=1.2)
    s.text(60, 176, "符号域：高度 3", size=14, fill=INK, weight="700")
    nodes = {
        "⊤": (240, 212), "≤0": (150, 298), "≠0": (240, 298), "≥0": (330, 298),
        "-": (150, 390), "0": (240, 390), "+": (330, 390), "⊥": (240, 490),
    }
    edges = [("⊥", "-"), ("⊥", "0"), ("⊥", "+"), ("-", "≤0"), ("0", "≤0"),
             ("0", "≥0"), ("+", "≥0"), ("-", "≠0"), ("+", "≠0"),
             ("≤0", "⊤"), ("≠0", "⊤"), ("≥0", "⊤")]
    for a, b in edges:
        s.line(nodes[a], nodes[b], color=LINE, sw=1.6)
    for name, (x, y) in nodes.items():
        s.circle(x, y, 24, fill=PAPER, stroke=BLUE, sw=1.8)
        s.text(x, y + 6, name, size=16 if name in "⊤⊥" else 13.5,
               fill=BLUE_DARK, anchor="middle", weight="600", family=MONO)
    s.text(60, 540, "任一上升链最多 4 个元素。迭代必然停。", size=12.5, fill=MUTED)

    # right: interval chain
    s.rect(460, 148, 400, 410, rx=14, fill=PANEL, stroke="#E8DFCF", sw=1.2)
    s.text(480, 176, "区间域：高度 ∞", size=14, fill=INK, weight="700")
    x0, scale = 560, 44
    rows = [(474, 0), (438, 1), (402, 2), (366, 3), (330, 4)]
    for y, k in rows:
        s.line((x0, y), (x0 + k * scale, y), color=BLUE, sw=7, opacity=0.85)
        s.line((x0 + k * scale, y - 9), (x0 + k * scale, y + 9), color=BLUE, sw=2)
        s.text(x0 - 14, y + 5, f"[0,{k}]", size=11.5, fill=MUTED, anchor="end",
               family=MONO)
    s.text(760, 292, "…", size=22, fill=MUTED, anchor="middle")
    s.line((x0, 258), (x0 + 276, 258), color=RED, sw=7, opacity=0.8)
    s.line((x0, 249), (x0, 267), color=RED, sw=2)
    s.text(700, 240, "[0, +∞]", size=12, fill=RED, anchor="middle", family=MONO)
    s.text(480, 506, "每轮多 1，永远不会停：", size=12.5, fill=MUTED)
    s.text(480, 528, "真实分析器必须换一条上升链。", size=12.5, fill=MUTED)
    s.save("ai-03-lattices")


# ------------------------------------------------------------------ 04
def fig_precision():
    s = SVG(W, 500)
    kicker(s, "05 · 精度")
    title(s, "精度从哪里漏掉", "合并丢相关性，域丢形状，widening 丢上界")
    panel(s, 40, 140, 380, 280)
    panel(s, 480, 140, 380, 280)
    s.text(58, 168, "① 路径合并", size=13, fill=MUTED, weight="600")
    s.text(498, 168, "② 相关性", size=13, fill=MUTED, weight="600")

    chip(s, 70, 200, 96, 44, "x = 1", fill=SKY, stroke=BLUE, tcol=BLUE_DARK,
         size=14, family=MONO)
    chip(s, 70, 292, 96, 44, "x = 2", fill=SKY, stroke=BLUE, tcol=BLUE_DARK,
         size=14, family=MONO)
    chip(s, 286, 246, 116, 44, "x ∈ [1,2]", fill=PANEL, stroke=RED, tcol=RED,
         size=13, family=MONO)
    s.arrow((170, 222), (282, 254), curve=-14, color=MUTED, sw=1.6, r2=4)
    s.arrow((170, 314), (282, 282), curve=14, color=MUTED, sw=1.6, r2=4)
    s.text(250, 228, "⊔ 合并", size=13, fill=RED)
    s.text(70, 372, "两个分支都到这里；摘要只记得“1 或 2”的外壳。", size=12.5, fill=MUTED)

    # correlation panel
    ox, oy, u = 540, 380, 68
    s.line((ox - 6, oy), (ox + 2 * u + 26, oy), color=MUTED, sw=1.4)
    s.arrow((ox + 2 * u + 26, oy), (ox + 2 * u + 38, oy), color=MUTED, sw=1.4)
    s.line((ox, oy + 6), (ox, oy - 2 * u - 26), color=MUTED, sw=1.4)
    s.arrow((ox, oy - 2 * u - 26), (ox, oy - 2 * u - 38), color=MUTED, sw=1.4)
    s.text(ox + 2 * u + 30, oy + 22, "x", size=12, fill=MUTED, anchor="middle")
    s.text(ox - 16, oy - 2 * u - 30, "y", size=12, fill=MUTED, anchor="middle")
    s.rect(ox, oy - 2 * u, 2 * u, 2 * u, fill="#F7E7E2", stroke=RED, sw=1.4,
           dash="5 5")
    for k in range(3):
        s.circle(ox + k * u, oy - k * u, 4.6, fill=BLUE, stroke="none")
    s.text(ox + u + 14, oy - u - 8, "x = y", size=12.5, fill=BLUE, family=MONO)
    s.circle(ox, oy - 2 * u, 7, fill="none", stroke=RED, sw=2)
    s.text(ox + 16, oy - 2 * u - 14, "不可达，但盒子以为可能", size=12, fill=RED)
    s.text(498, 404, "盒子记住了 x、y 各自的区间，却没记住它们一起变。", size=12.5, fill=MUTED)

    s.text(40, 462, "每次 join 都在回答：“这两个状态有什么共同的上界？”答案总是比真相更宽。",
           size=14.5, fill=INK)
    s.save("ai-05-precision")


# ------------------------------------------------------------------ 05
def fig_widening():
    s = SVG(W, 560)
    kicker(s, "04 · 加速")
    title(s, "widening：把上升链剪断", "先猜一个上界，再回来验证")
    x0, u = 220, 48
    rows = [(186, 0), (230, 1), (274, 2), (318, 3)]
    for y, k in rows:
        s.line((x0, y), (x0 + k * u, y), color=BLUE, sw=8, opacity=0.85)
        s.line((x0 + k * u, y - 10), (x0 + k * u, y + 10), color=BLUE, sw=2)
        s.text(200, y + 5, f"[0,{k}]", size=12, fill=MUTED, anchor="end", family=MONO)
        s.text(60, y + 5, f"第 {k} 轮", size=12.5, fill=MUTED)
    s.line((x0 + 3 * u, 326), (x0 + 3 * u, 396), color=RED, sw=1.6, dash="5 5")
    s.text(x0 + 3 * u + 14, 368, "∇", size=22, fill=RED, weight="700")

    y = 404
    s.line((x0, y), (800, y), color=RED, sw=8, opacity=0.85)
    s.text(x0, y + 26, "第 4 轮：∇ 直接跳到 +∞", size=13, fill=RED, weight="600")
    s.text(600, y + 26, "2 步收敛，上界却没了", size=12, fill=MUTED)

    y = 486
    s.line((x0, y), (x0 + 10 * u, y), color=GREEN, sw=8, opacity=0.85)
    s.line((x0 + 10 * u, y - 10), (x0 + 10 * u, y + 10), color=GREEN, sw=2)
    s.text(x0, y - 16, "阈值 / narrowing：[0, 10]", size=13, fill=GREEN, weight="600")
    s.text(560, y + 26, "用程序里的常量把上界捡回来", size=12, fill=MUTED)
    s.save("ai-04-widening")


# ------------------------------------------------------------------ 06
def fig_pipeline():
    s = SVG(W, 480)
    kicker(s, "06 · 工程")
    title(s, "分析器长什么样", "语义、摘要、不动点，各管一段")

    boxes = [
        (40, 150, "源码 / IR", "前端"),
        (210, 130, "CFG", ""),
        (360, 160, "转移函数 f#", "语义"),
        (540, 140, "不动点引擎", "迭代"),
        (700, 160, "报警 / 优化事实", "结论"),
    ]
    for x, w, txt, _ in boxes:
        chip(s, x, 200, w, 64, txt, fill=PANEL, stroke=BLUE, tcol=BLUE_DARK,
             size=14.5)
    for (x1, w1, _, _), (x2, _, _, _) in zip(boxes, boxes[1:]):
        s.arrow((x1 + w1 + 2, 232), (x2 - 4, 232), color=BLUE, sw=1.8)

    for x, w, _, tag in boxes:
        if tag:
            s.text(x + w / 2, 186, tag, size=11, fill=MUTED, anchor="middle", spacing=1.5)

    chip(s, 380, 320, 160, 54, "抽象域 A", fill="#F6F1E7", stroke=RED, tcol=RED,
         size=14.5, family=MONO)
    s.arrow((430, 318), (430, 268), color=RED, sw=1.6, dash="5 5")
    s.arrow((490, 318), (560, 268), color=RED, sw=1.6, dash="5 5")
    s.text(440, 300, "格与 join", size=11, fill=MUTED)

    s.path("M 780 268 L 780 430 L 460 430", stroke=MUTED, sw=1.5, dash="6 5")
    s.arrow((460, 430), (460, 378), color=MUTED, sw=1.5, dash="6 5")
    s.text(620, 418, "误报太多？调域 / 调阈值 / 加窄化", size=11.5, fill=MUTED,
           anchor="middle")

    s.text(40, 462, "转移函数只对“一条语句”负责；不动点负责把它推广到“所有路径、所有轮次”。",
           size=14, fill=INK)
    s.save("ai-06-pipeline")


# ------------------------------------------------------------------ 07
def fig_domains():
    s = SVG(W, 530)
    kicker(s, "07 · 选择")
    title(s, "精度是形状问题", "状态集合长什么样，决定哪个域够用")

    panels = [
        (40, "区间", "轴对齐的盒子", "成本：低"),
        (250, "八边形", "±x ±y ≤ c", "成本：中"),
        (460, "多面体", "任意线性不等式", "成本：高"),
        (670, "路径敏感", "有限个盒子的并", "成本：随路径数"),
    ]
    for x, name, note, cost in panels:
        s.rect(x, 150, 190, 280, rx=14, fill=PANEL, stroke="#E8DFCF", sw=1.2)
        s.text(x + 16, 178, name, size=14.5, fill=INK, weight="700")
        s.text(x + 16, 200, note, size=11.5, fill=MUTED, family=MONO)
        s.text(x + 16, 402, cost, size=11.5, fill=MUTED)
        # mini plot frame
        s.line((x + 30, 330), (x + 170, 330), color=LINE, sw=1.2)
        s.line((x + 30, 330), (x + 30, 230), color=LINE, sw=1.2)

    # interval box
    s.rect(60, 250, 100, 60, fill=SKY, stroke=BLUE, sw=1.8)
    s.circle(80, 300, 3, fill=BLUE); s.circle(120, 280, 3, fill=BLUE)
    s.circle(150, 262, 3, fill=BLUE)

    # octagon
    cx, cy, r = 345, 290, 52
    pts = [(cx + r * math.cos(a), cy + r * math.sin(a))
           for a in [math.pi / 8 + k * math.pi / 4 for k in range(8)]]
    s.poly(pts, color=BLUE, sw=1.8, fill=SKY, close=True)
    s.circle(325, 310, 3, fill=BLUE); s.circle(350, 300, 3, fill=BLUE)
    s.circle(365, 282, 3, fill=BLUE)

    # polyhedron
    s.poly([(500, 320), (590, 320), (620, 250)], color=BLUE, sw=1.8, fill=SKY,
           close=True)
    s.circle(530, 305, 3, fill=BLUE); s.circle(565, 295, 3, fill=BLUE)
    s.circle(590, 280, 3, fill=BLUE)

    # path sensitive: two boxes
    s.rect(700, 250, 60, 60, fill=SKY, stroke=BLUE, sw=1.6)
    s.rect(790, 270, 50, 60, fill=SKY, stroke=BLUE, sw=1.6)
    s.circle(720, 300, 3, fill=BLUE); s.circle(815, 290, 3, fill=BLUE)

    s.text(40, 470, "区间只能画一个盒子；八边形能把角切掉；多面体更贴合；路径敏感干脆画两个盒子。",
           size=14, fill=INK)
    s.text(40, 496, "每多一种形状，转移函数就多一份工作量——这就是精度的价格。",
           size=13, fill=MUTED)
    s.save("ai-07-domains")


# ------------------------------------------------------------------ cover
def cover():
    s = SVG(W, 500)
    s.text(60, 54, "形式化笔记 · 程序分析", size=13, fill=BLUE, spacing=2.6, weight="700")
    s.text(60, 168, "抽象解释", size=64, fill=INK, weight="700")
    s.text(60, 238, "把无限装进格子", size=42, fill=INK, weight="700")
    s.line((60, 266), (330, 266), color=BLUE, sw=3)
    s.text(60, 302, "具体是集合，摘要是元素", size=17, fill=MUTED)
    s.text(60, 330, "健全性只向上，不向下", size=17, fill=MUTED)
    s.text(60, 358, "widening 换终止，narrowing 换精度", size=17, fill=MUTED)
    s.text(60, 436, "从 Galois 连接、抽象域到 widening", size=13, fill=MUTED)
    s.text(60, 462, "附一个一百多行、可运行的区间分析器", size=12.5, fill=MUTED)

    # right: states -> one abstract element
    s.rect(590, 90, 270, 340, rx=18, fill=PANEL, stroke="#E8DFCF", sw=1.2)
    s.text(725, 120, "所有运行", size=12, fill=MUTED, anchor="middle")
    dots = [(650, 178), (682, 160), (716, 172), (748, 152), (780, 176),
            (806, 200), (770, 212), (730, 200), (694, 204), (660, 200)]
    for x, y in dots:
        s.circle(x, y, 4, fill=BLUE, stroke="none")
    s.ellipse(730, 184, 94, 44, stroke=BLUE, sw=1.4, dash="6 5")

    s.arrow((725, 240), (725, 292), color=BLUE, sw=1.8)
    s.text(740, 268, "α", size=18, fill=BLUE, weight="700")

    y = 330
    s.line((635, y), (815, y), color=LINE, sw=1.8)
    for k in range(5):
        xx = 635 + k * 45
        s.line((xx, y - 4), (xx, y + 4), color=MUTED, sw=1.2)
    s.line((680, y), (770, y), color=RED, sw=7, opacity=0.85)
    s.line((680, y - 10), (680, y + 10), color=RED, sw=2)
    s.line((770, y - 10), (770, y + 10), color=RED, sw=2)
    s.text(725, y - 18, "a = [1, 3]", size=12.5, fill=RED, anchor="middle",
           weight="600", family=MONO)
    s.text(725, 386, "一个格元素", size=12, fill=MUTED, anchor="middle")
    s.save("ai-cover")


if __name__ == "__main__":
    fig_abstraction()
    fig_square()
    fig_lattices()
    fig_widening()
    fig_precision()
    fig_pipeline()
    fig_domains()
    cover()
