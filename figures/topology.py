#!/usr/bin/env python3
"""Generate the figures for the topology article."""
import math, os, subprocess

W = 900
PAPER = "#FBF7F0"
PANEL = "#FFFCF7"
INK = "#23272E"
MUTED = "#7A7468"
LINE = "#D8CFBF"
RED = "#BF4A32"
RED_DARK = "#8E3324"
GREEN = "#2F7D6B"
GREEN_LIGHT = "#7FB3A4"
AMBER = "#D8A84E"
ORANGE = "#D9825B"
BLUE = "#5B7083"
BLUE_LIGHT = "#9FB0BE"

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

    def poly(self, pts, color=INK, sw=2, dash=None, opacity=1, fill="none"):
        d = f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"
        for p in pts[1:]:
            d += f" L {p[0]:.1f} {p[1]:.1f}"
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
    s.text(40, 78, t, size=32, fill=INK, weight="700")
    if sub:
        s.text(40, 110, sub, size=17.5, fill=MUTED)


def panel(s, x, y, w, h, stroke="#E8DFCF", fill=PANEL):
    s.rect(x, y, w, h, rx=16, fill=fill, stroke=stroke, sw=1.2)


def smooth_closed(pts):
    n = len(pts)
    d = f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in range(n):
        p0 = pts[(i - 1) % n]; p1 = pts[i]; p2 = pts[(i + 1) % n]; p3 = pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += (f" C {c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} "
              f"{p2[0]:.1f} {p2[1]:.1f}")
    return d + " Z"


def blob_pts(cx, cy, rx, ry, wob=0.0, seed=1, n=9):
    rnd = (math.sin(seed * 12.9898) * 43758.5453) % 1
    out = []
    for i in range(n):
        t = 2 * math.pi * i / n - math.pi / 2
        w = 1 + wob * math.sin(3 * t + seed + rnd * 6)
        out.append((cx + rx * w * math.cos(t), cy + ry * w * math.sin(t)))
    return out


def blob(s, cx, cy, rx, ry, fill="none", stroke=INK, sw=2, wob=0.06, seed=1,
         dash=None, opacity=1, n=9):
    pts = blob_pts(cx, cy, rx, ry, wob, seed, n)
    s.path(smooth_closed(pts), fill=fill, stroke=stroke, sw=sw, dash=dash,
           opacity=opacity)
    return pts


def torus(s, cx, cy, R, r, color=INK, fill_a="#F0E7D6"):
    s.ellipse(cx, cy, R + r, (R + r) * 0.42, fill=fill_a, stroke=color, sw=2.2)
    s.ellipse(cx, cy - r * 0.10, R - r, (R - r) * 0.42, fill=PAPER, stroke=color, sw=2.2)
    # inner shadow at the bottom of the hole
    s.path(f"M {cx-(R-r):.1f} {cy-r*0.10:.1f} "
           f"A {R-r:.1f} {(R-r)*0.42:.1f} 0 0 0 {cx+(R-r):.1f} {cy-r*0.10:.1f}",
           stroke=color, sw=3.2, opacity=0.14)
    # highlight on the upper-left rim
    s.path(f"M {cx-(R+r)*0.86:.1f} {cy-(R+r)*0.16:.1f} "
           f"A {R+r:.1f} {(R+r)*0.42:.1f} 0 0 1 {cx-(R+r)*0.18:.1f} {cy-(R+r)*0.40:.1f}",
           stroke="#FFFFFF", sw=3, opacity=0.65)


