# LaTeX Build Notes

本次汇报材料改为 LaTeX Beamer 学术风格，源文件为：

```text
reports/rag_noise_robustness_slides.tex
```

该文件已包含两张图：

1. RAG 鲁棒性实验全流程与成员分工图
2. EGI-RAG / EGI-RAG+ 方法框架图

## 编译方式

推荐安装 TeX Live 或 MiKTeX，并使用 XeLaTeX 编译中文 Beamer：

```powershell
xelatex reports\rag_noise_robustness_slides.tex
xelatex reports\rag_noise_robustness_slides.tex
```

当前机器的命令行环境未检测到 `xelatex`，因此这里只生成了 `.tex` 源文件，未生成 PDF。

## 汇报重点

- EGI-RAG 的核心贡献是 evidence gate、evidence extraction 和 support verification。
- EGI-RAG+ 应表述为风险控制型改进：Misinfo Adoption 明显下降，但因为过度拒答导致 Accuracy 下降。
- Failure Analysis 建议放在结果之后，解释错误来源：检索不到正确证据、误导文档共现、证据抽取不完整、过度拒答和字符串评估误差。
