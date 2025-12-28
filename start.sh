#!/bin/bash
# DataPulse Startup Script (Linux/macOS)
# Usage: ./start.sh

echo "========================================"
echo "   DataPulse - AI-Powered Analytics    "
echo "========================================"
echo ""

# Check Python
PYTHON_PATH="./venv/bin/python"
if [ ! -f "$PYTHON_PATH" ]; then
    echo "[ERROR] Virtual environment not found!"
    echo "Run: python3 -m venv venv"
    echo "Then: source venv/bin/activate"
    echo "Then: pip install -r backend/requirements.txt"
    exit 1
fi

# Check .env
if [ ! -f ".env" ]; then
    echo "[WARNING] .env file not found!"
    echo "Copying from .env.example..."
    cp .env.example .env
    echo "[INFO] Please edit .env and add your GOOGLE_API_KEY"
fi

# Check database
if [ ! -f "data/database/datapulse.db" ]; then
    echo "[INFO] Database not found, populating..."
    $PYTHON_PATH data/populate_db.py
fi

echo ""
echo "Starting DataPulse via scripts/run_local.py"
./venv/bin/python ./scripts/run_local.py

echo "Launcher exited. If you want to run services in background, consider using screen/tmux or modify this script."
