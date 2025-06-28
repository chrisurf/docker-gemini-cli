# Gemini Autonomous Agent

An autonomous AI agent powered by Google’s Gemini AI, running in a Docker container for automated task execution and data processing.

[![Docker Build](https://github.com/yourusername/gemini-autonomous-agent/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/yourusername/gemini-autonomous-agent/actions/workflows/docker-publish.yml)
[![Docker Pulls](https://img.shields.io/docker/pulls/yourusername/gemini-autonomous-agent)](https://hub.docker.com/r/yourusername/gemini-autonomous-agent)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Features

- **Autonomous Operation**: Continuously monitors for tasks and executes them automatically
- **Gemini AI Integration**: Leverages Google’s powerful Gemini AI for intelligent task processing
- **File-based Task Management**: Simple JSON-based task submission system
- **Data Processing**: Mounted volumes for seamless data input/output
- **Health Monitoring**: Built-in health checks and monitoring
- **Web Interface**: Optional web UI for task management and monitoring
- **Scalable Architecture**: Designed for easy extension and customization
- **Security**: Runs as non-root user with proper container security practices

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Basic Usage

1. **Pull the image:**

```bash
docker pull yourusername/gemini-autonomous-agent:latest
```

1. **Run with environment variables:**

```bash
docker run -d \
  --name gemini-agent \
  -e GEMINI_API_KEY=your_api_key_here \
  -v $(pwd)/data:/app/data \
  yourusername/gemini-autonomous-agent:latest
```

1. **Submit a task:**

```bash
# Create a task file
cat > data/input/task1.json << EOF
{
  "id": "task-001",
  "type": "analysis",
  "task": "Analyze the sales data and provide insights",
  "priority": "high",
  "deadline": "2024-01-15T10:00:00Z"
}
EOF
```

1. **Check results:**

```bash
# Results will appear in data/output/
ls data/output/
cat data/output/task-001_result.json
```

## Configuration

### Environment Variables

|Variable            |Description                |Default     |Required|
|--------------------|---------------------------|------------|--------|
|`GEMINI_API_KEY`    |Google Gemini API key      |-           |✅       |
|`GEMINI_MODEL`      |Gemini model to use        |`gemini-pro`|❌       |
|`GEMINI_TEMPERATURE`|Model temperature (0.0-1.0)|`0.7`       |❌       |
|`GEMINI_MAX_TOKENS` |Maximum output tokens      |`2048`      |❌       |
|`LOG_LEVEL`         |Logging level              |`INFO`      |❌       |

### Volume Mounts

|Container Path       |Purpose       |Description               |
|---------------------|--------------|--------------------------|
|`/app/data/input`    |Task Input    |Place JSON task files here|
|`/app/data/output`   |Results Output|Completed task results    |
|`/app/data/processed`|Archive       |Processed task files      |
|`/app/logs`          |Logging       |Application               |
