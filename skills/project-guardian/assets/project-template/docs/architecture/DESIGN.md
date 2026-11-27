# 设计系统与 AI 视觉复刻规范（DESIGN.md）

> 本文档是前端界面与组件视觉的**机器可读单一真源**（由「复盘沉淀官」或主理人沉淀维护）。任何模型（Antigravity / Codex / Claude）在新增页面或重构 UI 时，必须逐字遵守以下 Token 与禁用清单，确保全站 1:1 视觉一致。纯后端或 CLI 项目可忽略本文档。

---

## 1. 视觉定位与核心基调（Aesthetic Direction）

- **产品气质**：`<例如：克制、高密度的专业数据工作台 / 温暖轻盈的消费级内容工具>`
- **兼容基线（Browser Baseline）**：`Baseline Widely Available`（或填写指定浏览器下限）
- **参考标杆页面 / 基准截图**：`<填写本项目已验收页面的路径或组件文件，作为 1:1 复刻母版>`

---

## 2. 精确设计 Token（严禁自行发明近似色值）

### 2.1 色彩系统（Palette）
| 语义角色 | CSS 变量 | 亮色值（Light） | 暗色值（Dark，可选） | 适用场景 |
| :--- | :--- | :--- | :--- | :--- |
| 主背景 | `--bg-canvas` | `#FFFFFF` | `#0F1115` | 页面底色 |
| 卡片/容器面 | `--bg-surface` | `#F8FAFC` | `#161A22` | 面板、卡片、侧边栏 |
| 边框线 | `--border-subtle` | `#E2E8F0` | `#262C38` | 1px 分割线与卡片描边 |
| 主文字 | `--text-primary` | `#0F172A` | `#F1F5F9` | 标题与核心数据 |
| 次要文字 | `--text-muted` | `#475569` | `#94A3B8` | 辅助说明、表头、时间戳 |
| 品牌主色 | `--accent-primary` | `<#HEX / oklch(...)>` | `<#HEX / oklch(...)>` | 主按钮、选中态、关键高亮 |
| 状态色（成/警/危） | `--state-ok / warn / err` | `#16A34A / #D97706 / #DC2626` | `#22C55E / #F59E0B / #EF4444` | 校验通过、提示、阻断报错 |

### 2.2 排版与字号层级（Typography）
- **无衬线正文字体**：`<如 "Inter", -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif>`
- **等宽数据/代码字体**：`<如 "JetBrains Mono", ui-monospace, monospace>`（金额、指标数字强制开启 `font-variant-numeric: tabular-nums` 对齐）
- **字号标尺**：页标题 `24px / 600` · 区标题 `16px / 600` · 正文 `14px / 400` · 辅助标注 `12px / 400`

### 2.3 间距、圆角与阴影标尺（Spacing, Radius & Elevation）
- **基准步长**：`4px` 网格（常用 `8px / 12px / 16px / 24px / 32px`）
- **圆角 Token**：`--radius-sm: 6px`（按钮/输入框） · `--radius-md: 10px`（卡片） · `--radius-lg: 14px`（弹窗）
- **层级阴影**：优先使用 `1px solid var(--border-subtle)` 区分层次，仅浮层/弹窗使用轻阴影，禁止滥用厚重模糊投影。

---

## 3. 布局骨架与组件规范（Component Anatomy）

- **页面骨架**：`<如：左侧固定导航 240px + 顶部操作栏 56px + 主内容区最大宽度 1280px，移动端折叠抽屉>`
- **原生能力优先**：弹窗优先 `<dialog>`，气泡/菜单优先 `popover`，多列对齐优先 CSS Grid / Subgrid（协同 `modern-web-guidance` 与 `frontend-design`）。
- **数据多态硬约束**：所有列表与图表必须同步遵守 [API_AND_UI_STATES.md](./API_AND_UI_STATES.md) 的七态清单（严禁把 `NULL` 静默渲染成 `0`）。

---

## 4. 反面禁用清单（Anti-Slop Rules）

- **禁止**未经授权使用默认 AI 紫/蓝大面积渐变背景或发光玻璃拟态。
- **禁止**在组件内硬编码魔法色值（必须走第 2 节 CSS 变量）。
- **禁止**为简单交互引入冗余重型第三方 UI 框架。
- **禁止**无意义的空装饰卡片、假数据占位符或未验证的盲目动效。
