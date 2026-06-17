# GodMode AI System

An intelligent routing and execution system that automatically selects the best AI model for each task based on intent, capabilities, and privacy considerations.

## Overview

GodMode is a sophisticated AI system designed to intelligently route tasks to the most appropriate AI models. It uses a three-layer architecture:
1. **L1 Router**: Intent classification and capability mapping
2. **L2 Executor**: Model selection and execution with fallback strategies  
3. **L3 Governor**: Optional validation and escalation

## Key Features

- **Capability-Based Routing**: Automatically matches tasks to models with required capabilities
- **Local-First Policy**: Prefers local processing for privacy and performance
- **Intelligent Fallbacks**: Robust error handling with defined fallback chains
- **Skills System**: Extensible skill-based approach for system functionality
- **Privacy Considerations**: Built-in privacy-aware model selection

## Architecture

### Layer 1: Router
- Uses Ollama for intent classification
- Maps intents to required capabilities via `intent_map.json`
- Provides confidence scoring for intent classification

### Layer 2: Executor  
- Model registry in `configs/model_registry.yaml`
- Capability matching and model selection algorithm
- Fallback chain implementation

### Layer 3: Governor (Optional)
- Quality validation and final checks
- Complex request escalation
- Performance metrics collection

## Capabilities

The system supports these core capabilities:
- `code_execution`: Code generation and execution
- `repo_awareness`: Repository structure understanding  
- `architecture_review`: System design analysis
- `documentation_generation`: Technical documentation creation
- `multimodal_understanding`: Image/video processing
- `long_context_reasoning`: Large context window handling
- `final_validation`: Quality checks and validation
- `private_local_processing`: Local privacy-focused processing
- `cheap_batch_processing`: Efficient batch operations

## Skills System

Skills are located in the `skills/` directory and include:
- `analysis_skill.md`
- `architecture_skill.md`
- `code_generation_skill.md`
- `code_review_skill.md`
- `documentation_skill.md`

Each skill is defined as a markdown file with:
- Description of capabilities
- Provider configuration
- Usage examples
- Required parameters

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Ollama with required models:
```bash
# Install Ollama from https://ollama.com/download
# Pull required models
ollama pull qwen2.5-coder:14b
ollama pull llama3.2:1b
```

3. Install skills system:
```bash
python godmode_cli.py install-skills
```

## Usage

### Basic Usage:
```bash
python main.py "Create a Python function to calculate Fibonacci numbers"
```

### Advanced Usage:
```bash
# List available skills
python godmode_cli.py skills

# Run with specific intent
python main.py "Design a microservices architecture for an e-commerce platform"
```

## System Components

- `main.py`: Main execution entry point
- `godmode_cli.py`: Command-line interface for system management
- `configs/model_registry.yaml`: Model configuration and capabilities
- `routing/intent_map.json`: Intent to capability mapping
- `skills/`: Skill definitions and implementations
- `docs/system_overview.md`: Complete system documentation

## Security & Privacy

The system follows a local-first policy:
- Local processing preferred when capabilities allow it
- Cloud models used only when local processing is insufficient  
- All data handling follows security best practices
- Privacy considerations built into model selection process

## Performance Optimization

Model selection uses a scoring system that considers:
1. Capability match (max 100 points)
2. Privacy preference (max 50 points)
3. Multimodal support (max 50 points) 
4. Cost tier (max 20 points)
5. Latency tier (max 15 points)
6. Context window (max 10 points)

## Extensibility

The system is designed to be easily extended:
- Add new models to `model_registry.yaml`
- Create new skills in `skills/` 
- Extend capabilities and intents
- Customize fallback strategies

## Testing

```bash
# Test basic functionality
python main.py "Generate a React component for user authentication"

# Test with specific intent
python main.py "Analyze this sales dataset and identify key trends"
```

For more detailed system information, see `docs/system_overview.md`.