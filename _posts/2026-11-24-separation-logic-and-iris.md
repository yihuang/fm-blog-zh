---
layout: post
title: "分离逻辑：把世界切成两半"
subtitle: "从 ∗ 到 Iris 与 iris-lean：局部推理的第一性原理"
description: 写给软件工程师的分离逻辑与 Iris 科普：从框架问题、小公理与框架规则讲起，到并发、幽灵状态、不变式与 later，再到最弱前置条件为什么是“定义”而不是“公理”，最后读一段 Lean 4 里 iris-lean 的真实代码。
date: 2026-11-24 09:00:00 +0800
categories:
  - 形式化验证
tags:
  - 分离逻辑
  - Iris
  - Lean4
  - 并发
  - 幽灵状态
reading_time: 36
figure_count: 9
toc: true
cover: /images/sl-cover-card.png
image: /images/sl-cover.png
---

> 写给软件工程师。\
> 需要会读 C、知道什么是堆和指针；其余从零开始。\
> 文末有一段可运行的交错枚举，和一段真实的 Iris-Lean 代码。

<details class="toc" open markdown="1">
<summary>本文目录</summary>

* TOC
{:toc}

</details>

先看一个再普通不过的函数：

```c
void incr(int *p) { *p = *p + 1; }
```

两个线程各跑一次（两个格子都从 0 开始）。如果它们传的是两个不同的地址，`incr(&x)` 和 `incr(&y)`，那么无论怎么调度，结果都是 `x = y = 1`。如果它们传的是同一个地址，`incr(&x)` 和 `incr(&x)`，就可能丢掉一次更新——两个线程都读到 0，各自加一，各自写回 1。

代码一个字都没变。变的是两个运行**碰的内存**之间的关系：一处不相交，一处相交。

要给这件事写一条规格，你需要一种能说出「这两个运行碰的是两块不相交的内存」的语言。经典的 Hoare 逻辑说不出来：`{P} c {Q}` 里的 `P` 和 `Q` 都是关于**整个状态**的谓词，没有「这一块」的概念，也就没有「另一块不归我管」的概念。

分离逻辑（separation logic）只加了一个连接词 `∗`，意思是「这些内存可以切成互不相交的两块，一块满足左边，一块满足右边」。就这么一个连接词，让「其余部分不变」这句话第一次可以被写下来、被组合、被机器检查。

这个系列的前三篇分别讲了「永远」（[liveness 与不动点]({% post_url 2026-10-19-liveness-and-fixed-points %})）、「形状」（[拓扑学]({% post_url 2026-10-25-topology-for-computer-scientists %})）和「所有」（[抽象解释]({% post_url 2026-11-03-abstract-interpretation %})）。这一篇讲「部分」：一个程序只活在世界的一小块上，怎么把这一小块说清楚，然后让更大的世界自己拼起来。

## 一、框架问题：规格里说不出“别的地方”

先把失败写出来。

交换两个格子里的值：

```c
void swap(int *a, int *b) { int t = *a; *a = *b; *b = t; }
```

你想要的规格是：

```text
交换之后，a 里是原来 b 的值，b 里是原来 a 的值，
而且，除了 a 和 b 这两个格子，别的内存一个字节都没变。
```

用 Hoare 三元组写写看。第一版：

```text
{ a ↦ x ∧ b ↦ y }  swap  { a ↦ y ∧ b ↦ x }
```

这在真实程序里是**假**的：堆里除了 `a` 和 `b` 还有别的东西，所以左边的前提根本不成立。把它弱化成「里面有」也没用——那样后置条件只说「a 和 b 变成了什么」，对其它格子一无所知，`swap` 完全可以把别的格子擦掉，规格依然成立。

这就是**框架问题**（frame problem）：你想说的其实是「其余部分不变」，但 Hoare 逻辑的断言没有「其余」这个位置。1960 年代末，它从人工智能的行动推理里来（McCarthy 与 Hayes，1969），后来成了程序逻辑的核心麻烦：几乎所有的代码都只碰一小块内存，而所有的规格都在谈论整个状态。

有一个笨办法：在每条规格里手写「其余部分不变」。

```text
{ a ↦ x ∧ b ↦ y ∧ 其余一切 = H }
  swap
{ a ↦ y ∧ b ↦ x ∧ 其余一切 = H }
```

这样能说对了，但没法用。`H` 是什么？是整个堆。于是每条规格都要带一张堆的快照，每次函数调用都要证明调用者的堆和快照对得上；两个函数组合时，第一个的「其余」和第二个的「其余」还得对齐。规格的规模从「几个格子」变成了「整个内存」，组合的代价从「拼两块」变成了「拼整个程序」。

还有一笔别名税。`{a ↦ x ∧ b ↦ y}` 在 `a = b` 时也是可满足的（同一个格子，两个名字），所以你还得额外加上 `a ≠ b`；然后每个调用者都得证明它。别名不是边角情况，它是堆的常态。

> **冷知识**：`∗` 的祖先不是 Hoare 逻辑，而是「束蕴含」（bunched implications，O'Hearn 与 Pym，1999）。那里的「束」是一棵上下文树，树叶可以按不同方式组合；堆的不相交并，恰好是这棵树的一种解释。

## 二、让断言只说一半

修法的方向很清楚：**别让断言描述整个状态，让它描述状态的一块。**

先把堆定下来。堆是一个有限的部分映射：

```text
h : Loc ⇀ Val
```

也就是说，在有限多个地址上给出值，别处没有定义。两个堆的**不相交并** `h₁ ⊎ h₂` 只在两者的定义域不相交时有定义，值取并集。这个操作有单位元（空堆），满足结合律和交换律——它是一个偏交换幺半群。这个代数结构后面会反复出现。

