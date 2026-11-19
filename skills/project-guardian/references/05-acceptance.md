# 用真实输出验收任务

在 `SPEC.md` 记录用户原始目标、日常入口、输入批次或固定样例，以及用户能观察到的结果。每个任务或里程碑沿用 `TODO.md`、`STATUS.md` 中的稳定 ID。标准表格的第一列为 ID，勾选列表写作 `- [~] T1 描述`。保留任务与里程碑各自的验收条件。如果承诺五类数据，就从默认入口检查全部五类。文档类交付可用读者实际打开的文件作为入口。

## 默认入口

在 `SPEC.md` 放一个 `guardian-default` JSON 块。每个检查可以覆盖多个 ID。一个 ID 对应多个检查时必须全部通过。下列是可替换的示例：

```guardian-default
{
  "dashboard": {
    "covers": ["T1", "M1"],
    "entrypoint": "/dashboard",
    "data": "batch-B",
    "paths": ["src/dashboard/**", "data/current.json", "checks/observe_dashboard.py"],
    "expected": {"total": 17},
    "argv": ["python3", "checks/observe_dashboard.py"]
  }
}
```

观察程序从用户日常启动方式进入页面、命令或文件，读取真实入口、数据标识和实际值。成功退出，在标准输出写一行 JSON，例如 `{"entrypoint":"/dashboard","data":"batch-B","actual":{"total":17}}`。页面可复用现有浏览器自动化。预览页、指定候选库的调试参数或复述预期值的程序都不能替代用户入口。在 paths 登记会影响入口的源文件、依赖、配置和数据，包括观察程序。已完成项目命中这些路径时会重新核验。省略 paths 时，默认观察覆盖项目实现。验证者应实读适配器。外部数据会更新时，用实际批次或内容指纹。缺权限、缺输入或必须人工目测却还没有可靠观察途径时，记录限制并保留 `[~]`。

## 公式样例

在 `FORMULA.md` 放一个 `guardian-formula` JSON 块。每项登记真实实现、上游影响文件和观察程序的仓库相对路径或匹配模式。手算并锁定预期值。通过同一组输入调用生产公式。观察程序从标准输入读取仅含样例名与输入的 JSON，返回样例名与实际输出的 JSON。以下金额用整数元说明：

```guardian-formula
{
  "weighted-price": {
    "paths": ["src/prices.py", "checks/observe_price.py"],
    "argv": ["python3", "checks/observe_price.py"],
    "cases": {
      "normal": {"input": [[10,2],[20,2]], "expected": 15},
      "boundary": {"input": [], "expected": null},
      "counterexample": {"input": [[10,1],[20,9]], "expected": 19}
    }
  }
}
```

此例的正确输出为 `{"normal":15,"boundary":null,"counterexample":19}`。小数精度由公式契约定义。对齐类型与舍入，金额可用整数最小单位或定点字符串。新增公式同步登记实现路径。变更公式契约或命中公式路径时核对相应样例。公式可用 covers 关联交付任务。勾选这些任务时重核对应样例；勾选 STATUS.md 中的里程碑时核对全部公式。

## 运行与交接

1. 核对并暂存本次要交付的代码、验收定义和观察程序。先审阅配置中的命令，确认适用于当前任务且可在授权环境中运行。
2. 显式运行 `python3 "<技能目录>/scripts/acceptance.py" dashboard --root .`。公式检查用其 ID，例如 `weighted-price`。程序实际运行配置中的命令，比较完整结果。Git 提交钩子只核对证据。
3. 成功后把固定路径 `docs/tracking/evidence/<检查ID>.json` 与本次验收一起暂存，在对应任务旁引用它。证据含受测版本指纹、时间和实际观察值。只记录可公开给项目协作者的非敏感结果。
4. 结果相符才将任务或里程碑升为 `[x]`。旧版已完成记录保留。新晋升需要本工作区的实测记录。相关数据、外部服务或环境变化后，重新实测。无法验证时保留 `[~]`。

版本指纹覆盖该检查的契约、暂存的受测依赖和项目配置。已声明 paths 时，无关文件可以保留在工作区。进度、历史和证据文件可以在实测后更新。观察命令所读的实现应与候选提交一致。不要为获取证据提交无关的用户修改。存量项目首次启用时，将已有默认入口和手算样例填入原有追踪文档的对应代码块即可。
