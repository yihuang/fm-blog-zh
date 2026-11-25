#!/usr/bin/env python3
"""Generate the figures for the separation-logic / Iris article.

Reuses the SVG helper and palette from ai.py so both articles look the same.
Run from the repository root:  python3 figures/sl.py
"""
import os
import sys

from ai import (SVG, W, PAPER, PANEL, INK, MUTED, LINE, BLUE, BLUE_DARK,
                BLUE_LIGHT, SKY, RED, RED_DARK, RED_LIGHT, GREEN, AMBER,
                AMBER_LIGHT, SANS, SERIF, MONO, kicker, title, panel, chip)


def tw(s, size):
    """Rough text width, in px: CJK is square, ASCII about half."""
    w = 0.0
    for ch in s:
        w += size * (0.56 if ord(ch) < 0x2500 else 1.0)
    return w


def fitted_chip(s, x, y, w, h, txt, size=13, **kw):
    if tw(txt, size) > w - 14:
        print(f"  ! chip too narrow ({tw(txt, size):.0f} > {w - 14:.0f}): {txt}")
    chip(s, x, y, w, h, txt, size=size, **kw)


def cell(s, x, y, w, h, label, fill=SKY, stroke=BLUE, tcol=BLUE_DARK, size=12,
         dashed=False):
    s.rect(x, y, w, h, rx=8, fill=fill, stroke=stroke, sw=1.5,
           dash="5 4" if dashed else None)
    s.text(x + w / 2, y + h / 2 + size * 0.36, label, size=size, fill=tcol,
           anchor="middle", weight="600", family=MONO)


# ------------------------------------------------------------------ 01
def fig_split():
    s = SVG(W, 500)
    kicker(s, "01 · 整块与两半")
    title(s, "∧ 共享一个堆，∗ 把它切成两半",
          "断言不再描述“整个状态”，而是描述“状态的一块”")

    # left: conjunction over one heap
    panel(s, 40, 148, 380, 250)
    s.text(58, 176, "逻辑与：同一个堆，两件事都成立", size=12.5, fill=MUTED, weight="600")
    for i, a in enumerate(["x", "y", "z", "w"]):
        cell(s, 66 + i * 84, 200, 70, 46, f"{a} ↦ {i}")
    # a bracket under the heap
    s.line((66, 268), (394, 268), color=LINE, sw=1.6)
    s.line((66, 268), (66, 276), color=LINE, sw=1.6)
    s.line((394, 268), (394, 276), color=LINE, sw=1.6)
    s.text(230, 296, "整个堆 h", size=12.5, fill=INK, anchor="middle", weight="600")
    s.text(230, 326, "P ∧ Q：两句话都必须由这同一个 h 满足", size=11.5, fill=MUTED,
           anchor="middle")
    s.text(230, 348, "谁写了哪个格子？规格说不出来", size=11.5, fill=MUTED,
           anchor="middle")
    s.text(230, 378, "于是每加一个格子，规格都要重写", size=11.5, fill=MUTED,
           anchor="middle")

    # right: separating conjunction
    panel(s, 480, 148, 380, 250)
    s.text(498, 176, "分离合取：堆被切成互不相交的两半", size=12.5, fill=MUTED,
           weight="600")
    for i, a in enumerate(["x", "y"]):
        cell(s, 500 + i * 82, 200, 70, 46, f"{a} ↦ {i}")
    for i, a in enumerate(["z", "w"]):
        cell(s, 686 + i * 74, 200, 64, 46, f"{a} ↦ {i}",
             fill="#EFE7D8", stroke=RED, tcol=RED_DARK)
    s.text(543, 274, "P", size=15, fill=BLUE_DARK, anchor="middle", weight="700",
           family=MONO)
    s.text(718, 274, "Q", size=15, fill=RED, anchor="middle", weight="700",
           family=MONO)
    s.text(670, 318, "h = h1 + h2", size=13, fill=INK, anchor="middle",
           weight="600", family=MONO)
    s.text(670, 344, "两半不相交，合起来才是整个堆", size=11.5, fill=MUTED,
           anchor="middle")
    s.text(670, 378, "各说各的那一半，互不知道对方存在", size=11.5, fill=MUTED,
           anchor="middle")

    s.rect(40, 424, 820, 62, rx=14, fill="#F6F1E7", stroke="#E4D9C6", sw=1.2)
    s.text(60, 452, "h ⊨ P ∧ Q", size=13.5, fill=BLUE_DARK, family=MONO)
    s.text(176, 452, "iff  h ⊨ P 且 h ⊨ Q：同一个 h，两句话都说整个堆", size=13.5, fill=INK)
    s.text(60, 476, "h ⊨ P ∗ Q", size=13.5, fill=RED, family=MONO)
    s.text(176, 476, "iff  h = h1 + h2，h1 ⊨ P，h2 ⊨ Q：各说各的那一半", size=13.5, fill=INK)
    s.save("sl-01-split")