现在换一种断言。一个断言 `P` 不再表示「状态满足什么」，而表示**一堆满足它的堆**：

```text
⟦P⟧ ⊆ Heap
```

于是可以定义几个基本的东西：

| 断言 | 含义 |
|---|---|
| `emp` | 只有空堆满足 |
| `x ↦ v` | 只有一个格子的堆：地址 `x` 存着 `v` |
| `P ∗ Q` | 堆能切成两半，一半满足 `P`，一半满足 `Q` |
| `P -∗ Q` | 「魔法棒」：任何与当前堆不相交、且满足 `P` 的堆，拼上来都满足 `Q` |
| `⌜φ⌝` | 纯事实：`φ` 为真时任何堆都满足（不消耗内存） |

注意 `x ↦ v` 是**恰好一个格子**，不是「包含这个格子」。这个选择是整个理论的地基：只有 `↦` 是精确的，`∗` 的切分才是精确的，断言才不是「关于堆的一句话」而是「关于堆的一块的一份所有权」。

于是 `∧` 和 `∗` 的区别可以一句话说清：

| | `P ∧ Q` | `P ∗ Q` |
|---|---|---|
| 堆怎么分 | 同一个堆，两句话都说它 | 切成两半，各说各的 |
| 幂等 | `P ∧ P = P` | `P ∗ P` 通常**不可满足** |
| 别名 | 要额外证明 `a ≠ b` | 自动：`a = b` 时前提为假 |

最后一行值得停一下。`a ↦ _ ∗ b ↦ _` 在 `a = b` 时不可满足，因为一个堆没法被切成两个都以 `a` 为定义域的单点堆。所以别名问题不是「要小心处理」，而是**在前提里就不可能出现**：调用者如果传了 `a = b`，前置条件直接为假，这条规格对它什么也没承诺，它也用不上。

![∧ 共享一个堆，∗ 把它切成两半]({{ '/images/sl-01-split.png' | relative_url }})
{: .post-figure}

*图 1：左：`∧` 的两个断言争同一个堆，说不清谁写了哪个格子。右：`∗` 把堆切成不相交的两半，`P` 和 `Q` 各管一半。图上的 `+` 就是 `⊎`——不相交时才有的加法。*
{: .caption}

### 小公理

有了断言，就能给每条语句一条**只提它自己**的规格：

```text
{ x ↦ _ }   [x] := v    { x ↦ v }
{ x ↦ v }   y := [x]    { x ↦ v ∗ y = v }
{ emp }     x := alloc(v)   { x ↦ v }
{ x ↦ v }   free(x)     { emp }
```

这叫**小公理**（small axioms）。它们小到不能再小：分配只承诺一个新格子，读只承诺读出来的值，写只改一个格子。别的什么都没说。

但只有小公理是没法用的：它们太弱了，任何真实程序都在一个有别的格子的堆里跑。

### 框架规则

补上那块缺失的拼图，只需要一条规则：

```text
    {P} c {Q}          mod(c) ∩ fv(R) = ∅
    ─────────────────────────────────────
              {P ∗ R} c {Q ∗ R}
```

读作：如果 `c` 在满足 `P` 的堆上能保证 `Q`，那么在一个多出 `R` 的堆上，它照样能保证 `Q`，而 `R` 原封不动。前提是 `c` 不修改 `R` 里出现的那些**程序变量**——否则 `R` 可能被改假。

这条规则叫**框架规则**（frame rule），它是分离逻辑的全部魔法。有了它，小公理可以「长」成任意大的规格，而规格的组合变成了机械操作：证明 `swap` 只需要四步，每步一条小公理加一次框架。

![小公理与框架规则]({{ '/images/sl-02-small-axioms.png' | relative_url }})
{: .post-figure}

*图 2：上：小公理只提一个格子。下：框架规则把任意 `R` 挂在两边，`R` 不需要任何证明。*
{: .caption}

把 `swap` 推一遍。寄存器 `t`、`u` 不在堆里，`⌜⌝` 里的纯事实不占内存：

| 已经知道 | 执行 | 得到 |
|---|---|---|
| `a ↦ x ∗ b ↦ y` | `t := [a]` | `t = x ∗ a ↦ x ∗ b ↦ y` |
| `t = x ∗ a ↦ x ∗ b ↦ y` | `u := [b]` | `t = x ∗ u = y ∗ a ↦ x ∗ b ↦ y` |
| `t = x ∗ u = y ∗ a ↦ x ∗ b ↦ y` | `[a] := u` | `t = x ∗ u = y ∗ a ↦ y ∗ b ↦ y` |
| `t = x ∗ u = y ∗ a ↦ y ∗ b ↦ y` | `[b] := t` | `a ↦ y ∗ b ↦ x` |

每一步都是「小公理 + 框架」：比如第一步用的是 `{a ↦ _} t := [a] {a ↦ x ∗ t = x}`，框架 `b ↦ y` 把另一个格子带过去。四步之后，前置条件 `a ↦ x ∗ b ↦ y` 变成后置条件 `a ↦ y ∗ b ↦ x`，中间没有任何一步提到整个堆。

这就是**局部推理**：证明只沿着程序走，规格的规模跟着代码走，不跟着内存走。四个格子的程序和四百万个格子的程序，`swap` 的证明一样长。

## 三、框架规则为什么是对的：局部性

上一节把框架规则当成一条规则用了。它凭什么成立？

因为它不是逻辑的性质，是**机器**的性质。分离逻辑的框架规则等价于下面这句话：

