# Skills Directory

This directory contains all the skills available to the godmode agent system. Skills are organized into logical categories to improve maintainability and discoverability.

## Structure

- `skills/core/` - Core agent capabilities and fundamental skills
- `skills/utilities/` - Utility functions and helper methods  
- `skills/analysis/` - Analytical and data processing skills
- `skills/communication/` - Communication and interaction skills
- `skills/tools/` - Tool integration and external service skills
- `skills/helpers/` - Supporting helper functions

## Adding New Skills

When adding new skills:
1. Place them in the appropriate subdirectory based on their functionality
2. Follow the naming convention: `skill_name.py`
3. Include proper documentation and type hints
4. Ensure they follow the existing code style

## Installing Skills

Skills can be installed using the following methods:

### Via .gemini file
Create a `.gemini` file in your project root with:
\`\`\`json
{
  "skills": [
    "analysis_skill",
    "code_generation_skill"
  ]
}
\`\`\`

### Via .claude file  
Create a `.claude` file in your project root with:
\`\`\`json
{
  "skills": [
    "architecture_skill",
    "documentation_skill"
  ]
}
\`\`\`

### Via .agent file
Create an `.agent` file in your project root with:
\`\`\`json
{
  "skill_imports": [
    "skills.analysis.analysis_skill",
    "skills.communication.code_review_skill"
  ]
}
\`\`\`

## Usage

Skills can be imported and used throughout the agent system:

```python
from skills.core import some_core_skill
```

