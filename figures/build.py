#!/usr/bin/env python3
"""Generate the SVG figures for the liveness article, then rasterize with ImageMagick."""
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

SANS = "PingFang SC, Hiragino Sans GB, Noto Sans CJK SC, sans-serif"
SERIF = "Songti SC, STSong, Noto Serif CJK SC, serif"
MONO = "SFMono-Regular, Menlo, Consolas, monospace"

COLORS = {"ink": INK, "red": RED, "green": GREEN, "muted": MUTED,
          "amber": AMBER, "orange": ORANGE, "white": "#FFFFFF"}


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


class SVG:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.parts = []
        self.defs = []

    def add(self, s):
        self.parts.append(s)

    def marker(self, key, color):
        self.defs.append(
            f'<marker id="ar-{key}" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{color}"/></marker>')

    def text(self, x, y, s, size=18, fill=INK, anchor="start", family=SANS,
             weight="normal", style="normal", spacing=0, opacity=1):
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
        # tangents at endpoints
        v1 = (cx - x1, cy - y1)
        l1 = math.hypot(*v1) or 1
        v2 = (x2 - cx, y2 - cy)
        l2 = math.hypot(*v2) or 1
        sx, sy = x1 + v1[0] / l1 * r1, y1 + v1[1] / l1 * r1
        ex, ey = x2 - v2[0] / l2 * r2, y2 - v2[1] / l2 * r2
        key = "ink"
        for k, v in COLORS.items():
            if v == color:
                key = k
        if key not in [m[0] for m in getattr(self, "_markers", [])]:
            if not hasattr(self, "_markers"):
                self._markers = []
            self.marker(key, color)
            self._markers.append((key, color))
        da = f' stroke-dasharray="{dash}"' if dash else ""
        o = f' opacity="{opacity}"' if opacity != 1 else ""
        m = f' marker-end="url(#ar-{key})"' if head else ""
        self.add(f'<path d="M {sx:.1f} {sy:.1f} Q {cx:.1f} {cy:.1f} {ex:.1f} {ey:.1f}" '
                 f'fill="none" stroke="{color}" stroke-width="{sw}" '
                 f'stroke-linecap="round"{da}{o}{m}/>')

    def node(self, x, y, r, fill, stroke, label, label_fill="#FFFFFF", size=16,
             sw=2, rank=None, rank_fill=None, double=False, rank_pos=None):
        if double:
            self.circle(x, y, r + 5, fill="none", stroke=stroke, sw=1.5)
        self.circle(x, y, r, fill=fill, stroke=stroke, sw=sw)
        self.text(x, y + size * 0.35, label, size=size, fill=label_fill,
                  anchor="middle", weight="600")
        if rank is not None:
            bx, by = rank_pos or (x + r * 0.78, y - r * 0.78)
            rf = rank_fill or fill
            self.circle(bx, by, 10.5, fill=PAPER, stroke=stroke, sw=1.4)
            self.text(bx, by + 4, rank, size=11, fill=rf if rank_fill else stroke,
                      anchor="middle", weight="600")

    def render(self):
        defs = "".join(self.defs)
        body = "".join(self.parts)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w*2}" '
                f'height="{self.h*2}" viewBox="0 0 {self.w} {self.h}" '
                f'text-rendering="geometricPrecision">'
                f'<defs>{defs}</defs>'
                f'<rect width="{self.w}" height="{self.h}" fill="{PAPER}"/>'
                f'{body}</svg>')

    def save(self, name):
        os.makedirs("images/src", exist_ok=True)
        svg = self.render()
        with open(f"images/src/{name}.svg", "w", encoding="utf-8") as f:
            f.write(svg)
        subprocess.run(["magick", f"images/src/{name}.svg", f"images/{name}.png"],
                       check=True)
        print("wrote", name)


def kicker(s, txt):
    s.text(40, 38, txt, size=13, fill=MUTED, spacing=2.4, weight="600")


def title(s, t, sub=None):
    s.text(40, 78, t, size=32, fill=INK, weight="700")
    if sub:
        s.text(40, 110, sub, size=18, fill=MUTED)


