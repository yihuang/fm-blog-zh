#!/usr/bin/env python3
"""Build a self-contained reading preview from the pandoc fragment."""
import re, pathlib, subprocess, html

ROOT = pathlib.Path(__file__).resolve().parent.parent
md = ROOT / "liveness-and-fixed-points.md"
frag_path = pathlib.Path("/tmp/article-fragment.html")

subprocess.run(["pandoc", str(md), "-f", "markdown", "-t", "html5",
                "--no-highlight", "-o", str(frag_path)], check=True)
frag = frag_path.read_text(encoding="utf-8")

# subtitle -> styled subtitle + meta line (the first <p><em> after the h1)
frag = re.sub(
    r'(</h1>\s*)<p><em>(.*?)</em></p>',
    r'\1<p class="subtitle"><em>\2</em></p>\n<div class="meta">约 20 分钟 · 9 张图</div>',
    frag, count=1, flags=re.S)

# figure captions
frag = frag.replace('<p><em>图 ', '<p class="caption"><em>图 ')
frag = frag.replace('<p><em>小图', '<p class="caption"><em>小图')

kicker = '<div class="kicker">形式化验证 · 科普</div>\n'

css = r"""
:root{
  --paper:#FBF7F0; --card:#FFFDF8; --ink:#23272E; --muted:#7A7468;
  --line:#E6DCCB; --red:#BF4A32; --red-dark:#8E3324; --green:#2F7D6B;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  margin:0; padding:0; color:var(--ink); background:#F2ECE1;
  background-image:
    radial-gradient(circle at 12% 8%, rgba(191,74,50,.045), transparent 42%),
    radial-gradient(circle at 88% 24%, rgba(47,125,107,.045), transparent 40%);
  font-family:"PingFang SC","Hiragino Sans GB","Noto Sans CJK SC","Microsoft YaHei",sans-serif;
  font-size:17px; line-height:1.95; -webkit-font-smoothing:antialiased;
}
.page{
  max-width:850px; margin:52px auto; padding:66px 82px 58px;
  background:var(--card); border:1px solid #E8DFCF;
  box-shadow:0 30px 90px rgba(60,45,30,.09); border-radius:6px;
}
.kicker{
  font-size:12px; letter-spacing:.2em; color:var(--red);
  font-weight:600; margin-bottom:20px;
}
h1{
  font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;
  font-size:45px; line-height:1.18; letter-spacing:.01em;
  font-weight:700; margin:0 0 14px; color:#1B1E23;
}
p.subtitle{
  font-family:"Songti SC","STSong",serif;
  font-size:19px; line-height:1.6; color:#6E675C;
  margin:0 0 16px;
}
.meta{
  font-size:12px; color:var(--muted); letter-spacing:.08em;
  padding-bottom:28px; border-bottom:1px solid var(--line); margin-bottom:34px;
}
p{margin:0 0 1.15em}
strong{font-weight:600; color:#191C21}
em{font-style:italic}
a{color:var(--red); text-decoration:none; border-bottom:1px solid rgba(191,74,50,.3)}
a:hover{border-bottom-color:var(--red)}
h2{
  font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;
  font-size:30px; line-height:1.35; font-weight:700;
  margin:64px 0 22px; padding-left:19px; position:relative;
}
h2::before{
  content:""; position:absolute; left:0; top:.52em;
  width:8px; height:8px; background:var(--red);
}
h3{
  font-family:"Songti SC","STSong",serif;
  font-size:22px; margin:38px 0 14px; font-weight:700;
}
blockquote{
  margin:30px 0; padding:20px 24px; background:#F9F0E7;
  border-left:3px solid var(--red); border-radius:0 8px 8px 0;
  color:#4B453C; font-size:16px; line-height:1.85;
}
blockquote p{margin-bottom:.7em}
blockquote p:last-child{margin-bottom:0}
blockquote strong{color:#9E3B27}
blockquote ul{margin:.4em 0 .2em; padding-left:1.35em}
blockquote li{margin:.28em 0}
code{
  font-family:"SFMono-Regular",Menlo,Consolas,monospace;
  font-size:.86em; background:#F2E9DB; color:var(--red-dark);
  padding:2px 6px; border-radius:4px;
}
pre{
  background:#2A2E35; color:#F6EEE2; padding:20px 22px;
  border-radius:10px; overflow-x:auto; margin:24px 0 30px;
  font-size:14px; line-height:1.75;
}
pre code{background:none; color:inherit; padding:0; font-size:inherit}
table{
  width:100%; border-collapse:collapse; margin:24px 0 30px;
  font-size:15px; line-height:1.65;
}
th{text-align:left !important; background:#F5EDE1; font-weight:600; color:#3A342C}
th,td{padding:10px 12px; border-bottom:1px solid var(--line); vertical-align:top}
tr:last-child td{border-bottom:none}
figure{margin:0}
figcaption{display:none}
img{
  display:block; width:100%; height:auto; margin:36px 0 10px;
  border-radius:8px; border:1px solid var(--line); background:var(--paper);
}
p.caption{
  font-size:12.5px; line-height:1.7; color:#8B8377;
  text-align:center; margin:0 0 38px;
}
p.caption em{font-style:normal}
hr{border:0; border-top:1px solid var(--line); margin:54px 0}
ul,ol{padding-left:1.5em; margin:0 0 1.2em}
li{margin:.3em 0}
.endmark{
  text-align:center; color:var(--muted); font-size:12px;
  letter-spacing:.35em; margin:56px 0 6px;
}
@media (max-width:720px){
  body{font-size:16px; line-height:1.9}
  .page{margin:0; padding:34px 22px 40px; border:none; border-radius:0; box-shadow:none}
  h1{font-size:33px}
  h2{font-size:24px; margin-top:48px}
  blockquote{padding:16px 18px; font-size:15px}
  table{font-size:13px}
  th,td{padding:8px 6px}
  pre{font-size:13px; padding:16px}
}
@media print{
  body{background:#fff}
  .page{margin:0; max-width:none; border:none; box-shadow:none; padding:0}
}
"""

doc = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>liveness 和不动点</title>
<meta name="description" content="写给软件工程师的 liveness 与不动点科普：从永远完不成的任务，到无限轨迹、套索、公平性与最小/最大不动点。">
<style>{css}</style>
</head>
<body>
<main class="page">
{kicker}{frag}
<div class="endmark">— 完 —</div>
</main>
<script>
window.addEventListener('load', () => {{
  if (location.hash) {{
    const el = document.querySelector(location.hash);
    if (el) el.scrollIntoView();
  }}
}});
</script>
</body>
</html>
"""

out = ROOT / "preview.html"
out.write_text(doc, encoding="utf-8")
# GitHub Pages serves index.html at the site root
(ROOT / "index.html").write_text(doc, encoding="utf-8")
print("wrote", out, "and index.html", len(doc), "bytes")
