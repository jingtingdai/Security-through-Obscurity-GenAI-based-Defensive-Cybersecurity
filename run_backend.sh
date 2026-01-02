#!/bin/bash
# Script to run the FastAPI backend with the correct virtual environment

cd "$(dirname "$0")"

# Activate virtual environment
source app/.venv/bin/activate

# Change to backend directory
cd app/backend

# Run uvicorn
echo "Starting FastAPI backend on http://localhost:8000"
echo "API docs available at http://localhost:8000/docs"
echo "Press CTRL+C to stop"
echo ""

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