# ------------------------------------------------------------------ 02
def fig_small():
    s = SVG(W, 540)
    kicker(s, "02 · 小公理与框架规则")
    title(s, "只说自己碰过的那几个格子", "剩下的世界，交给一条规则统一处理")

    s.text(240, 158, "小公理", size=12.5, fill=MUTED, anchor="middle", weight="700",
           spacing=2)
    fitted_chip(s, 70, 180, 340, 54, "{x ↦ _}\u00A0\u00A0x := v\u00A0\u00A0{x ↦ v}",
                fill=SKY, stroke=BLUE, tcol=BLUE_DARK, size=12.5)
    s.text(240, 258, "恰好一个格子：不多说一个字", size=11.5, fill=MUTED,
           anchor="middle")
    cell(s, 208, 282, 64, 42, "_", size=13, dashed=True)

    s.arrow((404, 296), (486, 296), color=BLUE, sw=2.2, r1=6, r2=6)
    s.text(445, 282, "框住", size=13, fill=BLUE, anchor="middle", weight="700")
    s.text(445, 318, "R", size=13, fill=BLUE, anchor="middle", family=MONO)

    s.text(660, 158, "框住的版本", size=12.5, fill=MUTED, anchor="middle",
           weight="700", spacing=2)
    fitted_chip(s, 500, 180, 360, 54, "{x ↦ _ ∗ R}\u00A0x := v\u00A0{x ↦ v ∗ R}",
                fill=PANEL, stroke=RED, tcol=RED, size=12)
    s.text(682, 258, "R 的格子：一个字都不许动", size=11.5, fill=MUTED,
           anchor="middle")
    cell(s, 538, 282, 64, 42, "_", size=13)
    for i, a in enumerate(["a", "b", "c"]):
        cell(s, 628 + i * 66, 282, 56, 42, "?", fill="#EFE7D8", stroke=RED,
             tcol=RED_DARK, size=13)

    s.rect(40, 372, 820, 148, rx=14, fill="#F6F1E7", stroke="#E4D9C6", sw=1.2)
    s.text(60, 400, "框架规则（frame rule）", size=12.5, fill=MUTED, weight="700",
           spacing=2)
    s.text(64, 434, "{P}  c  {Q}", size=15, fill=INK, family=MONO)
    s.text(300, 434, "前提：c 不改 R 里出现的程序变量", size=11.5, fill=MUTED)
    s.line((64, 450), (420, 450), color=INK, sw=1.2)
    s.text(64, 482, "{P ∗ R}  c  {Q ∗ R}", size=15, fill=RED, family=MONO)
    s.text(300, 482, "R 原样挂在两边，不需要额外证明", size=11.5, fill=MUTED)
    s.text(64, 508, "一条规则，替代了每个规格里那句“其余不变”。", size=11.5,
           fill=MUTED)
    s.save("sl-02-small-axioms")


