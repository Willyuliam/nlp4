# 组员 B 中期答辩材料

## 负责内容

组员 B 负责 RAG 系统与 baseline 原型，实现统一模型调用接口和可比较的基础方法，为成员 A 的评估脚本和成员 C 的 EGI-RAG 方法对比提供输出。

## 模型调用设计

中期使用已有 conda 环境 `type3` 运行，不额外安装依赖。模型调用使用 Qwen/百炼 API。代码通过 `QwenClient` 封装模型调用，统一提供 `generate(prompt)` 接口。真实 API Key 不写入项目文件，运行时优先从环境变量 `DASHSCOPE_API_KEY` 读取；如果 API Key 为空，程序会提示“请设置 DASHSCOPE_API_KEY 或填写本地配置”。

## Baseline 方法

1. Zero-shot：只输入问题，不提供任何检索文档，用来观察模型自身知识的回答能力。
2. Naive RAG：输入问题和前 `top_k` 篇候选文档，直接让模型基于上下文回答，用来观察噪声文档对普通 RAG 的影响。
3. Rerank RAG：先对候选文档进行轻量重排，再选取前 `top_n` 篇文档生成答案，用来验证重排是否能缓解无关噪声。

## 检索与重排模块

中期阶段不下载 embedding 模型，也不引入 FAISS。Rerank RAG 使用本地关键词/字符重合度打分，优先选择与问题词项重合更多的文档。最终阶段计划升级为 `bge-m3` embedding、FAISS 向量召回和 `bge-reranker-v2-m3` 重排器。

## 输出与评估对接

三个 baseline 均输出 JSON 文件，字段包含 `id`、`method`、`answer`、`selected_doc_ids`、`contexts_used`、`prompt_version`、`raw_response` 和 `error`。成员 A 可以直接根据 `id` 对齐参考答案，计算 Accuracy、错误答案采纳率、证据选择准确率等指标。

## 中期可展示内容

若成员 A 已提供样本且 API Key 可用，可运行 20-30 条样本生成正式输出。若数据或 API Key 尚未到位，可使用 `--dry_run` 生成 prompt 和流程记录，展示系统从输入、文档选择、prompt 构造到输出文件的完整闭环。