# ---------------------------------------------------------------- lock state box
def lock_box(s, cx, cy, name, lock, t2, stroke=RED, title_fill=RED,
             fill=PANEL, rank=None):
    w, h = 176, 108
    x, y = cx - w / 2, cy - h / 2
    s.rect(x, y, w, h, rx=14, fill=fill, stroke=stroke, sw=2.2)
    s.text(x + 14, y + 26, name, size=18, fill=title_fill, weight="700")
    s.text(x + 14, y + 48, "lock", size=12, fill=MUTED)
    for lab, dx in (("T1", 62), ("T2", 112)):
        ox, oy = x + dx, y + 44
        owned = (lock == lab)
        s.circle(ox, oy, 5.5, fill=INK if owned else PAPER,
                 stroke=INK if owned else LINE, sw=1.4)
        s.text(ox, y + 60, lab, size=11, fill=MUTED, anchor="middle")
    s.text(x + 14, y + 84, "T2", size=12, fill=MUTED)
    spin = (t2 == "spin")
    s.circle(x + 62, y + 80, 5.5, fill=AMBER if spin else PAPER,
             stroke=AMBER if spin else LINE, sw=1.4)
    s.text(x + 78, y + 84, "spin" if spin else "inside", size=13, fill=INK)
    if rank is not None:
        bx, by = x + w - 14, y + 14
        s.circle(bx, by, 10.5, fill=PAPER, stroke=stroke, sw=1.3)
        s.text(bx, by + 4, rank, size=11.5, fill=title_fill,
               anchor="middle", weight="600")


# ---------------------------------------------------------------- figure 1
def fig1():
    h = 500
    s = SVG(W, h)
    kicker(s, "图 1 / SAFETY & LIVENESS")
    title(s, "两种 Bug", "证据的长度，决定了你该怎么找它")

    # panels
    for x in (40, 470):
        s.rect(x, 140, 390, 300, rx=16, fill=PANEL, stroke="#E8DFCF", sw=1.2)
    s.path("M 450 165 L 450 425", stroke=LINE, sw=1.2, dash="4 7")

    # left
    s.text(64, 178, "SAFETY", size=13, fill=RED, spacing=2.2, weight="700")
    s.text(64, 210, "坏事发生了", size=23, fill=INK, weight="700")
    s.text(64, 238, "有限前缀就是证据", size=15, fill=MUTED)

    ys = 305
    xs = [82, 140, 198, 256, 314, 372]
    for a, b in zip(xs, xs[1:]):
        if a < 256:
            s.arrow((a + 13, ys), (b - 13, ys), color=INK, sw=1.8)
        else:
            s.arrow((a + 13, ys), (b - 13, ys), color=LINE, sw=1.6, dash="3 5")
    for i, x in enumerate(xs):
        if i == 3:
            s.circle(x, ys, 15, fill=RED, stroke=RED_DARK, sw=1.5)
            s.text(x, ys + 7, "×", size=22, fill="#FFFFFF", anchor="middle", weight="700")
        elif i > 3:
            s.circle(x, ys, 12, fill=PAPER, stroke=LINE, sw=1.5)
        else:
            s.circle(x, ys, 12, fill=PAPER, stroke=INK, sw=1.8)
    # bracket
    s.path("M 82 345 L 82 356 L 256 356 L 256 345", stroke=RED, sw=1.6)
    s.text(169, 382, "证据：3 步", size=16, fill=RED, anchor="middle", weight="600")
    s.text(64, 416, "一旦发生，无法撤销", size=15, fill=INK)

    # right
    s.text(494, 178, "LIVENESS", size=13, fill=GREEN, spacing=2.2, weight="700")
    s.text(494, 210, "好事一直没发生", size=23, fill=INK, weight="700")
    s.text(494, 238, "每一步都只是“还没”", size=15, fill=MUTED)

    xs2 = [512, 565, 618, 671, 724, 777]
    for a, b in zip(xs2, xs2[1:]):
        s.arrow((a + 12, ys), (b - 12, ys), color=MUTED, sw=1.6, dash="3 5")
    for x in xs2:
        s.circle(x, ys, 12, fill=PAPER, stroke=MUTED, sw=1.6)
    s.arrow((789, ys), (838, ys), color=MUTED, sw=1.6, dash="2 6")
    s.text(846, ys + 10, "∞", size=30, fill=RED, anchor="middle", weight="700")
    s.text(669, 272, "p 从未出现", size=15, fill=RED, anchor="middle", weight="600")
    # bracket
    s.path("M 512 345 L 512 356 L 777 356 L 777 345", stroke=RED, sw=1.6)
    s.text(645, 382, "任意长的前缀", size=16, fill=RED, anchor="middle", weight="600")
    s.text(494, 416, "看多久都不能定罪", size=15, fill=INK)
    s.save("01-two-kinds-of-bugs")