```text
若 (e, h) →* (e′, h′)，且 h ⊎ h_R 有定义，
则 (e, h ⊎ h_R) →* (e′, h′ ⊎ h_R)。
```

也就是说：在一份更大的内存里跑同一段代码，结果就是原来的结果，加上那份从头到尾没人碰的内存。这叫**框架属性**（frame property），有时也叫**局部性**（locality）。

从它到框架规则只差一个归纳：小公理在空堆上成立，在任意扩展的堆上也成立（因为它们是「局部」的，只碰自己那几个格子）；每一步都保持；于是整个程序的证明也保持。反过来，如果机器不局部，框架规则立刻失效——你可以构造一个程序，它在小堆上老老实实，在大堆上顺手擦了旁边的格子。

所以那句话要说得更准确：**分离逻辑是给「局部语言」配的证明系统。** 局部性属于语言，不属于逻辑。

这个区分在工程上很有用。设计一门新语言、一个新的虚拟机、一个新的内存模型时，第一个该问的问题不是「怎么写规格」，而是「我的操作语义是局部的吗」：

- **有 GC 且会移动对象的语言**：`↦` 里的地址会变，`(e, h)` 和 `(e, h ⊎ h_R)` 的结果不再只差一个 `R`。要先建立两个堆之间的对应关系，框架属性才能恢复。
- **有 `free` 的语言**：没问题，因为 `free` 只释放自己拥有的那一个格子；释放之后地址不能被别人拿去用，否则「所有权」就不唯一了。这就是 iris-lean 里 `↦` 的参数是 `option` 的原因：活着的格子写 `some v`，释放之后写 `none`——地址仍然被占着，只是内容没了。
- **Rust**：借用、生命周期、`&mut` 都在挑战「只有我碰这块内存」的直觉。RustBelt 在 Iris 里给 Rust 建了一个语义模型，「一段代码只碰它借到的那块内存」于是变成了模型里的一个定理，而不是一条口头约定。

![局部性]({{ '/images/sl-03-locality.png' | relative_url }})
{: .post-figure}

*图 3：同一段代码在小堆上跑到 `e′`；在大堆上跑到 `e′`，并且 `R` 一个字节都没变。框架规则是这句话的证明论影子。*
{: .caption}

> **深水区**：更一般的说法是「局部动作」（local action，Calcagno、O'Hearn、Yang，2007）：一个程序的动作只依赖堆的一个子集，并且对扩展稳定。分离逻辑不是唯一能配这种语义的逻辑，但它是把这件事做得最顺手的一个。

## 四、并发：不相交就是不相扰

局部性在串行程序里只是省事，在并发程序里是**生死攸关**。

两条线程各自跑，调度器可以任意交错它们的指令。你要证明的性质是「不管怎么交错，都不会有线程看到半个更新」。手工做法是枚举交错，而交错的数量是指数级的。

分离逻辑给了一条规则：

```text
    {P₁} c₁ {Q₁}        {P₂} c₂ {Q₂}
    ───────────────────────────────────
       {P₁ ∗ P₂}  c₁ ∥ c₂  {Q₁ ∗ Q₂}
```

读作：如果两条线程各自能从自己的那半堆出发、保证自己的后置条件，那么把它们**不相交地**拼起来跑，就能保证两半的后置条件同时成立。

（在教科书里还要加一条技术条件：`c₁` 不能改 `c₂` 规格里出现的变量。Iris 里这条消失了——程序变量不可变，可变的东西全在堆里。）

这里有个容易被忽略的细节：规则里没有「假设它们不竞争」这一条。**竞争根本写不出来。** 如果两条线程都要写 `x`，它们的前提就必须是 `x ↦ _ ∗ x ↦ _`，而这个断言不可满足。所以：

- 一个通过了验证的程序，**不可能有数据竞争**——这不是额外证明的定理，是前提的副作用；
- 反过来说，`↦` 不是一个「关于格子的陈述」，而是一张**所有权凭证**。拿着它，你才能读写那个格子；同一张凭证不能有两个人拿。

这就是「资源」这个词的由来。分离逻辑后来被叫作资源逻辑，不是修辞：断言在说「我手里有哪些资源」，`∗` 在说「资源可以分开持有」。

![并发：不相交就不相扰]({{ '/images/sl-04-parallel.png' | relative_url }})
{: .post-figure}

*图 4：左：两块不相交的所有权，任何交错都不会交叉。右：同一个格子的两份所有权不可满足——竞态在前提层面就被排除了。*
{: .caption}

### 用枚举验一下

理论说得再顺，也不如跑一遍。下面这段程序不证明任何东西，它只做一件事：把两个线程的所有交错枚举出来，看看结局有几种。

```python
def incr(p, reg):                      # 一个线程做的事：读、加、写回
    return [("load", p, reg), ("add", reg, 1), ("store", p, reg)]

def schedules(threads):
    """枚举所有保序交错：每一步选一个线程走一条指令。"""
    def go(done, acc):
        if all(d == len(t) for d, t in zip(done, threads)):
            yield list(acc); return
        for i, t in enumerate(threads):
            if done[i] < len(t):
                acc.append((i, t[done[i]]))
                done[i] += 1
                yield from go(done, acc)
                done[i] -= 1
                acc.pop()
    yield from go([0] * len(threads), [])

def execute(threads, sched, heap):
    heap, regs = dict(heap), {}
    for i, (kind, a, b) in sched:
        if kind == "load":  regs[b] = heap.get(a, 0)
        if kind == "add":   regs[a] += b
        if kind == "store": heap[a] = regs[b]
    return heap

for name, threads in [("incr(&x) ∥ incr(&y)", [incr("x", "r1"), incr("y", "r2")]),
                      ("incr(&x) ∥ incr(&x)", [incr("x", "r1"), incr("x", "r2")])]:
    ss = list(schedules(threads))
    finals = {tuple(sorted(execute(threads, s, {"x": 0, "y": 0}).items())) for s in ss}
    print(f"{name}: {len(ss)} 种交错，{len(finals)} 种结局")
    for f in sorted(finals):
        print("   ", dict(f))
```

