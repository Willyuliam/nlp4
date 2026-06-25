param(
    [switch]$DryRun,
    [int]$Limit = 10
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "Member C midterm automation"
Write-Host "Root: $Root"
Write-Host "Limit: $Limit | DryRun: $($DryRun.IsPresent)"

$egiArgs = @(
    "-m", "src.run_egi_rag",
    "--input", "samples/rgb_input.json",
    "--output", "outputs/midterm/rgb_egi_rag_output.json",
    "--limit", "$Limit",
    "--top_k", "8",
    "--top_n", "5",
    "--max_iterations", "2"
)
if ($DryRun) {
    $egiArgs += "--dry_run"
}

Write-Host "Running EGI-RAG..."
python @egiArgs
if ($LASTEXITCODE -ne 0) { throw "EGI-RAG failed" }

$baselinePath = Join-Path $Root "outputs/midterm/rgb_naive_rag_output.json"
if (-not (Test-Path $baselinePath)) {
    Write-Host "Baseline output not found, skip case comparison."
} else {
    Write-Host "Building case comparison..."
    python -m src.analyze_cases `
        --input samples/rgb_input.json `
        --baseline outputs/midterm/rgb_naive_rag_output.json `
        --egi outputs/midterm/rgb_egi_rag_output.json `
        --output reports/egi_case_comparison.md `
        --limit 5
    if ($LASTEXITCODE -ne 0) { throw "Case comparison failed" }
}

Write-Host "Done."
Write-Host "outputs/midterm/rgb_egi_rag_output.json"
Write-Host "reports/egi_case_comparison.md"
Write-Host "reports/member_c_midterm.md"