# ------------------------------------------------------------------ 03
def fig_locality():
    s = SVG(W, 470)
    kicker(s, "03 · 局部性")
    title(s, "机器是局部的，框架规则才成立",
          "在更大的堆里跑，结果 = 原来的结果 + 原封不动的 R")

    s.text(96, 200, "h", size=11.5, fill=MUTED, anchor="end", family=MONO)
    s.text(120, 156, "① 小堆里跑", size=12, fill=MUTED, weight="600", spacing=1.6)
    for i, (a, v) in enumerate([("x", 0), ("y", 1)]):
        cell(s, 120 + i * 92, 170, 86, 46, f"{a} ↦ {v}", size=13)
    s.text(330, 200, "→*  e′", size=13, fill=MUTED, family=MONO)

    s.arrow((150, 226), (150, 268), color=MUTED, sw=1.8, r1=4)
    s.text(164, 252, "同一段代码", size=11, fill=MUTED)

    s.text(96, 344, "h + R", size=11.5, fill=MUTED, anchor="end", family=MONO)
    s.text(120, 300, "② 大堆里跑", size=12, fill=MUTED, weight="600", spacing=1.6)
    for i, (a, v) in enumerate([("x", 0), ("y", 1)]):
        cell(s, 120 + i * 92, 314, 86, 46, f"{a} ↦ {v}", size=13)
    s.rect(322, 302, 386, 82, rx=10, fill="none", stroke=RED, sw=1.4, dash="6 5")
    for i in range(3):
        cell(s, 340 + i * 74, 312, 62, 44, "?", fill="#EFE7D8", stroke=RED,
             tcol=RED_DARK, size=13)
    s.text(515, 376, "R：一个字节都没变", size=12, fill=RED, anchor="middle")
    s.text(726, 344, "→*  e′ + R", size=12.5, fill=MUTED, anchor="start",
           family=MONO)

    s.rect(40, 400, 820, 50, rx=14, fill="#F6F1E7", stroke="#E4D9C6", sw=1.2)
    s.text(60, 431, "这就是“局部”：程序只看得见自己的 footprint，容器变大不改变它的行为。",
           size=13, fill=INK)
    s.save("sl-03-locality")


# ------------------------------------------------------------------ 04
def fig_parallel():
    s = SVG(W, 560)
    kicker(s, "04 · 并发")
    title(s, "不相交，就不相扰", "两条规格各管一半堆，合起来就是并行")

    panel(s, 40, 146, 390, 216)
    s.text(58, 174, "互不相交", size=12.5, fill=GREEN, weight="700", spacing=1.6)
    cell(s, 66, 196, 66, 44, "x ↦ _")
    cell(s, 158, 196, 66, 44, "y ↦ _")
    s.arrow((99, 256), (99, 288), color=MUTED, sw=1.6)
    s.arrow((191, 256), (191, 288), color=MUTED, sw=1.6)
    s.text(133, 316, "各写各的格子，任何交错都一样", size=11.5, fill=MUTED,
           anchor="middle")
    s.text(58, 346, "P1 ∗ P2 可满足：两半真的能拼起来", size=11, fill=GREEN,
           family=MONO)

    panel(s, 470, 146, 390, 216)
    s.text(488, 174, "同一格，两份所有权", size=12.5, fill=RED, weight="700",
           spacing=1.6)
    cell(s, 496, 196, 66, 44, "x ↦ _", fill="#EFE7D8", stroke=RED, tcol=RED_DARK)
    cell(s, 580, 196, 66, 44, "x ↦ _", fill="#EFE7D8", stroke=RED, tcol=RED_DARK)
    s.line((506, 202), (636, 236), color=RED_DARK, sw=2)
    s.line((636, 202), (506, 236), color=RED_DARK, sw=2)
    s.text(672, 212, "x ↦ _  ∗  x ↦ _", size=11.5, fill=RED, family=MONO)
    s.text(672, 236, "不可满足", size=12, fill=RED_DARK, weight="700")
    s.text(665, 316, "竞态不是“要小心”，是前提本身就假", size=11.5, fill=MUTED,
           anchor="middle")
    s.text(488, 346, "通过验证的程序不可能有数据竞争", size=11, fill=RED_DARK,
           family=MONO)

    s.rect(40, 396, 820, 132, rx=14, fill="#F6F1E7", stroke="#E4D9C6", sw=1.2)
    s.text(66, 428, "{P1} c1 {Q1}", size=14.5, fill=INK, family=MONO)
    s.text(300, 428, "{P2} c2 {Q2}", size=14.5, fill=INK, family=MONO)
    s.line((66, 446), (462, 446), color=INK, sw=1.2)
    s.text(66, 478, "{P1 ∗ P2}  c1 ∥ c2  {Q1 ∗ Q2}", size=14.5, fill=RED,
           family=MONO)
    s.text(500, 424, "两条线程的 footprint 互不相交，", size=11.5, fill=MUTED)
    s.text(500, 448, "各自独立验证就够了。", size=11.5, fill=MUTED)
    s.text(500, 476, "交错不必枚举：没有一条能碰到对方。", size=11.5, fill=MUTED)
    s.save("sl-04-parallel")