输出：

```text
incr(&x) ∥ incr(&y): 20 种交错，1 种结局
    {'x': 1, 'y': 1}
incr(&x) ∥ incr(&x): 20 种交错，2 种结局
    {'x': 1, 'y': 0}
    {'x': 2, 'y': 0}
```

第一行是分离逻辑想让你相信的事：两个不相交的格子，二十种交错都给出同一个结局。第二行是它想让你避免的事：`x = 1` 的那个结局，来自这样的调度——

```text
T1 读 x，得到 0，放进 r1
T2 读 x，得到 0，放进 r2      ← 两次读都发生在任何写之前
T1 r1 := 1，写回 x
T2 r2 := 1，写回 x            ← 覆盖掉了 T1 的写
```

两次更新只留下一次。

注意这段程序的计算成本：每个线程三条指令，交错数是 `C(6,3) = 20`。每个线程 `k` 条指令，就是 `C(2k,k)`；`k = 20` 时是 1.4×10¹¹ 种。枚举是`指数`的，而分离逻辑的证明是`线性`的：两条规格，一次 `∗`，一次并行规则。**它没有变得更快，它只是不再枚举。**

## 五、幽灵状态：资源不一定是格子

到这里，分离逻辑能处理「各自一块内存」的并发了。但真实并发程序里有一大半的资源不在这张图里。

- 一把锁：两个线程要**共享**同一块资源，只是不同时。这不违反不相交，但也不符合「各有一半」。
- 一个计数器：`incr` 要用 CAS 重试，凭什么是安全的？
- 一半的读权限：两个读者可以同时读同一个格子，但只要有人写就必须独占。`↦` 只有「全有」和「全无」两档，说不出「一半」。

这三件事看起来各不相同，Iris 的答案却只有一个：**资源不一定是堆里的格子；任何能「相加」的东西都可以是资源。**

具体地说，取一个偏交换幺半群，带一个有效性谓词 `✓`：

```text
a ⋅ b        两半合起来
✓ a          a 自己站得住（能存在）
```

然后给每条资源一个名字 `γ`（幽灵名，ghost name），引入一个断言：

```text
own γ a     我持有名字 γ 下的资源 a
```

它满足两条定律：

```text
own γ a ∗ own γ b  ⊣⊢  own γ (a ⋅ b)        合并
own γ a            ⊢    ⌜✓ a⌝                有效
```

第一条说「分开持有的两半，合起来是一份」，第二条说「持有的东西必须站得住」。就这样，堆里的格子变成了一个特例：`x ↦ v` 不过是「名字是地址、资源是单点堆」的 `own`。

改写幽灵状态也只有一种方式：**保持框架的更新**（frame-preserving update）。`a` 可以改写成 `a′`，条件是任何能和 `a` 共存的 `b`，也能和 `a′` 共存。这条限制保证「我改我的资源，不会让别人的资源失效」——`Auth` 的权威份伪造不出来、`Frac` 的分数凭空加不上去，都是它的推论。

这个抽象的威力在于它把「资源」从「内存」里解放了出来。四种最常用的资源：

| 资源 | 长什么样 | 用来表达 |
|---|---|---|
| `Auth` | 一份权威 `● a` + 任意多份片段 `◯ b`，且 `b ⊑ a` | 协议：「服务端记录的版本是 3，客户端只知道 ≤ 3」 |
| `Frac` | `◯{q} v`，`q ∈ (0,1]`，两份相加不超过 1 | 权限：读权限可以复制，写权限唯一 |
| `Excl` | 只有一个元素，且只能被发一次 | 一次性令牌：「这个初始化只做一次」 |
| `Agree` | 所有片段必须相等 | 一致性：「两边看到的值必然相同」 |

数一数就会发现，前面所有的例子都能落到这几种里：锁是「一个布尔格子 + 不变式」，读权限是 `Frac`，CAS 计数器是 `Auth`（单调的那一种），一次性的初始化是 `Excl`。

![资源代数与幽灵状态]({{ '/images/sl-05-ghost.png' | relative_url }})
{: .post-figure}

*图 5：资源是一个带有效性的偏交换幺半群。`∗` 在资源层面就是 `⋅`。资源从不进堆，它只随证明流动。*
{: .caption}

> **深水区**：Iris 管这些结构叫 camera（CMRA）。名字里的「步进」不是装饰：模型是步进索引的，`▷` 是一个收缩映射，`⋅` 必须在「再看一步」的意义下与它相容。这是为了让这一节的 `own` 和下一节的 `▷` 能放进同一个逻辑。

## 六、不变式与 later：借出去的东西怎么还

回到锁。锁要解决的问题是：资源在两条线程之间**流动**，但在任何时刻只属于一条。

分离逻辑的写法是：让资源属于**锁**，而不是属于线程。

```text
inv N P
```

读作：在命名空间 `N` 里，`P` 永远成立。它不是谁的财产：`inv N P` 可以被复制任意多份，任何线程都能拿到它（Iris 里用 `□` 标记这种「持久」的断言）。代价是：**你只能在原子的意义上短暂地看见它。**

定义长这样（iris-lean，`Iris/Instances/Lib/Invariants.lean`）：

