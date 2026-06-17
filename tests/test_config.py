"""Configuration tests for the godmode AI system."""

import os
import yaml


def test_config_loading():
    """Test that api_config.yaml loads and has required sections."""
    with open('configs/api_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    assert 'ollama' in config, "Ollama section missing"
    assert 'models' in config, "Models section missing"
    assert 'base_url' in config['ollama'], "Ollama base_url missing"
    assert len(config['models']) > 0, "No models configured"
    ollama_models = [k for k in config['models'] if 'ollama' in k]
    assert len(ollama_models) > 0, "No Ollama models found"


def test_fallback_chain():
    """Test that fallback_chain.yaml loads and has required keys."""
    with open('configs/fallback_chain.yaml', 'r') as f:
        fallback_config = yaml.safe_load(f)

    assert 'retry_policies' in fallback_config, "Retry policies missing"
    assert 'default_fallback' in fallback_config, "Default fallback missing"