# ------------------------------------------------------------------ 05
def fig_ghost():
    s = SVG(W, 540)
    kicker(s, "05 · 幽灵状态")
    title(s, "资源不一定是格子", "只要它能“相加”，就能被 own 起来")

    panel(s, 40, 146, 400, 234)
    s.text(58, 174, "资源代数：偏交换幺半群 + 有效性", size=12, fill=MUTED,
           weight="600")
    cell(s, 68, 196, 62, 44, "a", size=14)
    s.text(146, 224, "·", size=18, fill=INK, anchor="middle", weight="700")
    cell(s, 164, 196, 62, 44, "b", size=14)
    s.arrow((236, 218), (280, 218), color=MUTED, sw=1.8, r1=4, r2=4)
    cell(s, 292, 196, 84, 44, "a · b", size=14, fill=PANEL, stroke=GREEN,
         tcol=GREEN)
    s.text(58, 276, "✓ a", size=13, fill=GREEN, family=MONO)
    s.text(102, 276, "两半能不能同时存在？", size=11.5, fill=MUTED)
    s.text(58, 306, "own γ a ∗ own γ b  ⊣⊢  own γ (a · b)", size=12, fill=INK,
           family=MONO)
    s.text(58, 336, "合并由 ⋅ 给出；有效性由 ✓ 检查。", size=11.5, fill=MUTED)
    s.text(58, 360, "资源从不进堆，只随证明流动。", size=11.5, fill=MUTED)

    panel(s, 480, 146, 380, 252)
    s.text(498, 174, "四种常用的资源", size=12, fill=MUTED, weight="600")
    rows = [("Auth ● / ◯", "权威一份、片段多份：协议", BLUE),
            ("Frac q", "分数：读可复制，写唯一", GREEN),
            ("Excl", "独占：只能发一次", RED),
            ("Agree", "一致：所有副本必须相等", AMBER)]
    for i, (name, note, col) in enumerate(rows):
        y = 192 + i * 44
        s.rect(496, y, 348, 36, rx=8, fill=PANEL, stroke=LINE, sw=1.1)
        s.text(510, y + 23, name, size=11.5, fill=col, family=MONO, weight="600")
        s.text(612, y + 23, note, size=11, fill=INK)
    s.text(498, 386, "都是 camera（CMRA）：带步进结构的资源代数", size=11, fill=MUTED)

    s.rect(40, 404, 820, 46, rx=14, fill="#F6F1E7", stroke="#E4D9C6", sw=1.2)
    s.text(60, 433, "own γ a：我持有资源 a（γ 是幽灵名）。它不在堆里，但和堆一样能被 ∗ 切分。",
           size=12.5, fill=INK)
    s.save("sl-05-ghost")