```lean
def inv (N : Namespace) (P : IProp GF) : IProp GF :=
  iprop(□ ∀ E, ⌜↑N ⊆ E⌝ → |={E, E \ ↑N}=> ▷ P ∗ (▷ P ={E \ ↑N, E}=∗ True))
```

逐段读：

- `□`：持久，可复制，不属于任何人。
- `∀ E, ⌜↑N ⊆ E⌝ →`：只要命名空间 `N` 在当前的「掩码」`E` 里（也就是它没被禁用）。
- `|={E, E \ ↑N}=>`：花一次**视图更新**（fancy update），把 `N` 从掩码里去掉——在打开期间，你自己不能再次打开它（不能重入）。
- `▷ P`：你拿到的是「下一步的 `P`」。
- `▷ P ={E \ ↑N, E}=∗ True`：还回去的凭据。交出 `▷ P`，`N` 重新启用。

打开、用、关上，对别的线程必须是**原子**的：从外面看，这几步要么全在它之前，要么全在它之后，不会插在中间。在打开的那段时间里，不变式并不成立，所以中间状态不能让任何人观察到。技术上靠两件事：掩码 `E \ ↑N` 保证打开期间 `N` 是关着的（不能重入）；`▷` 保证别的线程拿到的永远是「上一步的 `P`」。

至于那个 `▷`——为什么拿到的是「下一步」而不是 `P` 本身？

因为 `P` 可以提到这个不变式自己。锁的不变式里写着「锁是开的，并且资源 `R` 在里面」，而 `R` 里可能又包含另一把锁的不变式；一个递归的数据结构，它的不变式就是递归的。允许这种自引用，`inv N P` 的定义就成了一枚自指的方程，直接解是循环的。`▷` 把循环切断：**要谈 `P`，先走一步。**

这和类型论里的守卫递归（guarded recursion）是同一件事，许可证是 Löb 规则：

```lean
theorem loeb [BILoeb PROP] {P : PROP} : (▷ P → P) ⊢ P := by
  ...
```

「如果能从『下一步的 `P`』推出 `P`，那么 `P` 成立。」在步进索引的模型里，这就是「对步数做归纳」。

![不变式与 later]({{ '/images/sl-06-invariant.png' | relative_url }})
{: .post-figure}

*图 6：打开不变式是一次视图更新，拿到 `▷P`；关闭是反向的一次，把 `▷P` 还回去。`▷` 是自引用要付的过路费。*
{: .caption}

> **深水区**：`▷` 只保证「再走一步之后」，它不记录「还能走几步」。而 Löb 规则恰恰允许你把「下一步的目标」当成假设用；逻辑里没有任何东西阻止你无限次地这么用。于是「这个程序一定终止」这类需要数步数的性质，在只有 `▷` 的系统里说不清楚。Iris 2022 年加了 **later credits**：每条规约步发一张 `£`，用掉一个 `▷` 就得花掉一张，步数才真正被记在账上。iris-lean 也实现了它——`£` 就出现在下一节 `wp` 的定义里。

## 七、WP 是被定义的，不是被假设的

教科书里的分离逻辑是一组公理：小公理、框架规则、并行规则、不变式规则……然后有一个写在纸上的可靠性定理，说这些公理相对于某个语义是安全的。

Iris 不是这样。Iris 把整个逻辑**定义**在证明助手里：

1. 先定义一类「步进索引的命题」`IProp`，它是一个 COFE（带步进结构的完全度量空间）；
2. 用**守卫递归**定义最弱前置条件 `wp`，它是一个不动点；
3. 那些「公理」——`wp_load`、`wp_store`、`inv_acc`——全是**引理**，由定义推出来；
4. 最后用一条**充分性**（adequacy）定理，把 `wp` 和操作语义接上。

第三、四步是重点。先看 `wp` 的定义（`Iris/ProgramLogic/WeakestPre.lean`，照抄）：

```lean
def wp.pre (s : Stuckness) (wp : CoPset -> Expr -> (Val -> IProp GF) -> IProp GF) (E : CoPset)
    (e₁ : Expr) (Φ : Val -> IProp GF) : IProp GF :=
  match toVal e₁ with
  | some v => iprop(|={E}=> Φ v)
  | none => iprop(∀ (σ₁ : State) (ns : Nat) (obs obs' : List Obs) (nt : Nat),
    stateInterp σ₁ ns (obs ++ obs') nt ={E,∅}=∗
    ⌜s.MaybeReducible (e₁, σ₁)⌝ ∗
    ∀ e₂ σ₂ eₜ, ⌜(e₁, σ₁) -<obs>-> (e₂, σ₂, eₜ)⌝ -∗
      £ (ι.numLatersPerStep ns + 1) ={∅}▷=∗^[ι.numLatersPerStep ns + 1] |={∅,E}=>
      stateInterp σ₂ (ns + 1) obs' (nt + eₜ.length) ∗
      wp E e₂ Φ ∗ [∗list] e' ∈ eₜ, wp ⊤ e' ι.forkPost)
```

按 `e` 是不是一个值分两支：

- **是值 `v`**：没有步可走，直接把后置条件 `Φ v` 交出来（允许先做一次视图更新）。
- **不是值**：对任意满足 `stateInterp` 的状态，先证明 `e` 在这一步**不会卡住**；然后对每一个可能的下一步 `(e₂, σ₂)`，花掉一张 later credit `£`，在「下一步」`▷` 里，重新建立 `stateInterp`、继续 `wp e₂`、并且让所有 fork 出来的线程满足它们各自的后置条件 `[∗list]`（大分离合取）。

