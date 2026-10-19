# 形式化笔记

用 [Jekyll](https://jekyllrb.com/) 搭建的中文技术博客，托管在 GitHub Pages。
主题基于 Jekyll 官方的 [Minima](https://github.com/jekyll/minima)，首页与文章页使用各自独立的布局。

## 本地预览

建议使用 Ruby 3.x（GitHub Pages 的构建环境也使用 Ruby 3）。如果系统自带的 Ruby 较旧，建议用 rbenv 或 asdf 安装 Ruby 3.1+：

```bash
bundle install
bundle exec jekyll serve
```

打开 <http://127.0.0.1:4000/fm-blog-zh/>。如果希望本地地址不带 `baseurl`：

```bash
bundle exec jekyll serve --baseurl ""
```

## 写文章

在 `_posts/` 下新建 `YYYY-MM-DD-slug.md`，例如：

```yaml
---
layout: post
title: "文章标题"
subtitle: "副标题"
description: "用于首页摘要和 SEO 的一句话描述。"
date: 2026-10-19 09:00:00 +0800
categories:
  - 形式化验证
tags:
  - liveness
  - 不动点
reading_time: 20
figure_count: 9
cover: /images/example-card.png
image: /images/example.png
---
```

正文里的图片放在 `images/`，用 `relative_url` 拼接，保证 `baseurl` 变化时路径仍然正确：

```markdown
![图片说明]({{ '/images/example.png' | relative_url }})
{: .post-figure}

*图 1：图片说明。*
{: .caption}
```

首页的文章卡片会自动读取 `title`、`subtitle`、`description`、`tags`、`reading_time` 和 `cover`。
`cover` 是卡片缩略图，`image` 用于社交分享（Open Graph）。

## 目录结构

```text
_config.yml          站点配置
_posts/              文章（Markdown）
_layouts/            home / post / page / tags 布局
_includes/           header、footer、post-card 等片段
assets/main.scss     基于 Minima 的自定义样式
images/              文章插图
figures/build.py     插图生成脚本（需要 ImageMagick）
tags.md              标签索引页
404.html             404 页面
```

## 部署

GitHub Pages 会直接从 `main` 分支的根目录构建这个 Jekyll 站点，推送到 `main` 即可，
不需要额外的 CI 配置。仓库根目录没有 `.nojekyll`，这是为了让 GitHub Pages 执行 Jekyll 构建。

站点地址：<https://yihuang.github.io/fm-blog-zh/>

## 插图

`python3 figures/build.py` 会重新生成 `images/` 下的 SVG/PNG 插图（需要 ImageMagick）。
首页卡片使用的 `images/00-cover-card.png` 是从 `images/00-cover.png` 裁出的缩略图；
如果重做封面，请同步更新这张裁图。
