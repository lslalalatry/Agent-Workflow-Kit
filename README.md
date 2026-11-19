# Agent-Workflow-Kit · 通用 AI 项目治理与追踪文档工具箱

这是一套**跨行业、跨编程语言、100% 领域通用**的 AI 项目工程管控工具箱，同时兼容 **Antigravity** 与 **Codex**。
专门解决长任务和多轮迭代中最让人头疼的五大问题：**AI 越改越乱另起炉灶、偷偷改错计算公式、随手复制出一堆数据库与残留分支、聊久了跨窗口失忆、以及给非技术背景用户抛晦涩黑话**。

---

## 一、用「装修房子」秒懂这套机制怎么运作

把你的每一个项目想象成**一套正在装修的房子**，AI 是**施工队长**：

1. **墙上的《最高施工宪章》（项目根目录 `AGENTS.md`）**
   - 只有约 6 KB，每次对话自动生效，你不用记任何命令。里面规定了施工队长的铁律：遇到技术分叉必须打生活化比方让你选、不准私自加戏、不准乱搭平行违建、不准乱复制数据库。
2. **桌上的《追踪文档活页夹》（`docs/tracking/` 目录）**
   - 所有文档用固定名字（不带日期，不产生多份乱麻副本），各司其职：
     - `STATUS.md`（**100 行以内的交接白板**）：写清刚干完哪一步、下一步干什么。哪怕中途断网或新开聊天窗口，你只要说一句 **“按追踪文档继续”**，AI 看一眼这块白板就能无缝接上！
     - `SPEC.md`（**竣工蓝图说明书**）：只写系统现在长什么样、标准术语叫什么，绝不掺杂修 Bug 流水账。
     - `FORMULA.md`（**算账与算法铁契**，有计算的项目必开）：把公式、分子分母范围、保留几位小数、总和守恒等式和 3 组手算标准答案锁死，AI 没经你批准一个符号都不准改。
     - `TODO.md`（**今日施工微任务单**）：拆成 2–5 分钟能干完的小步子，区分 `[ ] 待办`、`[~] 草稿待验`、`[x] 正式入口实测通过`（防假勾选）。
     - `BACKLOG.md`（**以后再说的想法池 + 历史施工台账**）：把暂时不做的点子收好不干扰主线，把修过的旧问题归档到这里。
3. **工地门口的《红外自动安检闸机》（`verify_guardrails.py` + Git 自动拦截锁）**
   - AI 每次改完代码想存档交工时，门口闸机会自动扫描：
     - 临时搭的实验脚手架分支（`exp/*`）拆干净回主线 `main` 了吗？
     - 有没有偷偷多生出未登记的 `.db / .duckdb / .sqlite` 数据库或超大副本？
     - 改了代码，有没有同步更新 `STATUS.md` 进度白板？
     - `STATUS.md` 有没有写超 100 行变成裹脚布？
   - **只要有一条违规，闸机直接亮红灯拦住不准存档**，逼 AI 当场收拾干净再交工，你完全不用人工盯梢！

---

## 二、目录结构一览

```text
Agent-Workflow-Kit/
├── README.md                              # 本使用说明
├── global-rules/
│   └── COLLABORATION_PRINCIPLES.md        # 13 条全局通用《Agent 协作与比喻沟通原则》
├── project-template/                      # 可随时手动复制到任意新项目的空白模板包
│   ├── AGENTS.md                          # 通用项目宪章母版（仅需填底部 10 行配置卡）
│   └── docs/tracking/                     # 标准追踪文档空白模板套组
│       ├── SPEC.md
│       ├── STATUS.md
│       ├── TODO.md
│       ├── BACKLOG.md
│       ├── FORMULA.md
│       └── DECISIONS.md
├── skills/
│   └── project-guardian/                  # 全局主控 Skill（已同步安装到 Antigravity 与 Codex）
│       ├── SKILL.md                       # 阶段路由入口
│       ├── references/                    # 按阶段读取的工作手册（平时占 0 上下文）
│       └── scripts/
│           ├── init_project.py            # 一键给任意项目装好模板 + 自动安检闸机
│           └── verify_guardrails.py       # 自动安检闸机核心检查脚本
└── scripts/
    └── sync_global.py                     # 修改母版后一键同步刷新 Antigravity 与 Codex 全局目录
```

---

## 三、以后开启任何新项目或接入老项目，怎么用最省心？

### 方式 1：直接对 AI 说一句话（最推荐，零命令行操作）
打开任意空文件夹或现有项目文件夹，直接发给 AI（Antigravity 或 Codex 均可）：

> **“用 `project-guardian` 给当前项目初始化追踪文档和自动闸机，然后用 `/grill-me` 跟我对齐需求。”**
> *(如果项目涉及算钱、统计指标、权重或几何换算，顺带加一句：“包含计算公式文档”。)*

AI 会先根据初步想法盘点本项目并调研高星且近期有实质更新的 GitHub 项目，借鉴 ECC 的 search-first，再与你定稿。初始化实测结果写入 STATUS.md。公式和默认入口的验收方法见[验收手册](./skills/project-guardian/references/05-acceptance.md)。

AI 会自动帮你运行初始化脚本、装好自动安检闸机、用大白话比喻陪你理清需求、自动派两个独立红队子 Agent 挑刺抓漏洞、经你拍板后拆好 `docs/tracking/` 开始一步步稳健开发！

### 方式 2：终端一行命令初始化
- **普通项目（核心 4 份追踪文档 + 自动闸机）**：
  ```bash
  python3 ~/Documents/Agent-Workflow-Kit/skills/project-guardian/scripts/init_project.py /你的项目路径 --minimal
  ```
- **含金额/指标/物理几何计算的项目（额外开启 `FORMULA.md` 公式契约锁）**：
  ```bash
  python3 ~/Documents/Agent-Workflow-Kit/skills/project-guardian/scripts/init_project.py /你的项目路径 --with-formula --with-decisions
  ```

### 同一项目有多个对话时怎么接力？

收到拍板的对话当轮写回决策与受影响文档。新旧对话动手前重读工作区。GitHub 仓库按项目复用，commit 和 push 分别按交接节点和已有授权执行。[共享决定与 Git 交接](./skills/project-guardian/references/06-shared-decisions.md)

无论聊了多少轮、或者遇到网络流中断，直接新开一个干净窗口对 AI 说：
> **“重读最新 DECISIONS、STATUS、TODO 及本次涉及的产品和公式说明，从断点继续推进。”**

---

## 四、如果你以后微调了本工具箱里的规则

改完 `/Users/admin/Documents/Agent-Workflow-Kit/` 下的任何模板或脚本后，运行一次同步命令即可同时刷新 Antigravity 和 Codex 两端：

```bash
python3 ~/Documents/Agent-Workflow-Kit/scripts/sync_global.py
```
