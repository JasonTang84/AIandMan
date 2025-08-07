#!/usr/bin/env python3
"""
Simple launcher script for AIandMan application
"""

import subprocess
import sys
import os

def main():
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  Warning: .env file not found!")
        print("Please copy .env.example to .env and add your OpenAI API key:")
        print("cp .env.example .env")
        print()
    
    # Run the Streamlit app
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running application: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()