`stateInterp` 是**参数**。它说「当前的语言状态怎么解释成资源」。堆语言把它解释成「堆里每个格子都有一份 `↦`」，于是 `wp` 在 HeapLang 上就退化成了分离逻辑的样子；换一门语言，换一个 `stateInterp`，`wp` 一个字都不用改。这就是为什么 Iris 能同时是 C 的、Rust 的、Go 的、并发 λ 演算的逻辑。

指针 `wp` 与 `wp.pre` 的关系是「守卫不动点」：

```lean
instance wp.def : Wp (IProp GF) (Expr) (Val) Stuckness where
  wp s := fixpoint (wp.pre s)
```

`wp.pre` 对 `wp` 是收缩的（`Contractive`），所以 Banach 不动点定理给出唯一解。这就是那个 `▷` 的全部来源：递归定义要合法，就得有一个收缩的东西把它「挡一下」。

有了定义，公理就变成了引理。例如「读」的规则：从 `l ↦ v` 出发，读出 `v`，结果是 `l ↦ v ∗ w = v`——这是 `wp` 展开后走一步、再用 `stateInterp` 的内容算出来的。你不需要相信这条规则，你可以展开定义检查它。

最后是充分性。`wp` 是一个逻辑内部的谓词，它得能翻译成「程序真的不会卡住」：

{% raw %}
```text
若 ⊢ WP e {{ v. ⌜φ v⌝ }}，则 e 从初始状态出发永不卡住，
且任何终值 v 都满足 φ。
```
{% endraw %}

（严格地说，前面还要用一次视图更新把初始的 `stateInterp` 分配出来，所以定理的形式里带着 `|={⊤}=>`——这是为了让不变式和幽灵状态在开局时可以被创建。）

这条定理是整座桥的桥墩：一边是可执行的程序，一边是可证明的命题。

![WP 的定义]({{ '/images/sl-07-wp.png' | relative_url }})
{: .post-figure}

*图 7：`WP` 展开成两支：值直接交后置条件；非值先证不卡住，再对每步在 `▷` 里递归。*
{: .caption}

### 三元组是一个宏

还有一个细节值得单独说：你在 iris-lean 里看到的 {% raw %}`{{ P }} e {{ RET v; Q }}`{% endraw %} 并不是逻辑的原语，它是一段语法糖。（Rocq 版里它写作 {% raw %}`{{{ }}}`{% endraw %}，比 {% raw %}`WP e {{ Φ }}`{% endraw %} 多一层花括号；Lean 版靠语法位置区分，所以都是两层。）

它展开成这样：

{% raw %}
```text
{{ P }} e {{ RET v; Q }}   ≡   ∀ Φ, P -∗ ▷ (Q -∗ Φ v) -∗ WP e {{ Φ }}
```
{% endraw %}

{% raw %}也就是说：对任意后置条件谓词 `Φ`，给我 `P`，再给我「`Q` 能推出 `Φ v`」（晚一步给），我就还你 `WP e {{ Φ }}`。前置条件、后置条件、返回值，全是从 `wp` 的 `Φ` 里「读」出来的。{% endraw %}

{% raw %}那个 `▷` 也不是装饰：后置条件是在**下一步**被用掉的。{% endraw %}

## 八、iris-lean：同一套结构，换一个证明助手

到这里，分离逻辑的故事已经讲完了，剩下的是工程问题：这套东西怎么落到一个能用的工具上。

Rocq（原 Coq）里的 Iris 已经发展了十几年，几十位贡献者，是整个并发程序验证领域的基础设施：RustBelt、RefinedC、Perennial（Go）、λRust 都建在它上面。iris-lean 是把同一套东西搬到 Lean 4 的尝试。

**它是什么。** `leanprover-community/iris-lean`，一个 Lean 4 库。目前支持 Iris 的主要部件：`IProp` 的标准模型、MoSeL 证明模式、HeapLang 这个示例语言、不变式、later credits、一批现成的资源代数（`Auth`、`Frac`、`Excl`、`Agree`、`MonoNat`……）。`Iris/` 目录大约十万行 Lean，三百多个文件。

**它从哪来。** 2022 年，Lars König 的硕士论文（KIT）做出了最早的版本；之后由 Mario Carneiro 维护；2025 年起社区投入明显增加，2026 年进度加快。架构和 Rocq 版一一对应，所以 Rocq 版的论文、教程、直觉，大部分可以直接搬过来用。

![iris-lean 的分层]({{ '/images/sl-08-iris-lean.png' | relative_url }})
{: .post-figure}

*图 8：从 Lean 内核往上：COFE 与 camera、`IProp GF`、`wp` 与不变式、HeapLang、MoSeL 证明模式，最上面是你的证明。右边是换到 Lean 之后的三处改动。*
{: .caption}

### 搬到 Lean 之后改了什么

移植不是逐行翻译。Lean 和 Rocq 的类型系统相近（都是依赖类型论），但工程习惯差得很远，有三处改动是结构性的：

| Rocq 版 | iris-lean | 为什么 |
|---|---|---|
| OFE 带 `dist` / `equiv` 两个关系 | 只有 Leibniz 相等；需要商的时候用商类型 | 相等就是 `=`，`simp` 和 `rw` 才能正常工作 |
| 索引式量化 `∀ A, (A → PROP) → PROP` | 集合式量化 `sForall : (PROP → Prop) → PROP` | 绕开索引式量化在不同宇宙层级下的不一致 |
| canonical structures | typeclasses | Lean 没有 canonical structures；但「默认实例的急切推导」还没完全复刻 |

