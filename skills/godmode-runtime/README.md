# Godmode Runtime Skills

This directory contains all the skills available to the godmode runtime agent system. Skills are organized into logical categories to improve maintainability and discoverability.

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

## Usage

Skills can be imported and used throughout the agent system:

```python
from godmode_runtime.skills.core import some_core_skill
```