# ---------------------------------------------------------------- figure 2
def fig_open():
    h = 440
    s = SVG(W, h)
    kicker(s, "MUTEX / STATE GRAPH")
    title(s, "锁的状态图", "T1 和 T2 抢一把 test-and-set 自旋锁")

    S, R, G = (170, 250), (420, 250), (700, 250)
    s.rect(70, 175, 460, 155, rx=24, fill=RED, stroke="none", opacity=0.045)
    s.rect(70, 175, 460, 155, rx=24, fill="none", stroke=RED, sw=1.2,
           dash="5 6", opacity=0.4)
    s.text(300, 160, "T2 永远等下去", size=14, fill=RED, anchor="middle", weight="600")

    s.arrow((S[0] + 88, S[1]), (R[0] - 88, R[1]), color=INK, sw=2.2)
    s.arrow((R[0] - 55, R[1] - 54), (S[0] + 55, S[1] - 54),
            curve=35, color=INK, sw=2.2)
    s.arrow((R[0] + 88, R[1]), (G[0] - 88, G[1]), color=GREEN, sw=2.2, dash="6 6")
    s.text(295, 220, "T1 抢到", size=13.5, fill=INK, anchor="middle", weight="600")
    s.text(295, 270, "T1 释放", size=13.5, fill=MUTED, anchor="middle")
    s.text(560, 270, "T2 抢到", size=13.5, fill=GREEN, anchor="middle", weight="600")

    lock_box(s, *S, "S", "T1", "spin")
    lock_box(s, *R, "R", "free", "spin")
    lock_box(s, *G, "G", "T2", "inside", stroke=GREEN, title_fill=GREEN,
             fill="#E8F0EC")

    s.text(70, 390, "● = 真（持有 / 等待）    ○ = 假（空闲 / 运行）",
           size=12.5, fill=MUTED)
    s.save("lock-state-graph")


def fig2():
    h = 560
    s = SVG(W, h)
    kicker(s, "图 3 / LASSO")
    title(s, "反例的形状：一个环",
          "回到开头的锁状态图：S 和 R 转来转去，G 永远到不了")

    S, R, G = (180, 290), (450, 290), (740, 290)
    s.rect(80, 195, 460, 175, rx=26, fill=RED, stroke="none", opacity=0.05)
    s.rect(80, 195, 460, 175, rx=26, fill="none", stroke=RED, sw=1.2,
           dash="5 6", opacity=0.45)
    s.text(310, 173, "坏环", size=15, fill=RED, anchor="middle", weight="700")

    s.arrow((S[0] + 88, S[1]), (R[0] - 88, R[1]), color=RED, sw=2.3)
    s.arrow((R[0] - 55, R[1] - 54), (S[0] + 55, S[1] - 54),
            curve=35, color=RED, sw=2.3)
    s.arrow((R[0] + 88, R[1]), (G[0] - 88, G[1]), color=GREEN, sw=2.3, dash="6 6")

    s.text(315, 214, "T1 又抢到", size=12.5, fill=RED, anchor="middle", weight="600")
    s.text(315, 310, "T1 释放", size=13, fill=MUTED, anchor="middle")
    s.text(595, 265, "T2 抢到（没走）", size=12.5, fill=GREEN,
           anchor="middle", weight="600")

    lock_box(s, *S, "S", "T1", "spin")
    lock_box(s, *R, "R", "free", "spin")
    lock_box(s, *G, "G", "T2", "inside", stroke=GREEN, title_fill=GREEN,
             fill="#E8F0EC")
    s.text(78, 296, "start", size=12.5, fill=RED, anchor="end", weight="600")

    s.text(80, 450, "一条永远不到 G 的执行", size=14, fill=MUTED)
    s.text(80, 486, "σ = (S R)^ω", size=22, fill=INK, family=MONO)
    s.text(420, 486, "G 有入边；但这条执行永远不选它", size=13.5, fill=MUTED)
    s.save("03-lasso")


