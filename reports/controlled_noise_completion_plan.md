# Controlled Noise Completion Plan

- Total planned jobs: 24
- Complete jobs: 0
- Pending jobs: 24
- DASHSCOPE_API_KEY: set

## Run Commands

Plan only:

```powershell
python scripts\run_controlled_noise_completion.py --plan-only
```

Run the default EGI-RAG and EGI-RAG+ noise-ratio matrix with resume:

```powershell
$env:DASHSCOPE_API_KEY="你的百炼 API Key"
python scripts\run_controlled_noise_completion.py --workers 1
python scripts\summarize_extended_experiments.py
```

If baseline RAMDocs 0/40/80 ratios are also needed, add baseline methods explicitly:

```powershell
python scripts\run_controlled_noise_completion.py `
  --methods zero_shot,ordered_rag,naive_rag,rerank_rag,crag_lite,self_rag_lite `
  --datasets ramdocs --ratios 0,40,80 --positions front
```

## Pending Jobs

| Dataset | Noise | Position | Method | Existing | Expected | Output |
|---|---:|---|---|---:|---:|---|
| rgb | 0% | front | egi_rag | 181 | 300 | `outputs/egi_rag/controlled/rgb/egi_rag_rgb_noise000_front_output.json` |
| rgb | 0% | front | egi_rag_plus | 0 | 300 | `outputs/egi_rag/controlled/rgb/egi_rag_plus_rgb_noise000_front_output.json` |
| rgb | 20% | front | egi_rag | 0 | 300 | `outputs/egi_rag/controlled/rgb/egi_rag_rgb_noise020_front_output.json` |
| rgb | 20% | front | egi_rag_plus | 0 | 300 | `outputs/egi_rag/controlled/rgb/egi_rag_plus_rgb_noise020_front_output.json` |
| rgb | 40% | front | egi_rag | 0 | 300 | `outputs/egi_rag/controlled/rgb/egi_rag_rgb_noise040_front_output.json` |
| rgb | 40% | front | egi_rag_plus | 0 | 300 | `outputs/egi_rag/controlled/rgb/egi_rag_plus_rgb_noise040_front_output.json` |
| rgb | 60% | front | egi_rag | 0 | 300 | `outputs/egi_rag/controlled/rgb/egi_rag_rgb_noise060_front_output.json` |
| rgb | 60% | front | egi_rag_plus | 0 | 300 | `outputs/egi_rag/controlled/rgb/egi_rag_plus_rgb_noise060_front_output.json` |
| rgb | 80% | front | egi_rag | 0 | 300 | `outputs/egi_rag/controlled/rgb/egi_rag_rgb_noise080_front_output.json` |
| rgb | 80% | front | egi_rag_plus | 0 | 300 | `outputs/egi_rag/controlled/rgb/egi_rag_plus_rgb_noise080_front_output.json` |
| rgb | 100% | front | egi_rag | 100 | 300 | `outputs/egi_rag/controlled/rgb/egi_rag_rgb_noise100_front_output.json` |
| rgb | 100% | front | egi_rag_plus | 0 | 300 | `outputs/egi_rag/controlled/rgb/egi_rag_plus_rgb_noise100_front_output.json` |
| ramdocs | 0% | front | egi_rag | 0 | 497 | `outputs/egi_rag/controlled/ramdocs/egi_rag_ramdocs_noise000_front_output.json` |
| ramdocs | 0% | front | egi_rag_plus | 0 | 497 | `outputs/egi_rag/controlled/ramdocs/egi_rag_plus_ramdocs_noise000_front_output.json` |
| ramdocs | 20% | front | egi_rag | 0 | 409 | `outputs/egi_rag/controlled/ramdocs/egi_rag_ramdocs_noise020_front_output.json` |
| ramdocs | 20% | front | egi_rag_plus | 0 | 409 | `outputs/egi_rag/controlled/ramdocs/egi_rag_plus_ramdocs_noise020_front_output.json` |
| ramdocs | 40% | front | egi_rag | 0 | 409 | `outputs/egi_rag/controlled/ramdocs/egi_rag_ramdocs_noise040_front_output.json` |
| ramdocs | 40% | front | egi_rag_plus | 0 | 409 | `outputs/egi_rag/controlled/ramdocs/egi_rag_plus_ramdocs_noise040_front_output.json` |
| ramdocs | 60% | front | egi_rag | 100 | 409 | `outputs/egi_rag/controlled/ramdocs/egi_rag_ramdocs_noise060_front_output.json` |
| ramdocs | 60% | front | egi_rag_plus | 0 | 409 | `outputs/egi_rag/controlled/ramdocs/egi_rag_plus_ramdocs_noise060_front_output.json` |
| ramdocs | 80% | front | egi_rag | 0 | 409 | `outputs/egi_rag/controlled/ramdocs/egi_rag_ramdocs_noise080_front_output.json` |
| ramdocs | 80% | front | egi_rag_plus | 0 | 409 | `outputs/egi_rag/controlled/ramdocs/egi_rag_plus_ramdocs_noise080_front_output.json` |
| ramdocs | 100% | front | egi_rag | 100 | 412 | `outputs/egi_rag/controlled/ramdocs/egi_rag_ramdocs_noise100_front_output.json` |
| ramdocs | 100% | front | egi_rag_plus | 0 | 412 | `outputs/egi_rag/controlled/ramdocs/egi_rag_plus_ramdocs_noise100_front_output.json` |
