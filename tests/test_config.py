"""Tests for configuration management."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from src.config import (
    ModelConfig,
    EvalConfig,
    load_config_from_yaml,
    save_config_to_yaml,
    _apply_env_overrides
)


class TestModelConfig:
    """Tests for ModelConfig."""
    
    def test_valid_model_config(self):
        """Test creating a valid ModelConfig."""
        config = ModelConfig(
            provider="openai",
            model_name="gpt-4o",
            temperature=0.7,
            max_tokens=2000
        )
        
        assert config.provider == "openai"
        assert config.model_name == "gpt-4o"
        assert config.temperature == 0.7
        assert config.max_tokens == 2000
    
    def test_invalid_provider(self):
        """Test that invalid provider raises error."""
        with pytest.raises(ValueError, match="Provider must be one of"):
            ModelConfig(
                provider="invalid_provider",
                model_name="test-model"
            )
    
    def test_provider_case_insensitive(self):
        """Test that provider is case-insensitive."""
        config = ModelConfig(
            provider="OpenAI",
            model_name="gpt-4o"
        )
        assert config.provider == "openai"
    
    def test_temperature_validation(self):
        """Test temperature bounds validation."""
        # Valid temperatures
        ModelConfig(provider="openai", model_name="gpt-4o", temperature=0.0)
        ModelConfig(provider="openai", model_name="gpt-4o", temperature=2.0)
        
        # Invalid temperatures
        with pytest.raises(ValueError):
            ModelConfig(provider="openai", model_name="gpt-4o", temperature=-0.1)
        
        with pytest.raises(ValueError):
            ModelConfig(provider="openai", model_name="gpt-4o", temperature=2.1)
    
    def test_get_api_key_default(self):
        """Test getting API key from default environment variable."""
        os.environ['OPENAI_API_KEY'] = 'test-key-123'
        
        config = ModelConfig(
            provider="openai",
            model_name="gpt-4o"
        )
        
        assert config.get_api_key() == 'test-key-123'
        
        # Cleanup
        del os.environ['OPENAI_API_KEY']
    
    def test_get_api_key_custom(self):
        """Test getting API key from custom environment variable."""
        os.environ['CUSTOM_API_KEY'] = 'custom-key-456'
        
        config = ModelConfig(
            provider="openai",
            model_name="gpt-4o",
            api_key_env="CUSTOM_API_KEY"
        )
        
        assert config.get_api_key() == 'custom-key-456'
        
        # Cleanup
        del os.environ['CUSTOM_API_KEY']


class TestEvalConfig:
    """Tests for EvalConfig."""
    
    def test_valid_eval_config(self):
        """Test creating a valid EvalConfig."""
        model_config = ModelConfig(
            provider="openai",
            model_name="gpt-4o"
        )
        
        config = EvalConfig(
            model=model_config,
            judge_model="claude-3-5-sonnet-20241022",
            golden_dataset_path="data/golden_dataset.json"
        )
        
        assert config.model.provider == "openai"
        assert config.judge_model == "claude-3-5-sonnet-20241022"
        assert config.min_accuracy == 0.75  # default
    
    def test_threshold_validation(self):
        """Test metric threshold validation."""
        model_config = ModelConfig(provider="openai", model_name="gpt-4o")
        
        # Valid thresholds
        EvalConfig(
            model=model_config,
            min_accuracy=0.5,
            min_faithfulness=0.9,
            min_safety_score=3.5
        )
        
        # Invalid accuracy (out of range)
        with pytest.raises(ValueError):
            EvalConfig(
                model=model_config,
                min_accuracy=1.5
            )
        
        # Invalid safety score (out of range)
        with pytest.raises(ValueError):
            EvalConfig(
                model=model_config,
                min_safety_score=6.0
            )
    
    def test_get_langsmith_api_key(self):
        """Test getting LangSmith API key."""
        os.environ['LANGSMITH_API_KEY'] = 'langsmith-key-789'
        
        model_config = ModelConfig(provider="openai", model_name="gpt-4o")
        config = EvalConfig(model=model_config)
        
        assert config.get_langsmith_api_key() == 'langsmith-key-789'
        
        # Cleanup
        del os.environ['LANGSMITH_API_KEY']


class TestYAMLLoading:
    """Tests for YAML configuration loading."""
    
    def test_load_valid_yaml(self):
        """Test loading a valid YAML configuration."""
        yaml_content = """
