$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

$Python = "D:\conda_envs\type3\python.exe"
$CacheRoot = Join-Path $Root ".hf_cache"
$ModelsRoot = Join-Path $CacheRoot "models"
$LogDir = Join-Path $Root "outputs\debug"
$LogPath = Join-Path $LogDir "neural_full.log"

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

    $safeName = [IO.Path]::GetFileNameWithoutExtension($OutputPath)
    $stdoutPath = Join-Path $LogDir "$safeName.stdout.log"
    $stderrPath = Join-Path $LogDir "$safeName.stderr.log"
    $arguments = @(
        "-m", "src.run_baseline",
        "--method", $Method,
        "--input", $InputPath,
        "--output", $OutputPath,
        "--top_k", "$TopK",
        "--top_n", "$TopN",
        "--workers", "1",
        "--resume",
        "--config", "configs\model_config.example.yaml"
    )

    $process = Start-Process `
        -FilePath $Python `
        -ArgumentList $arguments `
        -WorkingDirectory $Root `
        -RedirectStandardOutput $stdoutPath `
        -RedirectStandardError $stderrPath `
        -WindowStyle Hidden `
        -Wait `
        -PassThru

    Get-Content -Path $stdoutPath -ErrorAction SilentlyContinue | Tee-Object -FilePath $LogPath -Append
    Get-Content -Path $stderrPath -ErrorAction SilentlyContinue | Tee-Object -FilePath $LogPath -Append
    if ($process.ExitCode -ne 0) {
        throw "Run failed with exit code $($process.ExitCode): method=$Method output=$OutputPath"
    }

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$timestamp] END method=$Method output=$OutputPath" | Tee-Object -FilePath $LogPath -Append
}

$seeds = @(
    @("outputs\rgb_results\rgb_neural_naive_rag_50.json", "outputs\rgb_results\rgb_neural_naive_rag_output.json"),
    @("outputs\rgb_results\rgb_neural_rerank_rag_50.json", "outputs\rgb_results\rgb_neural_rerank_rag_output.json"),
    @("outputs\rgb_results\rgb_neural_crag_lite_50.json", "outputs\rgb_results\rgb_neural_crag_lite_output.json"),
    @("outputs\rgb_results\rgb_neural_self_rag_lite_50.json", "outputs\rgb_results\rgb_neural_self_rag_lite_output.json"),
    @("outputs\ramdocs_results\ramdocs_neural_naive_rag_50.json", "outputs\ramdocs_results\ramdocs_neural_naive_rag_output.json"),
    @("outputs\ramdocs_results\ramdocs_neural_rerank_rag_50.json", "outputs\ramdocs_results\ramdocs_neural_rerank_rag_output.json"),
    @("outputs\ramdocs_results\ramdocs_neural_crag_lite_50.json", "outputs\ramdocs_results\ramdocs_neural_crag_lite_output.json"),
    @("outputs\ramdocs_results\ramdocs_neural_self_rag_lite_50.json", "outputs\ramdocs_results\ramdocs_neural_self_rag_lite_output.json")
)

foreach ($seed in $seeds) {
    if ((Test-Path -LiteralPath $seed[0]) -and -not (Test-Path -LiteralPath $seed[1])) {
        Copy-Item -LiteralPath $seed[0] -Destination $seed[1]
        "Seeded $($seed[1]) from $($seed[0])" | Tee-Object -FilePath $LogPath -Append
    }
}

$runs = @(
    @("naive_rag", "samples\rgb_all_input.json", "outputs\rgb_results\rgb_neural_naive_rag_output.json", 5, 5),
    @("rerank_rag", "samples\rgb_all_input.json", "outputs\rgb_results\rgb_neural_rerank_rag_output.json", 20, 5),
    @("crag_lite", "samples\rgb_all_input.json", "outputs\rgb_results\rgb_neural_crag_lite_output.json", 20, 5),
    @("self_rag_lite", "samples\rgb_all_input.json", "outputs\rgb_results\rgb_neural_self_rag_lite_output.json", 20, 5),
    @("naive_rag", "samples\ramdocs_all_input.json", "outputs\ramdocs_results\ramdocs_neural_naive_rag_output.json", 5, 5),
    @("rerank_rag", "samples\ramdocs_all_input.json", "outputs\ramdocs_results\ramdocs_neural_rerank_rag_output.json", 20, 5),
    @("crag_lite", "samples\ramdocs_all_input.json", "outputs\ramdocs_results\ramdocs_neural_crag_lite_output.json", 20, 5),
    @("self_rag_lite", "samples\ramdocs_all_input.json", "outputs\ramdocs_results\ramdocs_neural_self_rag_lite_output.json", 20, 5)
)

foreach ($run in $runs) {
    Invoke-Baseline -Method $run[0] -InputPath $run[1] -OutputPath $run[2] -TopK $run[3] -TopN $run[4]
}
