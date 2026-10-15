# iHsin的站点

个人技术博客：<https://itsusinn.github.io/>。

参照 [rust-proxy 文档站](https://github.com/rust-proxy/rust-proxy.github.io) 的 Wind 博客，使用 **Zensical 0.0.65** 的原生 `blog`、`rss` 和 `redirects` 功能。首页即博客，文章列表、分页、归档、分类、作者页和阅读时间均由 Zensical 生成，不需要额外安装 MkDocs 插件或维护文章索引。

## 本地开发

安装 [uv](https://docs.astral.sh/uv/) 和 [just](https://just.systems/)，在仓库根目录执行：

```sh
just serve   # http://127.0.0.1:8000/，包含草稿
just build   # 生成 site/，不发布
just check   # 构建并检查链接、文章地址、博客视图、搜索索引及 RSS
```

`justfile` 统一固定 Zensical 版本、Python 3.13 和 Windows 所需的 `tzdata`。uv 按需安装到工具缓存，无须维护项目虚拟环境。Windows 使用 PowerShell，其他平台使用默认 shell。

不安装 just 时，可以执行等价命令：

```sh
uvx --python 3.13 --with tzdata==2025.2 zensical==0.0.65 serve
uvx --python 3.13 --with tzdata==2025.2 zensical==0.0.65 build --clean
uv run --no-project --python 3.13 scripts/check_site.py
```

## 写文章

在 `docs/posts/` 下新增 Markdown 文件，可使用子目录整理源文件：

```markdown
---
title: 文章标题
date: 2026-10-15
slug: my-new-post
authors:
  - ihsin
categories:
  - Linux
draft: true
---

# 文章标题

用于首页和分类页的摘要。

<!-- more -->

正文从这里开始。
```

- `date`、唯一的 `slug` 和摘要分隔符是写作约定；发布时移除 `draft: true`。未来日期的文章也按草稿处理。
- 发布地址为 `/p/my-new-post/`，不受源文件所在子目录影响。已有文章的 slug 不应随意修改。
- 作者信息在 `docs/.authors.yml` 中维护。分类直接取自文章元数据，不单独创建分类页。
- `zensical.toml` 的 `nav` 只列出博客入口及普通页面，不加入单篇文章或生成的归档、分类、作者页面。
- 链接到其他文章时使用 Markdown 源路径，例如 `[Linux Tips](linux-tips.md)`；Zensical 会转换为发布地址。
- 内容使用简体中文，代码块建议注明语言。所有文章沿用 CC BY-NC-SA 4.0 许可。

更多配置见 [Zensical 博客文档](https://zensical.org/docs/setup/blog/)。

## 仓库结构

| 路径 | 用途 |
| --- | --- |
| `zensical.toml` | 站点、原生博客、RSS、主题及旧地址跳转配置 |
| `docs/index.md` | 博客首页介绍，文章列表自动生成 |
| `docs/posts/` | 文章源文件 |
| `docs/.authors.yml` | 作者资料 |
| `docs/links.md` | 个人链接与订阅入口 |
| `overrides/404.html` | 中文 404 页面，包含无障碍跳转锚点 |
| `justfile` | 本地和 CI 共用的构建入口与版本 |
| `scripts/check_site.py` | 无第三方依赖的构建产物检查 |
| `.github/workflows/deploy.yml` | PR 验证与 GitHub Pages 发布 |
| `site/` | 构建产物，已忽略，不提交 |

## 从 Hugo 迁移

两篇原有文章的正文、发布时间和地址保留：

- `/p/java-secure-random/`
- `/p/linux-tips/`

旧 RSS 地址 `/index.xml` 继续提供全文订阅，只包含文章；`/feed_rss_updated.xml` 提供更新订阅。搜索改用 Zensical 顶部的全文搜索，归档、分类和作者入口由博客侧栏提供。

旧 `/archives/`、`/search/`、`/post/` 跳转到博客首页；原来没有正文的 `/support/` 合并到 `/links/`。旧主题的空分类模板、示例社交链接及默认 Disqus 配置已移除。原站没有英文文章，因此不再生成空的英文站点。

## GitHub Pages

在仓库 **Settings → Pages → Build and deployment → Source** 中选择 **GitHub Actions**。此仓库使用 `master` 分支：

- Pull request 运行构建和产物检查，不发布。
- 推送到 `master` 或在 `master` 上手动运行工作流，检查成功后发布 `site/`。
- 构建任务只有仓库读取权限；仅部署任务具有 Pages 写入和 OIDC 权限。

博客构建不依赖参考仓库、Go、Hugo 或主题更新工作流。

## 三体模拟应用

`/apps/three-body/` 部署 [Itsusinn/three-body](https://github.com/Itsusinn/three-body) 的 Rust / WASM + WebGPU 应用。

- 网站 CI 解析三体 `main` 的最新提交，并调用其可复用构建工作流，检查代码并编译完整静态产物。
- 先运行 `just build` 生成博客，再将 `three-body-web` artifact 放入 `site/apps/three-body/`，最后校验博客链接、WASM 文件与 `version.json` 中的提交号。应用或博客失败都不发布。
- 三体仓库的 `main` 构建成功后，通过其 `WEBSITE_DEPLOY_TOKEN` secret 即时触发本站 `deploy.yml`；令牌仅需本仓库的 Actions 写权限。本站不需要额外 secret，也不会反向触发三体发布。
- 本仓库推送、PR 和手动运行也会构建应用；PR 不发布。多个发布串行进行，网站构建解析最新的三体提交。
- 本地 `just serve` / `just check` 显示说明页，不要求安装 Rust。要运行模拟，请在三体仓库执行 `trunk serve --release`。

线上版本可通过 <https://itsusinn.github.io/apps/three-body/version.json> 查询。Pages 使用 GitHub Actions，并在 `github-pages` 环境的分支策略中允许 `master`。