model:
  provider: openai
  model_name: gpt-4o
  temperature: 0.7
  max_tokens: 2000

judge_model: claude-3-5-sonnet-20241022
golden_dataset_path: data/golden_dataset.json
output_dir: ./eval_results
langsmith_project: test-project
min_accuracy: 0.80
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            config = load_config_from_yaml(temp_path)
            
            assert config.model.provider == "openai"
            assert config.model.model_name == "gpt-4o"
            assert config.judge_model == "claude-3-5-sonnet-20241022"
            assert config.min_accuracy == 0.80
        finally:
            os.unlink(temp_path)
    
    def test_load_nonexistent_file(self):
        """Test loading a non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_config_from_yaml("nonexistent_file.yaml")
    
    def test_load_invalid_yaml(self):
        """Test loading invalid YAML raises error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content:")
            temp_path = f.name
        
        try:
            with pytest.raises((ValueError, yaml.scanner.ScannerError)):
                load_config_from_yaml(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_save_and_load_roundtrip(self):
        """Test saving and loading configuration."""
        model_config = ModelConfig(
            provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.5
        )
        
        original_config = EvalConfig(
            model=model_config,
            judge_model="gpt-4o",
            min_accuracy=0.85
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            # Save
            save_config_to_yaml(original_config, temp_path)
            
            # Load
            loaded_config = load_config_from_yaml(temp_path)
            
            # Verify
            assert loaded_config.model.provider == "anthropic"
            assert loaded_config.model.temperature == 0.5
            assert loaded_config.judge_model == "gpt-4o"
            assert loaded_config.min_accuracy == 0.85
        finally:
            os.unlink(temp_path)


class TestEnvironmentOverrides:
    """Tests for environment variable overrides."""
    
    def test_model_config_overrides(self):
        """Test model config environment overrides."""
        config_dict = {
            'model': {
                'provider': 'openai',
                'model_name': 'gpt-4o',
                'temperature': 0.7
            }
        }
        
        os.environ['EVAL_MODEL_PROVIDER'] = 'anthropic'
        os.environ['EVAL_MODEL_NAME'] = 'claude-3-5-sonnet-20241022'
        os.environ['EVAL_MODEL_TEMPERATURE'] = '0.5'
        
        try:
            updated = _apply_env_overrides(config_dict)
            
            assert updated['model']['provider'] == 'anthropic'
            assert updated['model']['model_name'] == 'claude-3-5-sonnet-20241022'
            assert updated['model']['temperature'] == 0.5
        finally:
            del os.environ['EVAL_MODEL_PROVIDER']
            del os.environ['EVAL_MODEL_NAME']
            del os.environ['EVAL_MODEL_TEMPERATURE']
    
    def test_top_level_overrides(self):
        """Test top-level environment overrides."""
        config_dict = {
            'model': {
                'provider': 'openai',
                'model_name': 'gpt-4o'
            },
            'min_accuracy': 0.75,
            'verbose': False
        }
        
        os.environ['MIN_ACCURACY'] = '0.90'
        os.environ['EVAL_VERBOSE'] = 'true'
        
        try:
            updated = _apply_env_overrides(config_dict)
            
            assert updated['min_accuracy'] == 0.90
            assert updated['verbose'] is True
        finally:
            del os.environ['MIN_ACCURACY']
            del os.environ['EVAL_VERBOSE']
    
    def test_no_overrides_when_not_set(self):
        """Test that config is unchanged when env vars not set."""
        config_dict = {
            'model': {
                'provider': 'openai',
                'model_name': 'gpt-4o',
                'temperature': 0.7
            },
            'min_accuracy': 0.75
        }
        
        updated = _apply_env_overrides(config_dict.copy())
        
        assert updated == config_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
