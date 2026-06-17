#!/usr/bin/env python3
"""
Godmode CLI Tool for managing AI system
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def install_skills():
    """Install Godmode skills and configurations"""
    print("Installing Godmode skills...")
    
    # Create skills directory if it doesn't exist
    skills_dir = Path(".continue/agents")
    skills_dir.mkdir(parents=True, exist_ok=True)
    
    # Sample skills configuration
    skills_config = {
        "skills": [
            {
                "name": "code_generation",
                "description": "Generate code solutions",
                "provider": "ollama_qwen"
            },
            {
                "name": "documentation",
                "description": "Create documentation",
                "provider": "ollama_llama3"
            },
            {
                "name": "analysis",
                "description": "Data analysis and insights",
                "provider": "ollama_gemma4"
            }
        ],
        "default_provider": "ollama_qwen"
    }
    
    # Save skills configuration
    with open(skills_dir / "godmode_skills.json", "w") as f:
        json.dump(skills_config, f, indent=2)
    
    print("✓ Godmode skills installed successfully")
    print("Skills configuration saved to .continue/agents/godmode_skills.json")

def main():
    """Main CLI entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "install-skills":
        install_skills()
    else:
        print("Godmode CLI Tool")
        print("Usage: python godmode_cli.py install-skills")
        print("       python godmode_cli.py --help")

if __name__ == "__main__":
    main()