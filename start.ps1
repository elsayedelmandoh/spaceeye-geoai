# Starts the chatbot (port 8001) and the dashboard (port 8501) on Windows.
# Run from the repository root: powershell -ExecutionPolicy Bypass -File .\start.ps1
Set-Location $PSScriptRoot
Remove-Item Env:VIRTUAL_ENV -ErrorAction SilentlyContinue

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv is not installed. Install it, open a new terminal, and run this script again:"
    Write-Host '  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"'
    exit 1
}

if (-not (Test-Path "chatbot\.env")) {
    Copy-Item "chatbot\.env.example" "chatbot\.env"
    Write-Host "Created chatbot\.env. Open it, put the Gemini key after GEMINI_API_KEY=, then run this script again."
    exit 1
}

uv sync --locked --extra chatbot
if ($LASTEXITCODE -ne 0) { exit 1 }

# Prepared data: install once; a second install over different data would stop, so skip when it exists.
$appData = uv run --locked --extra chatbot python -c "from src.pipeline.common import APP; print(APP)" | Select-Object -Last 1
if (-not (Test-Path (Join-Path $appData "real\kpi_values.parquet"))) {
    uv run --locked --extra chatbot python -m src.pipeline.setup_review
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

# Search index: Chroma writes to its file while running, so start from the committed seed copy.
if (-not (Test-Path "chatbot\vector_db\chroma.sqlite3")) {
    New-Item -ItemType Directory -Force "chatbot\vector_db" | Out-Null
    Copy-Item "chatbot\vector_db_seed\chroma.sqlite3" "chatbot\vector_db\chroma.sqlite3"
}

Start-Process powershell -WorkingDirectory $PSScriptRoot -ArgumentList "-NoExit", "-Command",
    "uv run --locked --extra chatbot uvicorn chatbot.app.api.main:app --port 8001"
uv run --locked --extra chatbot streamlit run app.py