# ------------------------------------------------------------------ 06
def fig_invariant():
    s = SVG(W, 560)
    kicker(s, "06 · 不变式与 later")
    title(s, "把资源借出去，只准原子地拿回来",
          "inv N P：一个永远成立的盒子，打开要付一次视图更新")

    s.rect(330, 158, 240, 112, rx=14, fill=PANEL, stroke=BLUE, sw=2)
    s.text(450, 194, "inv N P", size=17, fill=BLUE_DARK, anchor="middle",
           weight="700", family=MONO)
    s.text(450, 220, "永远成立；不属于任何人", size=11, fill=MUTED, anchor="middle")
    s.text(450, 242, "□ 可复制，任意线程都能拿", size=11, fill=MUTED,
           anchor="middle")

    # take out (left, upper)
    s.arrow((326, 200), (222, 200), color=RED, sw=1.9, r1=8, r2=10)
    s.text(272, 186, "|={E, E∖N}=>", size=10.5, fill=RED, anchor="middle",
           family=MONO)
    s.rect(96, 176, 116, 48, rx=10, fill="#EFE7D8", stroke=RED, sw=1.5)
    s.text(154, 206, "▷ P", size=15, fill=RED_DARK, anchor="middle",
           weight="700", family=MONO)
    s.text(96, 250, "取出来的只是 ▷P", size=11, fill=RED)

    # put back (left, lower)
    s.arrow((222, 300), (326, 300), color=BLUE, sw=1.9, r1=10, r2=8)
    s.text(272, 330, "|={E∖N, E}=>", size=10.5, fill=BLUE, anchor="middle",
           family=MONO)
    s.text(96, 330, "原样还回去", size=11, fill=BLUE)
    s.text(96, 350, "才关得上盒子", size=11, fill=BLUE)

    # later ladder
    s.text(660, 176, "为什么要晚一步", size=12, fill=MUTED, weight="600")
    s.text(660, 206, "第 n 步", size=11, fill=MUTED)
    s.rect(724, 190, 110, 32, rx=7, fill=SKY, stroke=BLUE, sw=1.2)
    s.text(779, 211, "P", size=12, fill=BLUE_DARK, anchor="middle", family=MONO)
    s.text(660, 252, "第 n+1 步", size=11, fill=MUTED)
    s.rect(724, 236, 110, 32, rx=7, fill="#EFE7D8", stroke=RED, sw=1.2)
    s.text(779, 257, "▷ P", size=12, fill=RED_DARK, anchor="middle", family=MONO)
    s.line((724, 222), (724, 236), color=MUTED, sw=1.2)
    s.text(660, 300, "P 可以再次提到 inv N P 自己，", size=11, fill=MUTED)
    s.text(660, 320, "所以打开后拿到的只能是“下一步的 P”，", size=11, fill=MUTED)
    s.text(660, 340, "否则这个定义不是良基的不动点。", size=11, fill=MUTED)

    s.rect(40, 376, 820, 74, rx=14, fill="#F6F1E7", stroke="#E4D9C6", sw=1.2)
    s.text(60, 404, "打开：把 P 拿出来用；关闭：原样放回去。这在别的线程看来是原子的——", size=12.5,
           fill=INK)
    s.text(60, 432, "中间状态没人看得见，掩码 E∖N 保证你自己也不能重入。", size=12.5,
           fill=INK)

    s.rect(40, 466, 820, 46, rx=12, fill=PANEL, stroke=LINE, sw=1.1)
    s.text(60, 495, "每一步发一张 £（later credit），开一次盒子花一张：账目对得上，循环就骗不了它。",
           size=11.5, fill=MUTED)
    s.save("sl-06-invariant")


# ------------------------------------------------------------------ 07
def fig_wp():
    s = SVG(W, 570)
    kicker(s, "07 · 最弱前置条件")
    title(s, "WP 是被定义出来的", "一个守卫递归的不动点，而不是一组公理")

    fitted_chip(s, 340, 150, 220, 54, "WP e  {{ Φ }}", fill=SKY, stroke=BLUE,
                tcol=BLUE_DARK, size=15)
    s.arrow((450, 208), (450, 246), color=MUTED, sw=1.8, r1=4)
    s.text(462, 234, "按 e 是不是值分两支", size=10.5, fill=MUTED)

    panel(s, 40, 256, 380, 186)
    s.text(58, 282, "e 是值 v", size=12, fill=MUTED, weight="600")
    fitted_chip(s, 66, 300, 328, 48, "|={E}=> Φ v", fill=PANEL, stroke=GREEN,
                tcol=GREEN, size=13)
    s.text(58, 382, "没有步可走：直接把后置条件交出来", size=11, fill=MUTED)
    s.text(58, 404, "（视图更新允许先做一次幽灵改写）", size=11, fill=MUTED)

    panel(s, 480, 256, 380, 186)
    s.text(498, 282, "e 不是值", size=12, fill=MUTED, weight="600")
    s.text(496, 306, "∀ σ, stateInterp σ ={E,∅}=∗", size=10, fill=INK,
           family=MONO)
    s.text(496, 326, "⌜可归约⌝ ∗ ∀ e′ σ′, ⌜(e,σ) → (e′,σ′)⌝ -∗", size=10,
           fill=INK, family=MONO)
    s.text(496, 346, "£ (n+1) ={∅}▷=∗ WP e′ {{Φ}}", size=10, fill=RED,
           family=MONO)
    s.text(498, 380, "先证明它不会卡住，再对每一步递归", size=11, fill=MUTED)
    s.text(498, 402, "▷ 把递归挡在下一步之后", size=11, fill=MUTED)

    s.rect(40, 466, 820, 74, rx=14, fill="#F6F1E7", stroke="#E4D9C6", sw=1.2)
    s.text(60, 494, "adequacy：若 ⊢ WP e {{ v. ⌜φ v⌝ }}，则 e 从空堆出发永不卡住，", size=12.5,
           fill=INK)
    s.text(60, 522, "且任何终值 v 都满足 φ。这条定理把逻辑接回操作语义。", size=12.5,
           fill=INK)
    s.save("sl-07-wp")


