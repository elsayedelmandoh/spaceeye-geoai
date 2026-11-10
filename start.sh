#!/usr/bin/env bash
# Starts the chatbot (port 8001) and the dashboard (port 8501) on Linux/WSL.
# Run from anywhere: ./start.sh
set -euo pipefail
cd "$(dirname "$0")"
unset VIRTUAL_ENV

if ! command -v uv >/dev/null; then
    echo "uv is not installed. Install it, open a new terminal, and run this script again:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env. Open it, put the Gemini key after GEMINI_API_KEY=, then run this script again."
    exit 1
fi

uv sync --locked --extra chatbot

# Prepared data: install once; a second install over different data would stop, so skip when it exists.
app_data=$(uv run --locked --extra chatbot python -c "from src.pipeline.common import APP; print(APP)" | tail -n 1)
if [ ! -f "$app_data/real/kpi_values.parquet" ]; then
    uv run --locked --extra chatbot python -m src.pipeline.setup_review
fi

# Search index: Chroma writes to its file while running, so start from the committed seed copy.
if [ ! -f chatbot/vector_db/chroma.sqlite3 ]; then
    mkdir -p chatbot/vector_db
    cp chatbot/vector_db_seed/chroma.sqlite3 chatbot/vector_db/chroma.sqlite3
fi

uv run --locked --extra chatbot uvicorn chatbot.app.api.main:app \
    --host 127.0.0.1 --port 8001 >chatbot/chatbot.log 2>&1 &
chatbot_pid=$!
trap 'kill "$chatbot_pid" 2>/dev/null || true' EXIT

for _ in $(seq 60); do
    curl -fs http://127.0.0.1:8001/health >/dev/null 2>&1 && break
    kill -0 "$chatbot_pid" 2>/dev/null || { echo "Chatbot stopped; see chatbot/chatbot.log"; exit 1; }
    sleep 2
done

uv run --locked --extra chatbot streamlit run app.py --server.port 8501
