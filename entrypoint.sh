#!/bin/bash

set -e

# Initialize logging
mkdir -p /app/logs
touch /app/logs/agent.log

# Source environment variables
if [ -f /app/config/.env ]; then
    source /app/config/.env
fi

# Function to handle graceful shutdown
cleanup() {
    echo "Shutting down gracefully..."
    if [ ! -z "$AGENT_PID" ]; then
        kill -TERM "$AGENT_PID" 2>/dev/null || true
        wait "$AGENT_PID" 2>/dev/null || true
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Validate required environment variables
if [ -z "$GEMINI_API_KEY" ]; then
    echo "ERROR: GEMINI_API_KEY environment variable is required"
    exit 1
fi

# Initialize data directory structure
mkdir -p /app/data/{input,output,temp,processed}

echo "Starting Gemini CLI Autonomous Agent..."
echo "Timestamp: $(date)"
echo "Working Directory: $(pwd)"
echo "Data Directory: /app/data"

case "$1" in
    "agent")
        echo "Starting autonomous agent mode..."
        python src/autonomous_agent.py &
        AGENT_PID=$!
        wait $AGENT_PID
        ;;
    "task")
        echo "Running single task: $2"
        python src/task_executor.py --task "$2"
        ;;
    "web")
        echo "Starting web interface..."
        uvicorn src.web_interface:app --host 0.0.0.0 --port 8080 &
        AGENT_PID=$!
        wait $AGENT_PID
        ;;
    "shell")
        echo "Starting interactive shell..."
        /bin/bash
        ;;
    *)
        echo "Usage: $0 {agent|task|web|shell}"
        echo "  agent - Start autonomous agent (default)"
        echo "  task <description> - Execute single task"
        echo "  web - Start web interface"
        echo "  shell - Interactive shell"
        exit 1
        ;;
esac