# ------------------------------------------------------------------ figure 1
def fig_tree():
    h = 660
    s = SVG(W, h)
    kicker(s, "图 1 / OPEN SETS AS OBSERVATIONS")
    title(s, "开集：一次有限观察就能确认的性质",
          "空间 = 所有无限 0/1 序列；一次观察 = 一个有限前缀")

    depth = 4
    top, bottom = 166, 506
    leaves = 2 ** depth
    x0, x1 = 84, 816
    pos = {}

    def node_xy(p):
        d = len(p)
        span = 2 ** (depth - d)
        idx = int(p, 2) if p else 0
        xs = x0 + (x1 - x0) * (idx + 0.5) * span / leaves
        ys = top + (bottom - top) * d / depth
        return (xs, ys)

    for d in range(depth + 1):
        for i in range(2 ** d):
            p = format(i, "0%db" % d) if d else ""
            pos[p] = node_xy(p)

    hl = ["00", "010", "110"]
    for p in hl:
        x, y = pos[p]
        span = 2 ** (depth - len(p))
        idx = int(p, 2)
        lx = x0 + (x1 - x0) * (idx * span) / leaves
        rx = x0 + (x1 - x0) * ((idx + 1) * span) / leaves
        s.rect(lx + 3, y - 12, rx - lx - 6, bottom + 20 - (y - 12), rx=10,
               fill=GREEN, opacity=0.07)
        s.rect(lx + 3, y - 12, rx - lx - 6, bottom + 20 - (y - 12), rx=10,
               stroke=GREEN, sw=1.2, dash="5 6", opacity=0.45)

    def in_subtree(child, root):
        return child.startswith(root)

    for d in range(depth):
        for i in range(2 ** d):
            p = format(i, "0%db" % d) if d else ""
            for b in "01":
                c = p + b
                hot = any(in_subtree(c, q) for q in hl)
                s.line(pos[p], pos[c], color=GREEN_LIGHT if hot else LINE,
                       sw=2.0 if hot else 1.5)

    seq = ["", "0", "01", "010", "0100"]
    s.poly([pos[p] for p in seq], color=RED, sw=3.2)

    for d in range(depth + 1):
        for i in range(2 ** d):
            p = format(i, "0%db" % d) if d else ""
            x, y = pos[p]
            hot = any(in_subtree(p, q) for q in hl)
            r = {0: 15, 1: 14, 2: 13.5, 3: 13, 4: 7.5}[d]
            if p in hl:
                s.circle(x, y, r + 3.5, fill=GREEN, stroke=GREEN)
                s.circle(x, y, r, fill=PAPER, stroke=GREEN, sw=1.8)
            else:
                s.circle(x, y, r, fill=PAPER,
                         stroke=GREEN if hot else LINE, sw=1.6 if hot else 1.2)
            if d <= 3:
                s.text(x, y + 3.6, p if p else "ε", size=10,
                       fill=GREEN if hot else MUTED, anchor="middle", family=MONO)


    x, y = pos["0100"]
    s.arrow((x + 10, y + 4), (x + 58, y + 34), color=RED, sw=1.5, curve=-6)
    s.text(x + 62, y + 42, "x = 0100…", size=15, fill=RED, family=MONO, weight="600")

    s.text(84, 572, "开集 U = [00] ∪ [010] ∪ [110]", size=17, fill=GREEN,
           family=MONO, weight="600")
    s.text(84, 600, "每个 [s] = “所有以 s 开头的序列”，也就是一次有限观察能确认的全部。", size=14, fill=INK)
    s.text(84, 626, "x 落在 U 里，只因为看了 3 位 —— 不需要看完整个无限序列。", size=14, fill=MUTED)
    s.save("topo-01-tree")