# ---------------------------------------------------------------- figure 3
def fig3():
    h = 565
    s = SVG(W, h)
    kicker(s, "图 4 / LEAST & GREATEST FIXED POINTS")
    title(s, "两个不动点：从下往上，从上往下",
          "方程本身有很多解；“最小”和“最大”替我们挑出答案")

    for x in (40, 470):
        s.rect(x, 130, 390, 340, rx=16, fill=PANEL, stroke="#E8DFCF", sw=1.2)
    s.text(64, 170, "μ｜最小不动点", size=21, fill=GREEN, weight="700")
    s.text(64, 194, "从空集往上长", size=14, fill=MUTED)
    s.text(494, 170, "ν｜最大不动点", size=21, fill="#B07C22", weight="700")
    s.text(494, 194, "从全集往下剥", size=14, fill=MUTED)

    x0, x1, y0, y1 = 88, 400, 415, 250
    ymap = lambda v: y0 - v / 3.2 * (y0 - y1)
    xs = [x0 + i * (x1 - x0) / 5 for i in range(6)]
    labels = ["X₀", "X₁", "X₂", "X₃", "X₄", "X₅"]

    def chart(xoff, vals, color, start_label, end_label):
        ys = [ymap(v) for v in vals]
        s.path(f"M {x0+xoff} 245 L {x0+xoff} {y0} L {405+xoff} {y0}",
               stroke=LINE, sw=1.3)
        s.text(x0 + xoff - 6, 250, "S", size=11, fill=MUTED, anchor="end")
        s.text(x0 + xoff - 6, y0 + 4, "∅", size=11, fill=MUTED, anchor="end")
        s.text(405 + xoff, 242, "集合大小（示意）", size=10.5, fill=MUTED, anchor="end")
        d = f"M {xs[0]+xoff:.1f} {ys[0]:.1f}"
        for i in range(5):
            d += f" L {xs[i+1]+xoff:.1f} {ys[i]:.1f} L {xs[i+1]+xoff:.1f} {ys[i+1]:.1f}"
        s.path(d, stroke=color, sw=2.6)
        for x, y in zip(xs, ys):
            s.circle(x + xoff, y, 4.6, fill=PAPER, stroke=color, sw=1.8)
        # plateau marker
        s.path(f"M {xs[4]+xoff:.1f} {ys[4]:.1f} L {405+xoff:.1f} {ys[4]:.1f}",
               stroke=color, sw=1.2, dash="3 5")
        for x, lab in zip(xs, labels):
            s.text(x + xoff, 438, lab, size=11, fill=MUTED, anchor="middle", family=MONO)
        s.text(405 + xoff, 456, "迭代轮次", size=10.5, fill=MUTED, anchor="end")
        s.text(405 + xoff, ys[4] + 18, "停在这里", size=11, fill=color, anchor="end",
               weight="600")

    chart(0, [0, 0.55, 1.65, 2.55, 3.0, 3.0], GREEN, "∅", "μ")
    chart(430, [3.0, 2.8, 2.0, 1.2, 0.8, 0.8], "#C08A2E", "S", "ν")

    s.text(64, 464, "从 ∅ 出发，只会往上", size=12, fill=MUTED)
    s.text(494, 464, "从 S 出发，只会往下", size=12, fill=MUTED)
    s.text(64, 498, "X(0) = ∅,   X(n+1) = f(X(n))", size=12.5, fill=INK, family=MONO)
    s.text(494, 498, "X(0) = S,   X(n+1) = f(X(n))", size=12.5, fill=INK, family=MONO)
    s.text(450, 540, "有限状态 → 最多 |S|+1 轮一定停；这就是“解方程”能替代“跑无限步”的原因。",
           size=14.5, fill=MUTED, anchor="middle")
    s.save("04-two-fixed-points")


