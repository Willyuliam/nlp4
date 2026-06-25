# 组员 B Controlled 实验执行记录

## 已完成

- 已新增 `ordered_rag` 方法，用于按输入顺序取前 `top_k` 篇文档，专门分析正确文档在 `front/middle/back/random` 时的位置影响。
- 已新增批量运行脚本 `scripts/run_member_b_controlled.py`，覆盖组员 B 后续计划中的 controlled 实验矩阵。
- 已新增汇总脚本 `scripts/summarize_member_b_controlled.py`，可将 controlled 输出统一评估并写入 Markdown 表格。
- 已使用 conda 环境 `type3` 的解释器 `D:\conda_envs\type3\python.exe` 完成流程验证。

## 已验证命令

语法检查：

```powershell
D:\conda_envs\type3\python.exe -m py_compile src\rag_baselines\baselines.py scripts\run_member_b_controlled.py scripts\summarize_member_b_controlled.py
```

`ordered_rag` 单样本 dry-run：

```powershell
D:\conda_envs\type3\python.exe -m src.run_baseline --method ordered_rag --input samples\controlled\rgb\rgb_noise060_back_input.json --output %TEMP%\ordered_rag_smoke.json --limit 1 --dry_run --top_k 5
```

完整 controlled 矩阵 smoke：

```powershell
D:\conda_envs\type3\python.exe scripts\run_member_b_controlled.py --python D:\conda_envs\type3\python.exe --dry-run --limit 1 --disable-neural --output-root %TEMP%\member_b_controlled_smoke
```

验证结果：

- controlled 计划矩阵共 `90` 个任务。
- 任务组成：`15` 个 controlled 设置 × `6` 个方法。
- 方法：`zero_shot`、`ordered_rag`、`naive_rag`、`rerank_rag`、`crag_lite`、`self_rag_lite`。
- dry-run 结果：`90` 个任务全部成功，`0` 个失败。

## 正式运行结果

已在 conda 环境 `type3` 中完成组员 B controlled 正式实验。为避免首次下载 embedding/reranker 模型影响进度，本轮使用 `--disable-neural`，检索与重排走项目内词法 fallback；脚本同时把 HuggingFace 缓存路径设置到项目 `.hf_cache/` 下，避免默认写入 C 盘。

正式运行命令：

```powershell
D:\conda_envs\type3\python.exe scripts\run_member_b_controlled.py --python D:\conda_envs\type3\python.exe --methods zero_shot,ordered_rag,naive_rag,rerank_rag --workers 4 --job-workers 3 --disable-neural --output-root outputs\controlled
```

```powershell
D:\conda_envs\type3\python.exe scripts\run_member_b_controlled.py --python D:\conda_envs\type3\python.exe --methods crag_lite,self_rag_lite --workers 2 --job-workers 1 --disable-neural --output-root outputs\controlled
```

汇总表生成命令：

```powershell
D:\conda_envs\type3\python.exe scripts\summarize_member_b_controlled.py --output-root outputs\controlled --save reports\member_b_controlled_summary.md
```

输出位置：

- 模型结果：`outputs/controlled/{dataset}/`
- 指标汇总：`reports/member_b_controlled_summary.md`

## 完整性校验

- controlled 正式矩阵共 `90` 个输出文件，已全部生成。
- 输出记录共 `28,980` 条，所有输出文件行数均与对应 `reference.json` 对齐。
- 未发现重复样本、缺失样本或额外样本。
- 剩余 `13` 条样本包含 API 服务返回的 `DataInspectionFailed` 内容安全拦截错误，已保留在对应输出的 `error` 字段中，属于模型服务层拒绝而非脚本执行失败。

## 提交注意

本地 `configs/model_config.example.yaml` 中已填写 API key，仅用于本机运行验证。该文件的密钥改动不应提交到 GitHub；提交时只纳入代码、实验输出和报告文件。
