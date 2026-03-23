#!/bin/bash
# Start the Nga J1 Pipeline server
# Usage: ./start.sh [port]
PORT=${1:-4005}
cd "$(dirname "$0")"
pip install -q -r requirements.txt
uvicorn api:app --host 0.0.0.0 --port $PORT --reload