# ---------------------------------------------------------------- figure 4
def fig4():
    h = 560
    s = SVG(W, h)
    kicker(s, "图 5 / ATTRACTOR")
    title(s, "点亮：从目标倒着长",
          "同一张锁状态图：只有 G 被点亮")

    S, R, G = (180, 290), (450, 290), (740, 290)
    s.rect(80, 210, 460, 160, rx=26, fill=RED, stroke="none", opacity=0.05)
    s.rect(80, 210, 460, 160, rx=26, fill="none", stroke=RED, sw=1.2,
           dash="5 6", opacity=0.45)
    s.text(310, 188, "点不亮：坏环", size=15, fill=RED, anchor="middle", weight="700")

    s.arrow((S[0] + 88, S[1]), (R[0] - 88, R[1]), color=RED, sw=2.3)
    s.arrow((R[0] - 55, R[1] - 54), (S[0] + 55, S[1] - 54),
            curve=35, color=RED, sw=2.3)
    s.arrow((R[0] + 88, R[1]), (G[0] - 88, G[1]), color=MUTED, sw=2.0, dash="6 6")
    s.text(595, 265, "有出口，但没走", size=12.5, fill=MUTED,
           anchor="middle")

    lock_box(s, *S, "S", "T1", "spin", rank="∞")
    lock_box(s, *R, "R", "free", "spin", rank="∞")
    lock_box(s, *G, "G", "T2", "inside", stroke=GREEN, title_fill=GREEN,
             fill="#E8F0EC", rank="0")

    s.text(80, 440, "先点亮 G（0 步）。只有“所有后继都亮了”的点才会亮。",
           size=13.5, fill=MUTED)
    s.text(80, 466, "R 有一条边回到 S，S 又回到 R；所以 S、R 都停在 ∞。",
           size=13.5, fill=MUTED)
    s.text(80, 510, "0 = 目标    ∞ = 点不亮", size=12.5, fill=MUTED, spacing=1)
    s.save("05-peeling")


