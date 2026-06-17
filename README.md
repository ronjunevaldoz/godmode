# Godmode AI System

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/status-stable-green)](https://github.com/ronvaldoz/godmode)

An intelligent AI system with multi-provider support, fallback chains, and Ollama integration.

## Features

- **Multi-Provider Support**: OpenAI, Anthropic, Google, and Ollama
- **Intelligent Fallbacks**: Automatic switching between providers
- **Ollama Integration**: Local LLM support with 6 different models
- **Configurable Retry Logic**: Flexible retry policies
- **Extensible Architecture**: Easy to add new providers

## Quick Start

### Prerequisites

```bash
# Install required packages
pip install -r requirements.txt
```

### Setup

1. **Configure Environment Variables** (create a `.env` file or set directly):
   ```bash
   # Create .env file with your keys
   cp .env.example .env
   
   # Then edit .env to add your actual API keys
   ```

2. **Install Godmode Skills**:
   ```bash
   python godmode_cli.py install-skills
   ```

3. **Run the system**:
   ```bash
   python main.py
   ```

## Configuration

### Ollama Models Available
- `ollama_qwen`: qwen2.5-coder:14b
- `ollama_llama3`: llama3:latest
- `ollama_gemma4`: gemma4:12b
- `ollama_qwen3`: qwen3:8b
- `ollama_qwen3_5`: qwen3.5:4b
- `ollama_deepseek`: deepseek-r1:14b

### Configuration Files
- `configs/api_config.yaml` - Main API configuration
- `configs/fallback_chain.yaml` - Retry and fallback policies

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Input    │───▶│   Routing       │───▶│   Provider      │
│                 │    │   System        │    │   Selection     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Fallback      │
                    │   Chain         │
                    └─────────────────┘
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ronvaldoz/godmode.git
   cd godmode
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Godmode skills:
   ```bash
   python godmode_cli.py install-skills
   ```

## Usage

### Basic Usage
```bash
python main.py
```

### With Custom Configuration
```bash
python main.py --config configs/custom_config.yaml
```

## Environment Variables

The system uses the following environment variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `ANTHROPIC_API_KEY` | Anthropic API key | Yes |
| `GOOGLE_API_KEY` | Google API key | Yes |
| `OLLAMA_BASE_URL` | Ollama server URL | Yes |
| `OLLAMA_API_KEY` | Ollama API key (if required) | No |
| `OLLAMA_MODEL` | Default Ollama model name | No |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please open an issue on GitHub or contact the maintainers.