# ------------------------------------------------------------------ figure 2
def fig_lattice():
    h = 540
    s = SVG(W, h)
    kicker(s, "图 3 / THE LATTICE OF OPENS")
    title(s, "开集的格：真值不止两个",
          "同一个空间的开集按包含排成格；否定是否等于补集，决定了逻辑是不是布尔的")

    panel(s, 40, 140, 390, 320)
    s.text(64, 172, "Sierpiński 空间", size=16, fill=GREEN, weight="700")
    s.text(64, 194, "开集：∅、{1}、{0,1}", size=12.5, fill=MUTED)

    cx = 200
    ys = [240, 330, 420]
    labels = ["X", "P", "∅"]
    for i, (y, lab) in enumerate(zip(ys, labels)):
        if i < 2:
            s.line((cx, y + 30), (cx, ys[i + 1] - 30), color=INK, sw=2)
        s.circle(cx, y, 29, fill=PAPER, stroke=INK, sw=2)
        s.text(cx, y + 5, lab, size=14, fill=INK, anchor="middle", family=MONO, weight="600")
    s.text(cx + 46, 246, "= {0,1}", size=12, fill=MUTED, family=MONO)
    s.text(cx + 46, 336, "= {1}", size=12, fill=MUTED, family=MONO)



    panel(s, 470, 140, 390, 320)
    s.text(494, 172, "两点离散空间", size=16, fill=BLUE, weight="700")
    s.text(494, 194, "开集：∅、{a}、{b}、{a,b}", size=12.5, fill=MUTED)

    top = (665, 240)
    left = (590, 335)
    right = (740, 335)
    bot = (665, 420)
    def link(a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = (dx * dx + dy * dy) ** 0.5
        ux, uy = dx / L, dy / L
        s.line((a[0] + ux * 29, a[1] + uy * 29),
               (b[0] - ux * 29, b[1] - uy * 29), color=INK, sw=2)
    link(bot, left); link(bot, right); link(left, top); link(right, top)
    for (x, y), lab in [((665, 240), "X"), ((590, 335), "{a}"),
                        ((740, 335), "{b}"), ((665, 420), "∅")]:
        s.circle(x, y, 29, fill=PAPER, stroke=INK, sw=2)
        s.text(x, y + 5, lab, size=13, fill=INK, anchor="middle", family=MONO, weight="600")



    s.text(40, 502, "左边不是布尔代数：P 既不是 ⊥ 也不是 ⊤，¬P = ⊥，¬¬P = ⊤。", size=13.5, fill=INK)
    s.text(40, 526, "右边是：每个元素都有补集。开集的逻辑一般更接近左边 —— 边界就是那个“说不清”的中间值。",
           size=13.5, fill=MUTED)
    s.save("topo-02-frame")


# ------------------------------------------------------------------ figure 3
def fig_system():
    h = 580
    s = SVG(W, h)
    kicker(s, "图 4 / TOPOLOGICAL SYSTEMS")
    title(s, "拓扑系统：理论、模型、外延",
          "一个点，就是对所有观察的一个尊重逻辑的真值分配")

    # matrix
    x0, y0, cw, ch = 110, 230, 90, 58
    cols = ["U", "V", "W"]
    rows = ["x₁", "x₂", "x₃"]
    marks = [[1, 1, 0], [1, 0, 1], [0, 0, 1]]
    for j, c in enumerate(cols):
        s.text(x0 + j * cw + cw / 2, y0 - 18, c, size=16, fill=INK,
               anchor="middle", family=MONO, weight="600")
    for i, r in enumerate(rows):
        s.text(x0 - 22, y0 + i * ch + ch / 2 + 5, r, size=16, fill=INK,
               anchor="end", family=MONO, weight="600")
        for j in range(3):
            cx = x0 + j * cw + cw / 2
            cy = y0 + i * ch + ch / 2
            s.rect(x0 + j * cw, y0 + i * ch, cw, ch, fill=PANEL, stroke=LINE, sw=1)
            if marks[i][j]:
                s.circle(cx, cy, 7, fill=GREEN, stroke=GREEN)
            else:
                s.circle(cx, cy, 7, fill=PAPER, stroke=MUTED, sw=1.2)
    s.text(110, 452, "x ⊩ U：每一行是一个模型（点），每一列是一个观察（开集）。",
           size=12.5, fill=MUTED)
    s.text(110, 476, "第三行只满足 W：这个点区分开了 W 与 U、V。", size=12.5, fill=MUTED)

    # duality diagram
    s.rect(560, 180, 260, 66, rx=10, fill=PANEL, stroke=INK, sw=1.6)
    s.text(690, 206, "frame Ω", size=17, fill=INK, anchor="middle", weight="700",
           family=MONO)
    s.text(690, 230, "观察 / 理论", size=12.5, fill=MUTED, anchor="middle")

    s.rect(560, 360, 260, 66, rx=10, fill=PANEL, stroke=INK, sw=1.6)
    s.text(690, 386, "点集 pt(Ω)", size=17, fill=INK, anchor="middle", weight="700",
           family=MONO)
    s.text(690, 410, "模型 / 实现", size=12.5, fill=MUTED, anchor="middle")

    s.arrow((620, 252), (620, 352), color=GREEN, sw=2)
    s.text(608, 306, "ext", size=13, fill=GREEN, anchor="end", family=MONO)

    s.text(690, 470, "ext(U) = {x : x ⊩ U}，点 = frame hom Ω → 2", size=11.5,
           fill=MUTED, anchor="middle")

    s.text(40, 540, "连续映射 f : X → Y 对应 frame hom f* : ΩY → ΩX —— 逻辑的方向和点的方向相反。",
           size=13, fill=MUTED)
    s.save("topo-03-system")


# ------------------------------------------------------------------ figure 4
def fig_interior():
    h = 560
    s = SVG(W, h)
    kicker(s, "图 2 / INTERIOR, FRONTIER, EXTERIOR")
    title(s, "三种点：已确认、说不清、已否定",
          "内部、边界、外部 —— 看它有没有一个“整个落在里面”的开邻域")

    s.ellipse(300, 340, 196, 146, fill=GREEN, stroke=GREEN, sw=2, opacity=0.07)
    s.ellipse(300, 340, 196, 146, stroke=GREEN, sw=2.2)
    s.text(300, 268, "S", size=32, fill=GREEN, anchor="middle", weight="700", family=SERIF)

    def mark(x, y, color, label, dx=32, dy=6, anchor="start"):
        s.circle(x, y, 34, fill="none", stroke=color, sw=1.2, dash="4 5")
        s.circle(x, y, 7, fill=color, stroke=PAPER, sw=1.6)
        s.text(x + dx, y + dy, label, size=15, fill=color, weight="600", anchor=anchor)

    mark(232, 312, GREEN, "已确认", dx=44)
    bx, by = 300 + 196 * math.cos(0.55), 340 + 146 * math.sin(0.55)
    mark(bx, by, AMBER, "说不清", dx=0, dy=58, anchor="middle")
    s.text(bx, by + 82, "点在边界上", size=12, fill=MUTED, anchor="middle")
    mark(548, 228, MUTED, "已否定", dx=0, dy=-44, anchor="middle")

    cards = [
        (GREEN, "内部", "int S", "有一个开邻域整个落在 S 里：\nS 已经被确认。"),
        (AMBER, "边界", "∂S", "每个开邻域都同时碰到 S 和它的补集：\n既没确认，也没否定。"),
        (MUTED, "外部", "int Sᶜ", "有一个开邻域完全避开 S：\n¬S 已经被确认。"),
    ]
    for i, (c, name, formula, body) in enumerate(cards):
        y = 158 + i * 118
        panel(s, 622, y, 238, 102)
        s.rect(622, y, 5, 102, rx=2, fill=c)
        s.text(640, y + 29, name, size=17, fill=c, weight="700")
        s.text(844, y + 29, formula, size=12.5, fill=MUTED, anchor="end", family=MONO)
        for j, line in enumerate(body.split("\n")):
            s.text(640, y + 55 + j * 21, line, size=12.6, fill=INK)

    s.text(40, 534, "X = int S ∪ ∂S ∪ int Sᶜ，三类点互不重叠 —— 每个点恰好属于一类。",
           size=14.5, fill=INK)
    s.save("topo-02-interior")


# ------------------------------------------------------------------ figure 3
def fig_continuous():
    h = 580
    s = SVG(W, h)
    kicker(s, "图 5 / CONTINUITY")
    title(s, "连续：输出的每个观察，都能用输入的有限观察回答",
          "f 连续，当且仅当每个开集 U 的原像也是开集")

    bx = blob_pts(226, 330, 150, 124, wob=0.07, seed=5, n=10)
    s.path(smooth_closed(bx), stroke=INK, sw=2.2)
    s.text(226, 180, "X", size=24, fill=INK, anchor="middle", weight="700", family=SERIF)

    by = blob_pts(668, 330, 150, 124, wob=0.07, seed=9, n=10)
    s.path(smooth_closed(by), stroke=INK, sw=2.2)
    s.text(668, 180, "Y", size=24, fill=INK, anchor="middle", weight="700", family=SERIF)

    u = blob_pts(700, 300, 72, 56, wob=0.08, seed=13, n=8)
    s.path(smooth_closed(u), fill=GREEN, stroke=GREEN, sw=1.8, opacity=0.16)
    s.path(smooth_closed(u), stroke=GREEN, sw=1.8)
    s.text(700, 338, "U", size=17, fill=GREEN, anchor="middle", weight="700", family=MONO)

    pre = blob_pts(216, 342, 60, 72, wob=0.12, seed=17, n=8)
    s.path(smooth_closed(pre), fill=GREEN, stroke=GREEN, sw=1.8, opacity=0.16)
    s.path(smooth_closed(pre), stroke=GREEN, sw=1.8)
    s.text(216, 348, "f 的原像", size=14.5, fill=GREEN, anchor="middle", weight="700")

    s.arrow((398, 306), (508, 306), color=INK, sw=2.4, curve=-16)
    s.text(452, 276, "f", size=22, fill=INK, anchor="middle", style="italic", family=SERIF)

    s.circle(292, 348, 6, fill=RED, stroke=PAPER, sw=1.4)
    s.text(292, 378, "x", size=14, fill=RED, anchor="middle", family=MONO)
    s.circle(722, 278, 6, fill=RED, stroke=PAPER, sw=1.4)
    s.text(778, 300, "f(x)", size=14, fill=RED, family=MONO, anchor="start")
    s.arrow((300, 344), (712, 284), color=RED, sw=1.2, dash="4 5", opacity=0.75,
            curve=-26)

    s.text(40, 486, "要确认“f(x) ∈ U”，只要确认“x 落在 f 的原像里”。", size=16.5, fill=INK)
    s.text(40, 518, "连续性保证原像是开集：一次有限观察就能确认 —— 输出的每个观察都能被回答。",
           size=14.2, fill=MUTED)
    s.text(40, 550, "在度量空间里，这句话就是 ε-δ：∀ ε > 0, ∃ δ > 0, dist x y < δ ⟹ dist (f x) (f y) < ε。",
           size=13.2, fill=MUTED)
    s.save("topo-03-continuous")


# ------------------------------------------------------------------ figure 4
def fig_zoo():
    h = 640
    s = SVG(W, h)
    kicker(s, "图 6 / HOMEOMORPHISM & INVARIANTS")
    title(s, "形状动物园：哪些不一样，凭什么说不一样",
          "同胚 = 双向连续的双射；不变量 = 被同胚保持的性质")

    cols = [140, 350, 560, 770]
    names = ["[0, 1]", "S¹", "S¹ ∨ S¹", "ℝ"]
    subs = ["闭区间", "圆", "8 字", "直线"]

    s.line((cols[0] - 78, 250), (cols[0] + 78, 250), color=INK, sw=3)
    s.circle(cols[0] - 78, 250, 5.5, fill=INK, stroke=INK)
    s.circle(cols[0] + 78, 250, 5.5, fill=INK, stroke=INK)
    s.text(cols[0] - 78, 224, "0", size=12, fill=MUTED, anchor="middle", family=MONO)
    s.text(cols[0] + 78, 224, "1", size=12, fill=MUTED, anchor="middle", family=MONO)

    s.circle(cols[1], 248, 62, fill="none", stroke=INK, sw=3)
    s.circle(cols[1] + 62, 248, 5.5, fill=GREEN, stroke=GREEN)

    s.circle(cols[2] - 32, 248, 38, fill="none", stroke=INK, sw=3)
    s.circle(cols[2] + 32, 248, 38, fill="none", stroke=INK, sw=3)

    s.line((cols[3] - 84, 248), (cols[3] + 84, 248), color=INK, sw=3)
    s.arrow((cols[3] + 66, 248), (cols[3] + 86, 248), color=INK, sw=3)
    s.arrow((cols[3] - 66, 248), (cols[3] - 86, 248), color=INK, sw=3)

    for x, n, sub in zip(cols, names, subs):
        s.text(x, 342, n, size=19, fill=INK, anchor="middle", family=MONO, weight="600")
        s.text(x, 364, sub, size=12.5, fill=MUTED, anchor="middle")

    rows = [
        ("紧致", ["✓", "✓", "✓", "×"]),
        ("连通", ["✓", "✓", "✓", "✓"]),
        ("基本群 π₁", ["0", "ℤ", "ℤ ∗ ℤ", "0"]),
    ]
    ytop = 400
    s.line((40, ytop), (860, ytop), color=LINE, sw=1.2)
    for i, (name, vals) in enumerate(rows):
        y = ytop + 46 + i * 52
        s.text(44, y + 6, name, size=14.5, fill=MUTED, weight="600")
        for x, v in zip(cols, vals):
            s.text(x, y + 6, v, size=17, fill=INK if v != "×" else MUTED,
                   anchor="middle", family=MONO, weight="600")
        s.line((40, y + 24), (860, y + 24), color="#EDE5D8", sw=1)

    s.text(44, 600, "[0, 1] 与 ℝ 不同胚：紧致性不同。   S¹ 与 8 字不同胚：基本群不同。   ℝ 与 (0, 1) 同胚。",
           size=13.2, fill=INK)
    s.save("topo-04-zoo")


# ------------------------------------------------------------------ figure 5
def fig_compact():
    h = 620
    s = SVG(W, h)
    kicker(s, "图 7 / COMPACTNESS")
    title(s, "紧致：任何开覆盖，都能抽出有限个",
          "局部信息足够多时，紧致性保证只用有限多条就能覆盖全局")

    panel(s, 30, 140, 400, 330)
    s.text(54, 176, "紧致", size=19, fill=GREEN, weight="700")
    s.text(54, 200, "[0, 1]：有有限子覆盖", size=13, fill=MUTED)

    y = 390
    s.line((62, y), (398, y), color=INK, sw=3)
    s.circle(62, y, 4, fill=INK, stroke=INK)
    s.circle(398, y, 4, fill=INK, stroke=INK)

    covers = [(62, 150), (128, 218), (196, 286), (264, 352), (330, 398)]
    for i, (a, b) in enumerate(covers):
        s.arc(a, b, y, 66 + i * 7, color=GREEN, sw=2.4)
    s.text(54, 448, "这 5 个开集就盖住了整条线段：[0,1] 是紧致的。", size=12.2, fill=MUTED)

    panel(s, 470, 140, 400, 330)
    s.text(494, 176, "不紧致", size=19, fill=RED, weight="700")
    s.text(494, 200, "(0, 1)：没有有限子覆盖", size=13, fill=MUTED)

    y2 = 390
    s.line((500, y2), (850, y2), color=INK, sw=3, dash="7 6")
    s.circle(500, y2, 4, fill=PAPER, stroke=INK, sw=1.6)
    s.circle(850, y2, 4, fill=PAPER, stroke=INK, sw=1.6)
    for i, n in enumerate([2, 3, 4, 6]):
        s.arc(502, 500 + 348 * (1 - 1 / n), y2, 40 + i * 14,
              color=RED, sw=1.8, opacity=0.7)
    s.arc(502, 846, y2, 96, color=RED, sw=1.4, dash="4 5", opacity=0.5)
    s.text(500, 444, "U_n = (0, 1−1/n)：每个都差一点到 1；", size=12.4, fill=MUTED)
    s.text(500, 466, "有限个里最长的那个，还是差一点。", size=12.4, fill=MUTED)
    s.text(852, y2 - 22, "1", size=12, fill=MUTED, anchor="middle", family=MONO)
    s.text(500, y2 + 24, "0", size=12, fill=MUTED, anchor="middle", family=MONO)

    s.text(40, 528, "把“每个点附近都成立”升级成“整块上一致成立”，代价是：只付得起有限张证书。",
           size=14.5, fill=INK)
    s.text(40, 558, "紧致性就是这张“有限证书”存在性的保证。Heine–Borel：ℝⁿ 里，紧致 ⟺ 有界且闭。",
           size=13.5, fill=MUTED)
    s.text(40, 588, "反例：(0,1) 有界但不闭；ℚ ∩ [0,1] 有界且闭，但在 ℝ 里不紧致 —— 因为 ℚ 有洞。",
           size=13.5, fill=MUTED)
    s.save("topo-05-compact")


# ------------------------------------------------------------------ figure 6
def fig_connected():
    h = 700
    s = SVG(W, h)
    kicker(s, "图 8 / CONNECTEDNESS")
    title(s, "连通：不能被切成两个非空开集",
          "连续映射把连通集映成连通集 —— 中间值定理就是这句话")

    # panel a: disconnected
    panel(s, 30, 140, 390, 220)
    s.text(54, 172, "不连通", size=18, fill=RED, weight="700")
    s.circle(150, 270, 52, fill=RED, stroke=RED, sw=2, opacity=0.06)
    s.circle(150, 270, 52, stroke=RED, sw=2.2)
    s.circle(300, 270, 52, fill=RED, stroke=RED, sw=2, opacity=0.06)
    s.circle(300, 270, 52, stroke=RED, sw=2.2)
    s.text(150, 276, "A", size=20, fill=RED, anchor="middle", weight="700", family=SERIF)
    s.text(300, 276, "B", size=20, fill=RED, anchor="middle", weight="700", family=SERIF)
    s.text(54, 340, "A、B 都是非空开集，且 A ∪ B 是整个空间。", size=12, fill=MUTED)

    # panel b: sine curve
    panel(s, 450, 140, 420, 220)
    s.text(474, 172, "连通，但不路径连通", size=18, fill=AMBER, weight="700")
    y0 = 272
    pts = []
    for i in range(700):
        t = 0.055 + i * (0.945 / 699)
        pts.append((496 + t * 330, y0 - 54 * math.sin(1 / t)))
    s.poly(pts, color=AMBER, sw=1.6)
    s.line((496, y0 - 54), (496, y0 + 54), color=AMBER, sw=3)
    s.line((480, y0), (840, y0), color=LINE, sw=1, dash="4 6")
    s.text(474, 346, "y = sin(1/x) 的图像，加上 x = 0 处的那条竖线。", size=12, fill=MUTED)

    # panel c: IVT
    panel(s, 30, 385, 840, 230)
    s.text(54, 428, "介值定理：连续 + 连通，就会“经过”中间的一切", size=18, fill=GREEN, weight="700")
    ax, ay = 105, 600
    bx = 800
    s.arrow((ax, ay), (bx, ay), color=INK, sw=1.6)
    s.arrow((ax, ay), (ax, 455), color=INK, sw=1.6)
    s.text(ax - 10, ay + 20, "a", size=13, fill=MUTED, anchor="middle", family=MONO)
    s.text(bx, ay + 20, "b", size=13, fill=MUTED, anchor="middle", family=MONO)

    def curve(t):
        x = ax + 665 * t
        y = ay - 118 * (t ** 0.8) - 14 * math.sin(6 * t)
        return (x, y)

    cs = [curve(i / 200) for i in range(201)]
    s.poly(cs, color=GREEN, sw=2.6)
    xa, ya = curve(0)
    xb, yb = curve(1)
    s.circle(xa, ya, 6, fill=GREEN, stroke=PAPER, sw=1.5)
    s.circle(xb, yb, 6, fill=GREEN, stroke=PAPER, sw=1.5)
    s.text(xa - 12, ya - 8, "f(a)", size=12.5, fill=GREEN, anchor="end", family=MONO)
    s.text(xb + 10, yb - 8, "f(b)", size=12.5, fill=GREEN, family=MONO)

    yc = 530
    s.line((ax, yc), (bx, yc), color=RED, sw=1.2, dash="5 6")
    s.text(ax - 12, yc + 5, "y", size=13, fill=RED, anchor="end", family=MONO)
    t = 0
    while t < 1:
        x, y = curve(t)
        if abs(y - yc) < 1.2:
            break
        t += 0.0005
    x, y = curve(t)
    s.circle(x, y, 7, fill=RED, stroke=PAPER, sw=1.6)
    s.text(x - 20, yc - 30, "∃ c, f(c) = y", size=13.5, fill=RED, anchor="end", family=MONO)

    s.text(54, 664, "如果连通性被破坏，曲线就能从下面“跳到”上面而不经过 y。", size=12.5, fill=MUTED)
    s.save("topo-06-connected")


# ------------------------------------------------------------------ figure 7
def fig_quotient():
    h = 590
    s = SVG(W, h)
    kicker(s, "图 9 / QUOTIENT SPACES")
    title(s, "商空间：把点粘起来，拓扑也跟着粘",
          "粘合就是商类型：先声明哪些点等价，再看哪些函数还连续")

    cols = [150, 450, 750]
    heads = ["① 线段 → 圆", "② 正方形 → 环面", "③ 矩形 → Möbius 带"]
    for x, t in zip(cols, heads):
        s.text(x, 172, t, size=16.5, fill=INK, anchor="middle", weight="600")

    # ---- column 1: interval -> circle
    y = 252
    s.line((85, y), (215, y), color=INK, sw=3)
    s.circle(85, y, 6.5, fill=GREEN, stroke=PAPER, sw=1.4)
    s.circle(215, y, 6.5, fill=GREEN, stroke=PAPER, sw=1.4)
    s.text(85, y + 24, "0", size=12, fill=GREEN, anchor="middle", family=MONO)
    s.text(215, y + 24, "1", size=12, fill=GREEN, anchor="middle", family=MONO)
    s.arc(92, 208, y - 8, 74, color=GREEN, sw=1.8, dash="5 5")
    s.arrow((150, 300), (150, 336), color=MUTED, sw=1.8)
    s.text(162, 322, "商", size=12, fill=MUTED)
    s.circle(150, 430, 52, stroke=INK, sw=3)
    a0 = -0.6
    s.circle(150 + 52 * math.cos(a0), 430 + 52 * math.sin(a0), 5.5, fill=GREEN,
             stroke=PAPER, sw=1.4)
    s.arrow((150 - 40 * math.cos(a0), 430 - 40 * math.sin(a0)),
            (150 + 30 * math.cos(a0 + 2.5), 430 + 30 * math.sin(a0 + 2.5)),
            color=GREEN, sw=1.4, curve=16)
    s.text(150, 522, "S¹ = [0,1] / (0~1)", size=12.5, fill=MUTED, anchor="middle",
           family=MONO)

    # ---- column 2: square -> torus
    x0, y0, w = 395, 208, 110
    s.rect(x0, y0, w, w, fill=PANEL, stroke=INK, sw=2)
    for yy in (y0, y0 + w):
        s.arrow((x0 + 18, yy), (x0 + w - 14, yy), color=GREEN, sw=1.6)
        s.text(x0 + w / 2, yy + 19 if yy == y0 else yy - 8, "a", size=12.5,
               fill=GREEN, anchor="middle", family=MONO, weight="600")
    for xx in (x0, x0 + w):
        s.arrow((xx, y0 + w - 18), (xx, y0 + 14), color=RED, sw=1.6)
        s.text(xx - 12 if xx == x0 else xx + 12, y0 + w / 2 + 4, "b", size=12.5,
               fill=RED, anchor="middle", family=MONO, weight="600")
    s.arrow((450, 342), (450, 378), color=MUTED, sw=1.8)
    s.text(462, 364, "商", size=12, fill=MUTED)
    torus(s, 450, 452, 70, 30)
    s.text(450, 548, "T² = S¹ × S¹", size=12.5, fill=MUTED, anchor="middle", family=MONO)

    # ---- column 3: rectangle -> mobius
    rx0, ry0, rw, rh = 686, 218, 128, 64
    s.rect(rx0, ry0, rw, rh, fill=PANEL, stroke=INK, sw=2)
    s.arrow((rx0, ry0 + rh - 10), (rx0, ry0 + 10), color=GREEN, sw=1.7)
    s.arrow((rx0 + rw, ry0 + 10), (rx0 + rw, ry0 + rh - 10), color=RED, sw=1.7)
    s.text(rx0 - 13, ry0 + rh / 2 + 5, "↑", size=15, fill=GREEN, anchor="middle")
    s.text(rx0 + rw + 13, ry0 + rh / 2 + 5, "↓", size=15, fill=RED, anchor="middle")
    s.arrow((750, 306), (750, 342), color=MUTED, sw=1.8)
    s.text(762, 328, "商", size=12, fill=MUTED)

    mx, my, a, b = 750, 444, 58, 22
    outer, inner = [], []
    for i in range(181):
        t = 2 * math.pi * i / 180
        wob = b * math.cos(t / 2)
        outer.append((mx + (a + wob) * math.cos(t),
                      my + (a + wob) * 0.55 * math.sin(t) + b * math.sin(t / 2) * 0.55))
        inner.append((mx + (a - wob) * math.cos(t),
                      my + (a - wob) * 0.55 * math.sin(t) - b * math.sin(t / 2) * 0.55))
    band = f"M {outer[0][0]:.1f} {outer[0][1]:.1f}"
    for p in outer[1:]:
        band += f" L {p[0]:.1f} {p[1]:.1f}"
    for p in reversed(inner):
        band += f" L {p[0]:.1f} {p[1]:.1f}"
    s.path(band + " Z", fill="#EFE6D6", opacity=0.9)
    s.poly(outer, color=INK, sw=2.2)
    s.poly(inner, color=INK, sw=2.2)
    for i in range(0, 181, 20):
        s.line(outer[i], inner[i], color="#C9BFAE", sw=1)
    s.text(750, 542, "只有一个面，一条边", size=12.5, fill=MUTED, anchor="middle")

    s.text(40, 578, "粘合方式决定了形状：同一个正方形，改一下边的方向，得到的空间就换了。",
           size=13.5, fill=INK)
    s.save("topo-07-quotient")


# ------------------------------------------------------------------ figure 8
def fig_homotopy():
    h = 630
    s = SVG(W, h)
    kicker(s, "图 10 / HOMOTOPY & FUNDAMENTAL GROUP")
    title(s, "同伦：允许形变之后，剩下的才是“形状”",
          "绕不过去的洞，被基本群记成一个整数")

    s.rect(60, 150, 800, 340, rx=18, fill="#F4EEE2", stroke="#E4D9C6", sw=1)

    # the hole
    s.circle(400, 320, 58, fill=PAPER, stroke=INK, sw=2.4)
    s.text(400, 326, "洞", size=15, fill=MUTED, anchor="middle")

    # loop around the hole
    s.circle(400, 320, 118, fill="none", stroke=RED, sw=2.8, dash="9 7")
    s.arrow((400 + 118 * math.cos(-0.45), 320 + 118 * math.sin(-0.45)),
            (400 + 100 * math.cos(-0.9), 320 + 100 * math.sin(-0.9)),
            color=RED, sw=2.4, curve=18)
    s.text(268, 314, "绕数 1", size=13.5, fill=RED, anchor="end", weight="600")
    s.text(268, 336, "怎样都缩不成一点", size=12.5, fill=RED, anchor="end")

    # contractible loop
    cx, cy = 700, 258
    for rr, op in ((52, 0.25), (36, 0.45), (20, 0.75)):
        s.circle(cx, cy, rr, stroke=GREEN, sw=1.6, opacity=op, dash="5 5")
    s.circle(cx, cy, 5, fill=GREEN, stroke=GREEN)
    s.arrow((cx + 70, cy + 46), (cx + 24, cy + 18), color=GREEN, sw=1.4, dash="4 5")
    s.text(cx, cy + 78, "绕数 0：缩成一点", size=13, fill=GREEN, anchor="middle", weight="600")

    s.text(92, 192, "平面 ℝ²", size=13, fill=MUTED, family=SERIF)

    s.text(40, 534, "π₁(ℝ² ∖ {0}) ≅ ℤ：每个环落在一个整数上，连续形变不改变它。", size=15.5, fill=INK)
    s.text(40, 566, "而 π₁(ℝ²) = 0。于是“挖了一个点的平面”与“平面”不同胚 —— 尽管两者都连通、都不可数。",
           size=13.5, fill=MUTED)
    s.text(40, 598, "同伦比同胚粗：它允许把距离、角度、甚至把整个空间压扁，只留下“洞”的信息。",
           size=13.5, fill=MUTED)
    s.save("topo-08-homotopy")


# ------------------------------------------------------------------ cover
def cover():
    h = 500
    s = SVG(W, h)
    s.text(60, 54, "拓扑学 · 写给计算机科学家", size=13, fill=GREEN, spacing=2.6, weight="700")
    s.text(60, 160, "拓扑学", size=62, fill=INK, weight="700")
    s.text(60, 232, "形状的逻辑", size=44, fill=INK, weight="700")
    s.line((60, 258), (300, 258), color=GREEN, sw=3)
    s.text(60, 292, "开集是可确认的性质", size=17, fill=MUTED)
    s.text(60, 320, "空间是一套理论，点是它的模型", size=17, fill=MUTED)
    s.text(60, 348, "连续是理论的翻译", size=17, fill=MUTED)
    s.text(60, 436, "关键定义都有 Lean 4 版本", size=13, fill=MUTED)
    s.text(60, 462, "不需要任何前置知识", size=12.5, fill=MUTED)

    torus(s, 680, 250, 118, 48)
    s.text(680, 398, "T²", size=20, fill=MUTED, anchor="middle", family=MONO)
    s.text(680, 432, "π₁ ≅ ℤ × ℤ", size=13, fill=MUTED, anchor="middle", family=MONO)
    s.save("topo-cover")


def card_cover():
    subprocess.run([
        "magick", "images/topo-cover.png",
        "-crop", "1778x1000+11+0", "+repage",
        "-resize", "1200x675", "images/topo-cover-card.png",
    ], check=True)
    print("wrote topo-cover-card")


if __name__ == "__main__":
    fig_tree(); fig_lattice(); fig_system()
    fig_interior(); fig_continuous(); fig_zoo()
    fig_compact(); fig_connected(); fig_quotient(); fig_homotopy()
    cover(); card_cover()
