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
    skills_dir = Path("skills")
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
    print("Skills configuration saved to skills/godmode_skills.json")

def list_skills():
    """List all available skills"""
    skills_dir = Path("skills")
    
    if not skills_dir.exists():
        print("No skills directory found. Run 'install-skills' first.")
        return
    
    # List skill files
    skill_files = list(skills_dir.glob("*.md"))
    
    if not skill_files:
        print("No skills found in skills/")
        return
    
    print("\nAvailable Skills:")
    print("=" * 50)
    
    for skill_file in skill_files:
        try:
            with open(skill_file, 'r') as f:
                content = f.read()
                # Extract skill name from filename
                skill_name = skill_file.stem.replace('_', ' ').title()
                print(f"• {skill_name}")
                # Show first line of description if available
                lines = content.split('\n')
                for line in lines:
                    if line.startswith('## Description'):
                        desc_line = next((l for l in lines[lines.index(line)+1:] if l.strip()), "")
                        if desc_line:
                            print(f"  {desc_line}")
                        break
                print()
        except Exception as e:
            print(f"Error reading {skill_file}: {e}")

def main():
    """Main CLI entry point"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "install-skills":
            install_skills()
        elif sys.argv[1] == "skills":
            list_skills()
        else:
            print("Godmode CLI Tool")
            print("Usage: python godmode_cli.py install-skills")
            print("       python godmode_cli.py skills")
            print("       python godmode_cli.py --help")
    else:
        print("Godmode CLI Tool")
        print("Usage: python godmode_cli.py install-skills")
        print("       python godmode_cli.py skills")
        print("       python godmode_cli.py --help")

if __name__ == "__main__":
    main()