第一条影响最大。Iris 的整个模型建立在 COFE 上，而 COFE 的相等是「距离任意小」而不是「相等」；Rocq 版里到处都是 `≡` 和 setoid 重写。Lean 版直接规定「OFE 的相等就是 `=`」，需要非 Leibniz 相等的地方（比如 `Agree`）先用商类型商掉。代价是有些构造要额外证商是良定义的，收益是所有 Lean 的自动化都能直接用。

### 一段真实的代码

下面这些代码不是伪代码，是从 `Iris/HeapLang/Lib/Counter.lean` 里抄出来的，能编译、能跑在真实的 iris-lean 上。

先看程序：一个用 CAS 自增的计数器（`hl(&incr #l)` 是把 `l` 应用给 `incr`，`#n` 是字面量）。

{% raw %}
```lean
def incr : Val := hl_val%
  rec incr l :=
    let n := !l;
    if cas(l, n, #1 + n)
      then #()
      else incr l
```
{% endraw %}

它的不变式只有一行（`iprop%` 是把一段 Lean 语法解释成 `IProp` 的引号）：格子里的数是 `n`，幽灵状态 `A n` 记录着它。

{% raw %}
```lean
abbrev counterInv (A : Nat → IProp GF) (l : Loc) : IProp GF := iprop%
  ∃ n : Nat, A n ∗ l ↦ some hl_val(#n)
```
{% endraw %}

然后是它的规格。注意前条件里的 `∧`：不变式是**假设**，不是所有物。

{% raw %}
```lean
private theorem incr_spec {A : Nat → IProp GF} (P : IProp GF) (Q : IProp GF) (l : Loc)
    (hupd : ∀ c : Nat, iprop(A c ∗ P) ⊢ iprop(|==> (A (c + 1) ∗ Q))) :
    {{ inv N (counterInv A l) ∧ P }} hl(&incr #l) {{ RET hl_val(#()); Q }} := by
  iintro %Φ ⟨#Hinv, HP⟩ Hφ
  iloeb as IH
  wp_rec
  wp_bind !_
  iinv Hinv with ⟨%c, HA, Hl⟩ Hclose
  wp_load
  imod Hclose $$ [HA Hl] with -
  · inext; iexists c; iframe
  imodintro
  wp_pures
  wp_bind cmpXchg(_, _, _)
  iinv Hinv with ⟨%c', HA, Hl⟩ Hclose
  wp_cmpxchg with hsuc hfail
  ...
```
{% endraw %}

（省略了后面两个分支，它们各自把不变式还回去，再走剩下的证明。）

这段证明里出现了前面讲过的所有东西：

| 战术 | 它在做什么 |
|---|---|
| `iintro %Φ ⟨#Hinv, HP⟩ Hφ` | 展开三元组：引入后置条件谓词 `Φ`、不变式（`#` 表示持久）、线程自己的资源 |
| `iloeb as IH` | Löb 归纳：把「下一步能证」当成假设——因为 `incr` 是递归的 |
| `wp_rec` / `wp_load` / `wp_bind` | 按 HeapLang 的规约走一步，`bind` 把焦点移到子表达式 |
| `iinv Hinv with ⟨%c, HA, Hl⟩ Hclose` | 打开不变式：拿到数 `c`、幽灵状态 `HA`、格子 `Hl`，以及关门器 `Hclose` |
| `imod Hclose $$ [HA Hl] with -` | 用视图更新把不变式还回去，`inext` 处理那个 `▷` |
| `wp_cmpxchg with hsuc hfail` | CAS 的两个结果，各自一个分支 |
| `iapply Hφ $$ HQ` | 用后置条件收尾 |

而 `hupd` 这个参数是全篇最漂亮的地方：**计数器的协议本身是一个参数**。同一个 `incr_spec`，传 `Auth MaxNat` 就得到「单调计数器」，传 `FracAuth Nat` 就得到「带贡献的计数器」——程序推理只做一次，幽灵状态更新按需要换。

上层规格因此短得不像话：

{% raw %}
```lean
theorem incr_mono_spec (l : Loc) (n : Nat) :
    {{ mcounter (GF := GF) N l n }} hl(&incr #l) {{ RET hl_val(#()); mcounter N l (n + 1) }} := by
  ...
```
{% endraw %}

读作：如果 `l` 是一个共享的、当前值为 `n` 的计数器，那么 `incr l` 之后，它还是一个共享的计数器，值为 `n + 1`。没有说「不竞争」，因为它根本不可能竞争：共享的那一份在不变式里，只有打开不变式的那一个原子步才拿得到。

### 用它要付什么

**好处**（也是那篇 *Iris in Lean* 草稿的卖点）：商类型让相等变简单；Lean 的元编程让证明模式跑得更快；可以直接用 Mathlib——论文里拿概率程序验证做例子，因为概率、测度、代数这些基础在 Mathlib 里现成；还有自动构造 Iris 的不动点、Diaframe 风格的自动化。

**代价**：你仍然要会 Lean，会自己写资源代数，会读 `iintro` / `imod` 这些战术；十万行的库还在追赶上游十几年的积累，大规模案例研究还不多；canonical structures 的模拟、默认实例的推导还在打磨（`docs/compatibility.md` 里列着呢）。

**怎么用**：把它当依赖加进 `lakefile.toml`，`subDir = "Iris"` 即可。

```toml
[[require]]
name = "iris"
git.url = "https://github.com/leanprover-community/iris-lean.git"
git.subDir = "Iris"
rev = "master"
```

文档在 `docs/tactics.md`（战术手册）、`docs/compatibility.md`（和 Rocq 版的差异）、`docs/proofmode.md`（MoSeL）；还有一个自动生成的对照页，把 Lean 里的每个定义对到 Rocq 版。

## 九、带走一张地图