# ---------------------------------------------------------------- figure 5
def fig5():
    h = 480
    s = SVG(W, h)
    kicker(s, "图 6 / FAIRNESS")
    title(s, "公平性：liveness 的隐形前提",
          "没有公平的调度，“最终”可以被无限期推迟")

    for x in (40, 470):
        s.rect(x, 130, 390, 260, rx=16, fill=PANEL, stroke="#E8DFCF", sw=1.2)

    s.text(64, 168, "不公平的调度", size=20, fill=RED, weight="700")
    s.text(64, 193, "T2 一直 enabled，却永远轮不到", size=12.5, fill=MUTED)
    s.text(494, 168, "弱公平的调度", size=20, fill=GREEN, weight="700")
    s.text(494, 193, "T2 会被选中，最终拿到锁", size=12.5, fill=MUTED)

    cw, ch, gap = 36, 28, 5

    def cell(x, y, fill, stroke, label, color, dash=None):
        s.rect(x, y, cw, ch, rx=6, fill=fill, stroke=stroke, sw=1.3, dash=dash)
        s.text(x + cw / 2, y + ch / 2 + 5, label, size=12, fill=color,
               anchor="middle", family=MONO, weight="600")

    # left grid
    gx, y1, y2 = 100, 232, 282
    s.text(64, y1 + 19, "T1", size=12, fill=MUTED, family=MONO)
    s.text(64, y2 + 19, "T2", size=12, fill=MUTED, family=MONO)
    for i in range(7):
        x = gx + i * (cw + gap)
        cell(x, y1, "#F4DCD4", RED, "A", RED)
        cell(x, y2, "none", LINE, "·", MUTED, dash="3 4")
    s.text(gx + 7 * (cw + gap), y1 + 19, "…", size=14, fill=MUTED)
    s.path(f"M {gx} 330 L {gx} 340 L {gx+7*(cw+gap)-gap} 340 L {gx+7*(cw+gap)-gap} 330",
           stroke=RED, sw=1.4)
    s.text(gx + 7 * (cw + gap) / 2 - 2, 362, "从未被调度", size=12.5, fill=RED,
           anchor="middle", weight="600")

    # right grid
    gx2 = 530
    s.text(494, y1 + 19, "T1", size=12, fill=MUTED, family=MONO)
    s.text(494, y2 + 19, "T2", size=12, fill=MUTED, family=MONO)
    for i in range(7):
        x = gx2 + i * (cw + gap)
        if i % 2 == 0:
            cell(x, y1, "#E8F0EC", GREEN, "A", GREEN)
            cell(x, y2, "none", LINE, "·", MUTED, dash="3 4")
        else:
            cell(x, y1, "none", LINE, "·", MUTED, dash="3 4")
            cell(x, y2, "#DCEBE5", GREEN, "B", GREEN)
    s.text(gx2 + 7 * (cw + gap), y1 + 19, "…", size=14, fill=MUTED)
    s.text(gx2 + 7 * (cw + gap) - 12, y2 + 19, "✓", size=15, fill=GREEN, weight="700")
    s.text(gx + 7 * (cw + gap) - 12, y2 + 19, "✗", size=15, fill=RED, weight="700")
    s.rect(742, 204, 66, 24, rx=12, fill="#E1EEE8", stroke="none")
    s.text(775, 220, "有进展", size=11.5, fill=GREEN, anchor="middle", weight="700")
    s.text(64, 378, "T2 的槽位一直是空的", size=11.5, fill=MUTED)
    s.text(494, 378, "T2 的槽位终于被填上", size=11.5, fill=MUTED)

    # vs
    s.circle(450, 260, 15, fill=PAPER, stroke=LINE, sw=1.2)
    s.text(450, 264, "vs", size=10.5, fill=MUTED, anchor="middle", weight="600")

    s.text(450, 425, "WF(B): ◇□ Enabled(B) ⇒ □◇ B", size=17, fill=INK,
           anchor="middle", family=MONO)
    s.text(450, 452, "弱公平：从某一刻起一直 enabled，就会无限多次被执行",
           size=12.5, fill=MUTED, anchor="middle")
    s.save("06-fairness")


# ---------------------------------------------------------------- cover
def cover():
    h = 500
    s = SVG(W, h)
    # a faint oversized ring in the background
    s.circle(700, 250, 210, fill="none", stroke=RED, sw=1, opacity=0.06)
    s.text(60, 52, "形式化验证 · 科普", size=13, fill=RED, spacing=2.6, weight="700")
    s.text(60, 150, "永远不报错的", size=46, fill=INK, weight="700")
    s.text(60, 222, "Bug", size=66, fill=RED, weight="700")
    s.path("M 60 246 L 190 246", stroke=RED, sw=3)
    s.text(60, 288, "程序验证里的 liveness 与不动点", size=18, fill=MUTED)
    s.text(60, 316, "从“最终”到方程", size=14, fill=MUTED)
    s.text(60, 430, "写给不熟悉形式化验证的软件工程师", size=13, fill=MUTED)
    s.text(60, 456, "不需要预备知识", size=12, fill=MUTED)

    # lasso: stem into a loop with an exit
    cx, cy, r = 700, 255, 86
    s.arrow((560, cy), (cx - r, cy), r1=0, r2=0, color=INK, sw=2.2)
    s.circle(560, cy, 9, fill=PAPER, stroke=INK, sw=2)
    s.text(560, cy + 30, "start", size=11, fill=MUTED, anchor="middle", family=MONO)
    # loop with a gap at the upper right
    a1, a2 = math.radians(-28), math.radians(-62)
    p1 = (cx + r * math.cos(a1), cy + r * math.sin(a1))
    p2 = (cx + r * math.cos(a2), cy + r * math.sin(a2))
    s.path(f"M {p1[0]:.1f} {p1[1]:.1f} A {r} {r} 0 1 1 {p2[0]:.1f} {p2[1]:.1f}",
           stroke=RED, sw=3)
    # loop direction arrow
    s.circle(cx + r * math.cos(math.radians(150)), cy + r * math.sin(math.radians(150)),
             4, fill=RED, stroke="none")
    s.circle(cx + r * math.cos(math.radians(230)), cy + r * math.sin(math.radians(230)),
             4, fill=RED, stroke="none")
    # exit
    s.arrow((cx + r * math.cos(math.radians(-45)) + 2, cy + r * math.sin(math.radians(-45)) + 2),
            (cx + 150, cy - 125), color=GREEN, sw=2.6)
    s.text(cx + 160, cy - 130, "出口", size=18, fill=GREEN, weight="700")
    s.text(700, 262, "∞", size=38, fill=RED, anchor="middle", weight="700")
    s.save("00-cover")