# ------------------------------------------------------------------ 08
def fig_stack():
    s = SVG(W, 540)
    kicker(s, "08 · iris-lean")
    title(s, "同一套结构，换一个证明助手",
          "从 Rocq 的 Ltac 与 canonical structures，到 Lean 4 的宏与 typeclass")

    layers = [
        ("Lean 4 + Mathlib", "内核、宏、simp、代数与概率", MUTED, "#F2EDE3"),
        ("COFE / OFE / camera", "商类型 + Leibniz 相等", GREEN, "#EAF1EC"),
        ("IProp GF", "步进索引；GF 是资源代数的槽", BLUE_DARK, SKY),
        ("WP + 不变式 + later credits", "由 wp.pre 的不动点定义", BLUE, SKY),
        ("HeapLang 与规则", "hl(λ x, ...)，wp_load、wp_cmpxchg", BLUE, SKY),
        ("MoSeL 证明模式", "对任意 BI 都成立的证明搜索", BLUE, SKY),
        ("你的证明", "iintro / iinv / wp_load / imod", RED, "#EFE7D8"),
    ]
    y = 500
    for name, note, col, fill in layers:
        s.rect(40, y - 40, 520, 36, rx=9, fill=fill, stroke=col, sw=1.3)
        s.text(56, y - 17, name, size=12, fill=col, weight="700")
        s.text(306, y - 17, note, size=10.5, fill=MUTED)
        y -= 42

    s.text(600, 176, "换到 Lean 之后的三处改动", size=12, fill=MUTED,
           weight="600")
    notes = [
        ("Leibniz OFE", "OFE 里没有 dist / equiv，", "非 Leibniz 的用商类型"),
        ("集合式量化", "sForall : (PROP → Prop) → PROP", "绕开宇宙不一致"),
        ("typeclass", "取代 canonical structures", "合成行为仍在打磨"),
    ]
    for i, (h, a, b) in enumerate(notes):
        yy = 198 + i * 92
        s.rect(590, yy, 270, 76, rx=10, fill=PANEL, stroke=LINE, sw=1.1)
        s.text(606, yy + 24, h, size=11.5, fill=RED, weight="700", family=MONO)
        s.text(606, yy + 46, a, size=10.5, fill=INK)
        s.text(606, yy + 64, b, size=10.5, fill=MUTED)

    s.text(600, 486, "十万行 Lean，从一篇硕士论文长出来", size=11, fill=MUTED)
    s.save("sl-08-iris-lean")


