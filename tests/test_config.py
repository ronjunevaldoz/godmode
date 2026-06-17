"""
Configuration test for AI system
"""

import sys
import os
import yaml

def test_config_loading():
    """Test that configuration loads properly"""
    try:
        # Load config directly
        with open('configs/api_config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Verify required sections exist
        assert 'ollama' in config, "Ollama section missing"
        assert 'models' in config, "Models section missing"
        
        # Check Ollama configuration
        ollama_config = config['ollama']
        assert 'base_url' in ollama_config, "Ollama base_url missing"
        
        # Check models structure
        models = config['models']
        assert len(models) > 0, "No models configured"
        
        # Verify Ollama models are present
        ollama_models = [k for k in models.keys() if 'ollama' in k]
        assert len(ollama_models) > 0, "No Ollama models found"
        
        print("✓ Configuration test passed")
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def test_fallback_chain():
    """Test that fallback chain loads properly"""
    try:
        with open('configs/fallback_chain.yaml', 'r') as f:
            fallback_config = yaml.safe_load(f)
        
        assert 'retry_policies' in fallback_config, "Retry policies missing"
        assert 'default_fallback' in fallback_config, "Default fallback missing"
        
        print("✓ Fallback chain test passed")
        return True
        
    except Exception as e:
        print(f"✗ Fallback chain test failed: {e}")
        return False

if __name__ == "__main__":
    success1 = test_config_loading()
    success2 = test_fallback_chain()
    
    if success1 and success2:
        print("\n🎉 All configuration tests passed!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)