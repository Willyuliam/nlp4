# fair_subset_summary

| Setting | Method | Outputs | Missing | Errors | Accuracy | F1 | Misinfo Adopt | Evidence Acc | Refusal Acc | Faithfulness |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ramdocs noise060 front | crag_lite | 50 | 0 | 0 | 0.5000 | 0.1949 | 0.1400 | 0.8600 | 0.7000 | 0.8600 |
| ramdocs noise060 front | naive_rag | 50 | 0 | 0 | 0.5400 | 0.1883 | 0.1600 | 1.0000 | 0.6000 | 1.0000 |
| ramdocs noise060 front | rerank_rag | 50 | 0 | 0 | 0.6000 | 0.1808 | 0.2000 | 1.0000 | 0.6000 | 1.0000 |
| ramdocs noise060 front | self_rag_lite | 50 | 0 | 0 | 0.3800 | 0.1565 | 0.0600 | 1.0000 | 0.5800 | 1.0000 |
| rgb noise060 back | crag_lite | 50 | 0 | 0 | 0.6200 | 0.3226 | 0.0000 | 0.9600 | 0.9600 | 0.9600 |
| rgb noise060 front | crag_lite | 50 | 0 | 1 | 0.6000 | 0.2781 | 0.0000 | 0.9600 | 0.9600 | 0.9600 |
| rgb noise060 random | crag_lite | 50 | 0 | 0 | 0.5800 | 0.2799 | 0.0000 | 0.9800 | 0.9800 | 0.9800 |
| rgb noise060 back | naive_rag | 50 | 0 | 0 | 0.6400 | 0.3381 | 0.0000 | 1.0000 | 1.0000 | 1.0000 |
| rgb noise060 front | naive_rag | 50 | 0 | 0 | 0.7200 | 0.2927 | 0.0000 | 1.0000 | 1.0000 | 1.0000 |
| rgb noise060 random | naive_rag | 50 | 0 | 0 | 0.6600 | 0.2733 | 0.0000 | 1.0000 | 1.0000 | 1.0000 |
| rgb noise060 back | rerank_rag | 50 | 0 | 0 | 0.6600 | 0.3134 | 0.0000 | 1.0000 | 1.0000 | 1.0000 |
| rgb noise060 front | rerank_rag | 50 | 0 | 0 | 0.7000 | 0.3043 | 0.0000 | 1.0000 | 1.0000 | 1.0000 |
| rgb noise060 random | rerank_rag | 50 | 0 | 0 | 0.6400 | 0.2911 | 0.0000 | 1.0000 | 1.0000 | 1.0000 |
| rgb noise060 back | self_rag_lite | 50 | 0 | 0 | 0.6600 | 0.3370 | 0.0000 | 1.0000 | 0.9800 | 1.0000 |
| rgb noise060 front | self_rag_lite | 50 | 0 | 0 | 0.7000 | 0.2981 | 0.0000 | 1.0000 | 1.0000 | 1.0000 |
| rgb noise060 random | self_rag_lite | 50 | 0 | 0 | 0.6600 | 0.2864 | 0.0000 | 1.0000 | 1.0000 | 1.0000 |
