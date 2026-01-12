#!/usr/bin/env python3

import os
import sys
from datetime import datetime


def main():
    print("=" * 60)
    print("Oracle - Macro Research Agent Setup")
    print("=" * 60)
    print()

    print("Checking project structure...")
    required_dirs = [
        "backend",
        "backend/agents",
        "backend/data",
        "backend/models",
        "backend/storage",
        "backend/scheduler",
        "backend/templates",
        "backend/delivery",
        "backend/cli",
        "backend/config",
        "reports/daily",
        "reports/weekly",
        "data",
    ]

    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"  ✓ {dir_path}")
        else:
            os.makedirs(dir_path, exist_ok=True)
            print(f"  + Created {dir_path}")

    print()
    print("Checking configuration...")
    if os.path.exists(".env"):
        print("  ✓ .env file found")
    else:
        print("  + .env file not found - copying from .env.example")
        if os.path.exists(".env.example"):
            import shutil

            shutil.copy(".env.example", ".env")
            print("  ✓ .env created from example")
            print("  ⚠️  Please edit .env with your API keys!")
        else:
            print("  ✗ .env.example not found!")
            return 1

    print()
    print("Project structure ready!")
    print()
    print("Next steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Configure API keys in .env file")
    print("3. Run the application:")
    print("   - API server: python -m backend.main")
    print("   - Generate daily report: python -m backend.cli daily")
    print("   - On-demand research: python -m backend.cli research 'your query'")
    print("   - Check status: python -m backend.cli status")
    print()
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