把全文压缩成一张对照表：

| 你熟悉的东西 | 分离逻辑里的名字 | 一句话 |
|---|---|---|
| 一个堆 | `Heap` | 有限部分映射 |
| “只有这个格子” | `↦` | 单点堆，不是「包含」 |
| “两半各自成立” | `∗` | 不相交的并 |
| “其余不变” | 框架规则 | 局部性的证明论影子 |
| 数据竞争 | 不可满足的 `∗` | 同一格子的两份所有权不存在 |
| 锁 | 不变式 | 借出去，只能原子地拿回来 |
| 权限 | 分数 | 读权限可复制，写权限唯一 |
| 协议 / 令牌 | 幽灵状态 | 不在堆里的资源，照样能被 `∗` 切分 |
| 步数 | `▷` 与 `£` | 守卫递归，以及它的记账单位 |
| 规格 | `WP` | 用不动点定义出来的谓词 |

如果只带走五句话：

1. **分离逻辑只加了一个连接词 `∗`，意思是「堆能切成互不相交的两半」。** 它把「其余部分不变」从每条规格里的一句话，变成了一条规则。
2. **`↦` 是单点堆，不是「包含」。** 因为精确，`∗` 才能精确地切；别名从「要证明的前提」变成了「不可满足的前提」。
3. **框架规则不是公理，是局部性的影子。** 机器局部，逻辑才健全；换语言的时候，第一个要问的是「我的语义还是局部的吗」。
4. **并发里，不相交就是不相扰。** 竞态写不出来，所以数据竞争自由是前提的副作用，不是额外要证的定理。
5. **Iris 的三样东西各管一件事：** 幽灵状态管「资源是什么」，不变式管「怎么共享」，`▷` 管「自引用怎么合法」。而 `wp` 是这三样东西上定义出来的一个不动点，不是一组要你相信的公理。

## 尾声：名字的误会

第一次听到「分离逻辑」，很容易联想到「关注点分离」（separation of concerns）。两者只有一个词的缘分。

分离逻辑分离的不是关注点，是**堆**。它说的是：世界可以切成互不相交的部分，每部分有自己的主人；一个程序只对自己那部分负责，其余部分交给别人，而「其余部分」不需要在规格里出现。

这个想法朴素得几乎不像一个理论。但正是它，让「这条线程不会碰那条线程的内存」从一句口头承诺，变成了一条可以被机器检查的前提；让「这把锁保护着那个计数器」从一张架构图，变成了一个带 `▷` 的不变式；让「这个 `incr` 是安全的」从「我看了三遍」，变成了十几行 Lean。

回到开头那两个线程。分离逻辑没有让并发变得简单——交错还是那么多，bug 还是那么难找。它只是让**「它们互不干扰」这句话第一次可以被写下来**。而在形式化方法里，能写下来，就已经走完了一半。

---

### 延伸阅读

- John C. Reynolds, “Separation Logic: A Logic for Shared Mutable Data Structures”, *LICS*, 2002（分离逻辑的起点，`∗`、框架规则、小公理都在这里）
- Samin Ishtiaq, Peter O'Hearn, “BI as an Assertion Language for Mutable Data Structures”, *POPL*, 2001
- Peter O'Hearn, “Resources, Concurrency and Local Reasoning”, *CONCUR*, 2004（并发分离逻辑）
- Stephen Brookes, “A Semantics for Concurrent Separation Logic”, *CONCUR*, 2004
- Cristiano Calcagno, Peter O'Hearn, Hongseok Yang, “Local Action and Abstract Separation Logic”, *LICS*, 2007
- Ralf Jung, David Swasey, Filip Sieczkowski, Kasper Svendsen, Aaron Turon, Lars Birkedal, Derek Dreyer, “Iris: Monoids and Invariants as an Orthogonal Basis for Concurrent Reasoning”, *POPL*, 2015
- Robbert Krebbers, Ralf Jung, Aleš Bizjak, Jacques-Henri Jourdan, Derek Dreyer, Lars Birkedal, “The Essence of Higher-Order Concurrent Separation Logic”, *ESOP*, 2017
- Ralf Jung, Robbert Krebbers, Jacques-Henri Jourdan, Aleš Bizjak, Lars Birkedal, Derek Dreyer, “Iris from the Ground Up: A Modular Foundation for Higher-Order Concurrent Separation Logic”, *Journal of Functional Programming*, 2018（最完整的教程，本文的骨架基本来自它）
- Ralf Jung, Jacques-Henri Jourdan, Robbert Krebbers, Derek Dreyer, “RustBelt: Securing the Foundations of the Rust Programming Language”, *POPL*, 2018
- Robbert Krebbers, Jacques-Henri Jourdan, Ralf Jung, Joseph Tassarotti, Jan-Oliver Kaiser, Amin Timany, Arthur Charguéraud, Derek Dreyer, “MoSeL: A General, Extensible Modal Framework for Interactive Proofs in Separation Logic”, *ICFP*, 2018
- Simon Spies, Lennard Gäher, Joseph Tassarotti, Ralf Jung, Robbert Krebbers, Lars Birkedal, “Later Credits: Resourceful Reasoning about Later in Separation Logics”, *ICFP*, 2022
- Markus de Medeiros, Sergei Stepanenko, Zongyuan Liu 等, “Iris in Lean”, 草稿，2026（[arXiv:2609.24252](https://arxiv.org/abs/2609.24252)）
- Iris 项目主页：<https://iris-project.org/>
- Iris-Lean 仓库：<https://github.com/leanprover-community/iris-lean>；Rocq 版：<https://gitlab.mpi-sws.org/iris/iris/>