# ------------------------------------------------------------------ 09
def fig_pipeline():
    s = SVG(W, 560)
    kicker(s, "09 · 从代码到定理")
    title(s, "怎么把一段代码变成一条定理", "六步；卡住的地方通常在第三步或第四步")

    steps = [
        ("缩成核心", "去掉 I/O、错误处理、日志，只留共享状态与同步原语"),
        ("列出共享状态", "每一项写清楚：谁拥有它，什么时候转移"),
        ("写不变式", "每个锁、每个共享结构一条；写不出来，就是还没想清楚"),
        ("找幽灵状态", "计数、版本号、协议阶段——那些不在内存里的资源"),
        ("写原子规格", "is_xxx 抽象谓词把内部藏起来，外面只露三元组"),
        ("证", "先证顺序部分，再证并发；剩下的是体力活"),
    ]
    y = 168
    for i, (name, note) in enumerate(steps, 1):
        s.circle(80, y, 17, fill=PANEL, stroke=BLUE, sw=1.6)
        s.text(80, y + 5, str(i), size=12, fill=BLUE_DARK, anchor="middle",
               weight="700", family=MONO)
        s.text(112, y + 1, name, size=13.5, fill=INK, weight="700")
        s.text(112, y + 24, note, size=11.5, fill=MUTED)
        if i < len(steps):
            s.line((80, y + 19), (80, y + 39), color=LINE, sw=1.6)
        y += 52

    panel(s, 560, 146, 300, 306)
    s.text(578, 174, "常见的三个卡点", size=12, fill=MUTED, weight="600", spacing=1.4)
    blocks = [
        ("不变式写不出来", "你还没想清楚谁拥有什么。", RED),
        ("幽灵状态对不上", "协议里有一个「数」没被建模。", AMBER),
        ("证到一半卡住", "先退回去证顺序版本，再拆并发。", BLUE),
    ]
    for i, (h, note, col) in enumerate(blocks):
        yy = 196 + i * 82
        s.text(578, yy, h, size=12, fill=col, weight="700")
        s.text(578, yy + 22, note, size=11, fill=INK)

    s.rect(40, 480, 820, 56, rx=14, fill="#F6F1E7", stroke="#E4D9C6", sw=1.2)
    s.text(60, 505, "流水线的产物不是代码，是一条定理：它能被审查、被复用、被推翻。", size=13,
           fill=INK)
    s.text(60, 527, "「这段代码是安全的」于是变成一条有前提、有后置条件、可以被别人检查的命题。", size=13,
           fill=INK)
    s.save("sl-09-pipeline")


# ------------------------------------------------------------------ cover
def cover():
    s = SVG(W, 500)
    s.text(60, 54, "形式化笔记 · 程序逻辑", size=13, fill=BLUE, spacing=2.6,
           weight="700")
    s.text(60, 164, "分离逻辑", size=64, fill=INK, weight="700")
    s.text(60, 234, "把世界切成两半", size=42, fill=INK, weight="700")
    s.line((60, 262), (330, 262), color=BLUE, sw=3)
    s.text(60, 300, "∧ 共享一个堆，∗ 把它切开", size=17, fill=MUTED)
    s.text(60, 328, "不相交，就不相扰", size=17, fill=MUTED)
    s.text(60, 356, "剩下的，交给不变式与幽灵状态", size=17, fill=MUTED)
    s.text(60, 436, "从 Reynolds 的 ∗ 到 Iris 与 iris-lean", size=13, fill=MUTED)
    s.text(60, 462, "附一段可运行的交错枚举，和真实的 Iris-Lean 代码", size=12.5,
           fill=MUTED)

    s.rect(560, 90, 300, 340, rx=18, fill=PANEL, stroke="#E8DFCF", sw=1.2)
    s.text(710, 120, "一个堆，两块不相交的部分", size=11.5, fill=MUTED,
           anchor="middle")
    for i in range(4):
        s.rect(586 + i * 64, 150, 52, 44, rx=7, fill=SKY, stroke=BLUE, sw=1.4)
        s.text(612 + i * 64, 178, f"c{i}", size=12, fill=BLUE_DARK,
               anchor="middle", family=MONO)
    s.text(710, 222, "h", size=15, fill=INK, anchor="middle", weight="700",
           family=MONO)
    s.arrow((710, 236), (710, 268), color=MUTED, sw=1.8, r1=4)
    s.rect(570, 274, 132, 50, rx=8, fill=SKY, stroke=BLUE, sw=1.5)
    s.rect(718, 274, 132, 50, rx=8, fill="#EFE7D8", stroke=RED, sw=1.5)
    s.text(636, 306, "h1 ⊨ P", size=13, fill=BLUE_DARK, anchor="middle",
           family=MONO)
    s.text(784, 306, "h2 ⊨ Q", size=13, fill=RED, anchor="middle", family=MONO)
    s.text(710, 356, "h = h1 + h2", size=12.5, fill=INK, anchor="middle",
           family=MONO)
    s.text(710, 386, "P ∗ Q", size=17, fill=RED, anchor="middle", weight="700",
           family=MONO)
    s.save("sl-cover")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    for fn in (fig_split, fig_small, fig_locality, fig_parallel, fig_ghost,
               fig_invariant, fig_wp, fig_stack, fig_pipeline, cover):
        fn()
