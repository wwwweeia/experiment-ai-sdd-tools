# 文档首页 UI 优化计划

## 1. 目标与现状分析
- **现状**：当前 `docs/index.md` 的 Hero 区域由于没有配图，加上 `style.css` 中放宽了 `max-width` 限制，导致长标题和副标题在左侧生硬换行，右侧出现大片留白，视觉极不平衡。
- **目标**：根据确认的意图，采用**居中对齐**的布局方案，消除右侧留白，使整体视觉更加紧凑和专业。

## 2. 具体修改方案

### 2.1 修改 `docs/.vitepress/theme/style.css`
需要新增和调整 `.VPHero` 相关的 CSS 规则，强制内容居中。

- **核心容器居中**：给 `.VPHero` 和 `.VPHero .main` 添加居中相关的样式（如 `margin: 0 auto`，`text-align: center`）。
- **按钮组居中**：VitePress 的按钮组类名为 `.actions`，默认为左对齐（`justify-content: flex-start`），需要将其重写为 `justify-content: center !important;`。
- **文本块居中**：确保 `.name`、`.text`、`.tagline` 等文本元素的内外边距是对称的，以达到完美的视觉居中效果。

### 2.2 优化 `docs/index.md` 的文案排版（视效果微调）
- 原标题：“AI 编程 SDD 工具实战对比”
- 原副标题：“Superpowers · Spec-Kit · OpenSpec”
- 居中后，如果发现文字在特定屏幕宽度下依然有单字换行的情况，可以考虑在 `text` 属性中适当加入 `<br>` 标签或者调整字号，以确保断句优雅。

## 3. 假设与决策
- **决策**：完全采用 CSS 控制原生 VPHero 组件居中，避免引入额外的自定义组件或图片资产，符合“最小可用实现（KISS）”原则。
- **假设**：当前的 VitePress 主题 DOM 结构为标准的 `.VPHero > .container > .main > .actions`，标准的 CSS 覆盖可以生效。

## 4. 验证步骤
1. 执行修改后，运行 VitePress 的本地开发服务器。
2. 通过预览工具（或浏览器）查看 `http://localhost:5173/experiment-ai-sdd-tools/`。
3. 检查：标题、副标题、Tagline 和操作按钮是否全部水平居中。
4. 检查：响应式表现（缩小窗口时，居中效果和换行是否依然优雅）。