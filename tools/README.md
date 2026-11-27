# 站点构建

纯静态站点，GitHub Pages 直接托管。`build.py` 只用 Python 标准库。

```bash
python3 tools/build.py          # 生成并检查
python3 tools/build.py --check  # 只检查，不写文件
```

## 改什么、在哪改

| 想改的 | 位置 |
|---|---|
| 首页“代表作”和“全部项目”卡片：标题、简介、缩略图、关键数字、分类 | `tools/projects.json` |
| 项目页顶部的关键指标条、页尾的上一个/下一个 | `tools/projects.json`（`metrics` 前 3 条、`projects` 顺序） |
| 页头导航、页脚 | `tools/build.py` 的 `masthead()`、`FOOTER` |
| 项目页正文 | `projects/<slug>/index.html`，`<!-- build:* -->` 标记之间的内容会被重新生成，不要手改 |

`site.css`、`case.js`、`projects.js` 的版本号按内容哈希自动更新。

## 检查项

- 本地链接、`src`、`poster` 指向的文件存在，跨页锚点存在；
- 每个 `<img>` 有 `alt`、`width`、`height`；
- 禁用措辞：版本/重跑类词语（见 `PUBLIC_BANNED`），以及 `~/.config/nusniumu-site/banned.txt` 里的私有词（每行一个，不进仓库）；
- `projects.json` 与 `projects/` 目录一一对应；
- 未被任何页面引用的媒体文件（只警告，不删除）。

手机宽度下的横向溢出需要在浏览器里检查。