# ---------------------------------------------------------------- temporal patterns
def fig_temporal():
    h = 620
    s = SVG(W, h)
    kicker(s, "图 2 / FOUR PATTERNS")
    title(s, "四种时间模式", "同一条时间线，四种不同的承诺")
    s.text(40, 146, "横轴是时间；实心 = p 成立，空心 = p 不成立。", size=13.5, fill=MUTED)

    rows = [
        (230, "◇p", "最终 p", "发生一次就算数"),
        (330, "□p", "永远 p", "一次都不能少"),
        (430, "□◇p", "无限多次 p", "反复发生，可以中断"),
        (530, "◇□p", "最终永远 p", "从某一刻起不再停"),
    ]
    xs = [260 + i * 58 for i in range(11)]
    for y, sym, cn, note in rows:
        s.path(f"M 250 {y} L 855 {y}", stroke=LINE, sw=1.2)
        s.text(40, y - 8, sym, size=25, fill=INK, family=MONO, weight="600")
        s.text(40, y + 20, cn, size=15, fill=INK, weight="600")
        s.text(40, y + 40, note, size=12, fill=MUTED)

    # ◇p: one occurrence
    for i, x in enumerate(xs):
        if i == 5:
            s.circle(x, 230, 9, fill=GREEN, stroke=GREEN)
        else:
            s.circle(x, 230, 8, fill=PAPER, stroke=MUTED, sw=1.4)
    s.text(550, 205, "某一次", size=12, fill=GREEN, anchor="middle")

    # □p: all occurrences
    for x in xs:
        s.circle(x, 330, 9, fill=GREEN, stroke=GREEN)

    # □◇p: infinitely many occurrences
    for i, x in enumerate(xs):
        if i in (1, 4, 7, 10):
            s.circle(x, 430, 9, fill=GREEN, stroke=GREEN)
        else:
            s.circle(x, 430, 8, fill=PAPER, stroke=MUTED, sw=1.4)
    s.text(866, 438, "∞", size=22, fill=RED, anchor="middle", weight="700")

    # ◇□p: from some point on, forever
    s.rect(538, 505, 318, 50, rx=10, fill=GREEN, stroke="none", opacity=0.06)
    s.path("M 538 500 L 538 560", stroke=GREEN, sw=1.2, dash="3 5")
    s.text(548, 500, "从这一刻起", size=12, fill=GREEN, weight="600")
    for i, x in enumerate(xs):
        if i >= 5:
            s.circle(x, 530, 9, fill=GREEN, stroke=GREEN)
        else:
            s.circle(x, 530, 8, fill=PAPER, stroke=MUTED, sw=1.4)

    s.text(450, 598, "◇p、□◇p、◇□p 是 liveness；□p 是 safety。",
           size=13, fill=MUTED, anchor="middle")
    s.save("02-four-eventualities")



