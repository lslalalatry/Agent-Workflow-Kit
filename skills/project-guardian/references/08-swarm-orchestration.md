# Swarm 多工匠协同与单主线收口协议

> **触发边界（严禁擅自开启 Swarm）**：仅当用户在当前会话明确调用 `/swarm`，或已存在活跃的 Swarm 会话时才使用本手册；非 `/swarm` 场景严禁擅自调用 `swarm` 工具。若项目已接入 `project-guardian`（存在 `AGENTS.md` 与 `docs/tracking/`），用户开启 `/swarm` 时 Coordinator **自动读取并执行**本手册。

把单人单窗口的 `project-guardian` 视作“单工位匠人”；开启 `/swarm` 就像多人同场施工——必须先把**总账本写锁、模块领地、脚手架生命周期**定死，才不会把仓库和追踪文档改花。

---

## 零、任务分级自动判定（轻度 / 中度 / 深度）

当用户在**尚未接入 `project-guardian`** 的目录启动 `/swarm` 时，先依据用户的级别关键词（或一句话确认结果）决定是否建账本：

| 任务级别 | 典型特征 | `/swarm` 处理动作 |
| :--- | :--- | :--- |
| **轻度任务** | 一次性整理、纯只读调研、独立小脚本/小页面 | 直接用原生 `/swarm` 快速并行干完，不建 `AGENTS.md` 与 `docs/tracking/` |
| **中度任务** | 多功能并发改代码、需要防撞与主干干净收口 | 自动用 `--with-decisions` 轻量初始化，再按本手册分片施工与合回 |
| **深度任务** | 跨模块系统、含算钱/统计公式、集中存储或长期交接 | 完整接入（`--with-architecture --with-decisions`，涉计算加 `--with-formula`），锁定核心规格后再分片开工 |

---

## 一、角色分工与工作区边界（总账本单写者铁律）

| Swarm 角色 | `workspace` 与分支约定 | 可写范围 | 严禁行为 |
| :--- | :--- | :--- | :--- |
| **Coordinator**（主控 / 本对话） | 主工作区（唯一 `main`） | ① **唯一有权限修改 `docs/tracking/`（`STATUS/TODO/SPEC/FORMULA/DECISIONS`）**；<br>② 维护 `swarm_pane` 的 `plan.json`；<br>③ 合回分片、调用终检并执行 `commit` / `push` / `kill` | 禁止跳过跨模块验审直接替 Author 勾选 `TODO.md` `[x]` |
| **Author-`<module>`**（分片作者） | `workspace: "share"`，分支命名为 **`swarm/<worker>`**（推荐方案 A） | 所属子模块代码、模块单测、对应 `docs/architecture/modules/<module>.md` 的 `Expectations` | **禁止修改 `docs/tracking/` 总账本**；禁止复制数据库或大资产（严格遵守 `L0/L1`）；禁止跨模块改动他人领地 |
| **Verifier / Reviewer**（独立验审员） | `workspace: "inherit"`（只读主工作区） | 仅写入 `code_review.py` 本地审查记录 | 禁止由 Author 自写自审；必须等分支合回主工作区后再跑终检 |
| **Redteam-A / Redteam-B**（点名触发） | `workspace: "inherit"`，**禁止传 `fork`** | 只读审计并向 `@coordinator` 提交问题清单 | 禁止注入聊天妥协过程；禁止建议非必要复杂架构 |

---

## 二、Coordinator 开工前准备与 `swarm_pane` 对齐

1. **前置文档锁与按需检索**：Coordinator 先通过 `query_docs.py modules`（一眼掌握所有模块卡状态与未勾断言）、`query_docs.py search/read` 与 `chat_sync.py read` 确认当前 `TODO.md`、涉及的 `D-编号`/`F-编号` 与 `modules/<module>.md`。
2. **禁止并行抢写同一文件**：把待办拆成互不重叠的文件/模块边界；若存在公共契约修改（如 `SPEC.md` 术语或数据库表结构），必须先由 Coordinator 改完或串行排期，再派发并行 Author。
3. **对齐 `swarm_pane` 视图**：写入 `plan.json` 时，`threads` **按交付成果或子模块分组**（复用 `TODO.md` / `modules/*.md`），不按角色分组；若任务涉及前端界面修改，在 Author 的 Brief 中明确要求汇报附上：
   ```text
   Screenshot: <worker 自身 appData brain 目录下的绝对路径> | 改动说明（10词内）
   ```
4. **防记忆漂移**：给每位 Worker 的 Brief 中直接附带所需 `query_docs.py` 查询指令，要求其开始前**实读 `SPEC.md` `Reference` 落点与 `DECISIONS.md` 原文**，严禁靠提示词转述猜阈值。

---

## 三、方案 A 全生命周期：并行分片 -> 合回 `main` -> 独立验审 -> 清理销毁

1. **分片施工期（Author 在 `share` 工作副本中）**：
   - Author 切换到分片分支：`git checkout -b swarm/<worker>`（若环境已配好 `swarm/*` 分片分支则直接沿用）。
   - 完成本模块实现、更新对应 `modules/<module>.md` 的 `Expectations` 并跑通模块测试后，在 `swarm/<worker>` 上运行 `verify_guardrails.py`（次级 worktree / `swarm/*` 分支会放行临时分支并豁免总账本校验，但仍**严格拦截私建数据库、大文件克隆与越界命名**）；若需提交到分片分支，先执行 `code_review.py show` + `record` 满足本地钩子，再 `@coordinator` 汇报。
2. **合回主干与销毁临时工位（Coordinator 执行）**：
   - 所有依赖方完结后，Coordinator 在主工作区按依赖顺序合回各个 `swarm/<worker>`（推荐 `git merge --squash swarm/<worker>` 保持主干单提交历史干净，再删 `git branch -D swarm/<worker>`；或用 `git merge --no-ff` 后 `git branch -d`），随后对已完成 Author 执行 `swarm kill`（永久销毁 `share` 临时工作副本）。
3. **独立验审（Verifier 执行）**：
   - 在已合回的单一主工作区上，Coordinator 唤醒 `verifier`（`workspace: "inherit"`）：
     - 运行 `code_review.py show`，逐字核对涉及的 `D-编号` / `F-编号` 原文、反例 `Expectations` 与调用方；
     - 运行全量测试与 `acceptance.py` 默认正式入口实测；
     - 确认无阻断项后登记 `code_review.py record` 并 `@coordinator`。
4. **最终门禁与交付收口（Coordinator 执行）**：
   - Coordinator 通过 `chat_sync.py` 更新 `docs/tracking/STATUS.md`（断点锚点）、`TODO.md`（仅默认入口实测通过才标 `[x]`）及 `BACKLOG.md`。
   - 在 `main` 主工作区运行 `python3 "<技能目录>/scripts/verify_guardrails.py" --root .`：**此时恢复零容忍全严格校验——必须确保所有 `swarm/*` 分支与额外 worktree 已全部清零**。
   - 依据 `AGENTS.md` 中的 `delivery_mode` 执行提交并推送 `main`（或输出提醒卡等待确认），有监控器时发布 `[done]`，最后输出 **「🟢 本任务已完结（可新开对话框）」**。
