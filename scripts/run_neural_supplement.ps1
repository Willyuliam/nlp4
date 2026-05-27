$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

$Python = "D:\conda_envs\type3\python.exe"
$CacheRoot = Join-Path $Root ".hf_cache"
$ModelsRoot = Join-Path $CacheRoot "models"
$LogDir = Join-Path $Root "outputs\debug"
$LogPath = Join-Path $LogDir "neural_supplement_50.log"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$env:HF_HOME = $CacheRoot
$env:HF_HUB_CACHE = Join-Path $CacheRoot "hub"
$env:SENTENCE_TRANSFORMERS_HOME = Join-Path $CacheRoot "sentence-transformers"
$env:RAG_DISABLE_NEURAL_RETRIEVER = "0"
$env:RAG_DISABLE_NEURAL_RERANKER = "0"
$env:RAG_EMBEDDING_MODEL = Join-Path $ModelsRoot "bge-m3"
$env:RAG_RERANKER_MODEL = Join-Path $ModelsRoot "bge-reranker-v2-m3"

function Invoke-Baseline {
    param(
        [string]$Method,
        [string]$InputPath,
        [string]$OutputPath,
        [int]$TopK,
        [int]$TopN
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$timestamp] START method=$Method input=$InputPath output=$OutputPath" | Tee-Object -FilePath $LogPath -Append
    & $Python -m src.run_baseline `
        --method $Method `
        --input $InputPath `
        --output $OutputPath `
        --limit 50 `
        --top_k $TopK `
        --top_n $TopN `
        --workers 1 `
        --resume `
        --config configs\model_config.example.yaml 2>&1 | Tee-Object -FilePath $LogPath -Append
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$timestamp] END method=$Method output=$OutputPath" | Tee-Object -FilePath $LogPath -Append
}

$runs = @(
    @("naive_rag", "samples\rgb_all_input.json", "outputs\rgb_results\rgb_neural_naive_rag_50.json", 5, 5),
    @("rerank_rag", "samples\rgb_all_input.json", "outputs\rgb_results\rgb_neural_rerank_rag_50.json", 20, 5),
    @("crag_lite", "samples\rgb_all_input.json", "outputs\rgb_results\rgb_neural_crag_lite_50.json", 20, 5),
    @("self_rag_lite", "samples\rgb_all_input.json", "outputs\rgb_results\rgb_neural_self_rag_lite_50.json", 20, 5),
    @("naive_rag", "samples\ramdocs_all_input.json", "outputs\ramdocs_results\ramdocs_neural_naive_rag_50.json", 5, 5),
    @("rerank_rag", "samples\ramdocs_all_input.json", "outputs\ramdocs_results\ramdocs_neural_rerank_rag_50.json", 20, 5),
    @("crag_lite", "samples\ramdocs_all_input.json", "outputs\ramdocs_results\ramdocs_neural_crag_lite_50.json", 20, 5),
    @("self_rag_lite", "samples\ramdocs_all_input.json", "outputs\ramdocs_results\ramdocs_neural_self_rag_lite_50.json", 20, 5)
)

foreach ($run in $runs) {
    Invoke-Baseline -Method $run[0] -InputPath $run[1] -OutputPath $run[2] -TopK $run[3] -TopN $run[4]
}
