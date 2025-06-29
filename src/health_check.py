#!/usr/bin/env python3
"""
Health Check for Gemini Autonomous Agent
Performs basic health checks for the application
"""

import asyncio
import sys
from pathlib import Path

import structlog

from config_manager import ConfigManager
from gemini_client import GeminiClient

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

logger = structlog.get_logger()


async def check_gemini_api():
    """Check Gemini API connectivity"""
    try:
        client = GeminiClient()
        return await client.health_check()
    except Exception as e:
        logger.error("Gemini API check failed", error=str(e))
        return False


def check_directories():
    """Check required directories exist"""
    required_dirs = [
        "/app/data/input",
        "/app/data/output",
        "/app/data/processed",
        "/app/logs",
    ]

    for directory in required_dirs:
        if not Path(directory).exists():
            logger.error("Required directory missing", directory=directory)
            return False

    return True


def check_environment():
    """Check required environment variables"""
    try:
        config = ConfigManager()
        return bool(config.get("gemini_api_key"))
    except Exception as e:
        logger.error("Environment check failed", error=str(e))
        return False


async def main():
    """Main health check function"""
    checks = {
        "directories": check_directories(),
        "environment": check_environment(),
        "gemini_api": await check_gemini_api(),
    }

    all_passed = all(checks.values())

    if all_passed:
        print("✅ All health checks passed")
        sys.exit(0)
    else:
        print("❌ Health checks failed:")
        for check, status in checks.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {check}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