# ---------------------------------------------------------------- safety example
def fig_safety():
    h = 380
    s = SVG(W, h)
    kicker(s, "SAFETY EXAMPLE")
    title(s, "永远安全：一个三状态的小例子",
          "A、B 都在 Safe 里，但 B 有一条边到 Bad")

    A, B, Bad, r = (220, 200), (440, 200), (680, 200), 36
    s.rect(150, 135, 360, 130, rx=20, fill=GREEN, stroke=GREEN, sw=1.2,
           dash="5 6", opacity=0.05)
    s.text(330, 125, "Safe", size=14, fill=GREEN, anchor="middle", weight="600")

    s.arrow(A, B, r1=r, r2=r, color=INK, sw=2.2)
    s.arrow(B, A, curve=55, r1=r, r2=r, color=INK, sw=2.2)
    s.arrow(B, Bad, r1=r, r2=r, color=RED, sw=2.2)

    s.node(*A, r, PAPER, GREEN, "A", label_fill=INK, size=18, sw=2.4)
    s.node(*B, r, PAPER, GREEN, "B", label_fill=INK, size=18, sw=2.4)
    s.node(*Bad, r, RED, RED_DARK, "Bad", size=14, sw=2.4)
    s.text(A[0], A[1] + 58, "安全", size=13, fill=MUTED, anchor="middle")
    s.text(B[0], B[1] + 58, "安全", size=13, fill=MUTED, anchor="middle")
    s.text(Bad[0], Bad[1] + 62, "违反安全", size=13, fill=RED, anchor="middle")

    s.text(80, 330, "A、B 可以一直打转，但 B 有一条边到 Bad——所以 A、B 都不在 I* 里。",
           size=13.5, fill=MUTED)
    s.save("safety-example")




# ---------------------------------------------------------------- CTL paths
def fig_ctl():
    h = 400
    s = SVG(W, h)
    kicker(s, "CTL / PATHS")
    title(s, "EF 与 AF：一条路，还是所有路",
          "同一个状态图，换一个路径量词，答案就不同")

    def panel(x0, mode):
        s.text(x0 + 20, 162, mode, size=20, fill=INK, weight="700")
        ok = (mode == "EF G")
        badge = (GREEN, "✓ 成立") if ok else (RED, "✗ 不成立")
        s.text(x0 + 330, 162, badge[1], size=14, fill=badge[0],
               anchor="end", weight="700")

        R = (x0 + 195, 215)
        Gp = (x0 + 105, 305)
        Sp = (x0 + 285, 305)
        s.arrow((R[0] - 12, R[1] + 16), (Gp[0] + 12, Gp[1] - 16),
                color=GREEN, sw=2.2)
        s.arrow((R[0] + 12, R[1] + 16), (Sp[0] - 12, Sp[1] - 16),
                color=(MUTED if ok else RED), sw=2.2)
        s.arrow((Sp[0] + 6, Sp[1] - 16), (R[0] + 20, R[1] + 8),
                curve=34, color=(MUTED if ok else RED), sw=1.6, dash="4 5")
        s.text(x0 + 292, 258, "…", size=18, fill=(MUTED if ok else RED))

        s.circle(*R, 22, fill=PAPER, stroke=INK, sw=2)
        s.text(R[0], R[1] + 6, "R", size=16, fill=INK, anchor="middle", weight="600")
        s.circle(*Gp, 22, fill=GREEN, stroke=GREEN, sw=2)
        s.text(Gp[0], Gp[1] + 6, "G", size=16, fill="#FFFFFF", anchor="middle", weight="600")
        s.circle(*Sp, 22, fill=PAPER, stroke=(MUTED if ok else RED), sw=2)
        s.text(Sp[0], Sp[1] + 6, "S", size=16, fill=INK, anchor="middle", weight="600")

        note = "存在一条路到 G" if ok else "有一条路永远到不了 G"
        s.text(x0 + 20, 360, note, size=14, fill=badge[0])

    panel(40, "EF G")
    panel(470, "AF G")
    s.save("ctl-paths")


if __name__ == "__main__":
    for f in (fig_open, fig1, fig_temporal, fig2, fig3, fig_safety, fig_ctl, fig4, fig5, cover):
        f()
