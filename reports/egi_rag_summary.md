# egi_rag_summary

| Setting | Method | Outputs | Missing | Errors | Accuracy | F1 | Misinfo Adopt | Evidence Acc | Refusal Acc | Faithfulness |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ramdocs noise060 front | crag_lite | 100 | 0 | 0 | 0.6200 | 0.2811 | 0.1500 | 0.8700 | 0.6900 | 0.8700 |
| ramdocs noise100 front | crag_lite | 100 | 0 | 0 | 0.0000 | 0.0128 | 0.2700 | 0.0000 | 0.5800 | 0.0000 |
| ramdocs noise060 front | egi_rag | 100 | 0 | 0 | 0.5700 | 0.5868 | 0.1100 | 0.7300 | 0.7800 | 0.8900 |
| ramdocs noise100 front | egi_rag | 100 | 0 | 0 | 0.0100 | 0.0226 | 0.3200 | 0.0000 | 0.5900 | 0.5000 |
| ramdocs noise060 front | naive_rag | 100 | 0 | 0 | 0.6100 | 0.2014 | 0.2500 | 1.0000 | 0.5600 | 1.0000 |
| ramdocs noise100 front | naive_rag | 100 | 0 | 0 | 0.0100 | 0.0233 | 0.3900 | 0.0000 | 0.5000 | 0.0000 |
| ramdocs noise060 front | rerank_rag | 100 | 0 | 0 | 0.5700 | 0.1790 | 0.2500 | 1.0000 | 0.5600 | 1.0000 |
| ramdocs noise100 front | rerank_rag | 100 | 0 | 0 | 0.0100 | 0.0132 | 0.3700 | 0.0000 | 0.5400 | 0.0000 |
| rgb noise060 back | crag_lite | 100 | 0 | 0 | 0.6800 | 0.3810 | 0.0000 | 0.9800 | 0.9700 | 0.9800 |
| rgb noise100 front | crag_lite | 100 | 0 | 1 | 0.0600 | 0.0133 | 0.0000 | 0.0000 | 0.8200 | 0.0000 |
| rgb noise060 back | egi_rag | 100 | 0 | 0 | 0.9200 | 0.7835 | 0.0000 | 1.0000 | 0.9600 | 1.0000 |
| rgb noise100 front | egi_rag | 100 | 0 | 0 | 0.0900 | 0.1027 | 0.0000 | 0.0000 | 0.8100 | 0.2800 |
| rgb noise060 back | naive_rag | 100 | 0 | 0 | 0.7600 | 0.3668 | 0.0000 | 1.0000 | 0.9800 | 1.0000 |
| rgb noise100 front | naive_rag | 100 | 0 | 0 | 0.0700 | 0.0194 | 0.0000 | 0.0000 | 0.8200 | 0.0000 |
| rgb noise060 back | rerank_rag | 100 | 0 | 0 | 0.7600 | 0.3501 | 0.0000 | 1.0000 | 0.9800 | 1.0000 |
| rgb noise100 front | rerank_rag | 100 | 0 | 0 | 0.0700 | 0.0230 | 0.0000 | 0.0000 | 0.8100 | 0.0000 |
| ramdocs all | egi_rag | 500 | 0 | 0 | 0.5320 | 0.5381 | 0.1100 | 0.7780 | 0.7100 | 0.8920 |
| rgb all | egi_rag | 300 | 0 | 0 | 0.9200 | 0.8127 | 0.0000 | 0.9933 | 0.9667 | 1.0000 |
