"""Tests for LangSmith tracer."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.langsmith_tracer import (
    LangSmithTracer,
    create_langsmith_tracer,
    load_golden_dataset_to_langsmith
)


class TestLangSmithTracer:
    """Tests for LangSmithTracer class."""
    
    @patch('src.langsmith_tracer.Client')
    def test_initialization_with_api_key(self, mock_client):
        """Test initializing tracer with API key."""
        tracer = LangSmithTracer(
            project_name="test-project",
            api_key="test-key"
        )
        
        assert tracer.project_name == "test-project"
        mock_client.assert_called_once_with(api_key="test-key")
    
    @patch('langsmith.Client')
    def test_initialization_from_env(self, mock_client):
        """Test initializing tracer from environment variable."""
        with patch.dict('os.environ', {'LANGSMITH_API_KEY': 'env-key'}):
            tracer = LangSmithTracer(project_name="test-project")
            assert tracer.project_name == "test-project"
    
    def test_initialization_missing_api_key(self):
        """Test that missing API key raises error."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="API key not found"):
                LangSmithTracer(project_name="test-project")
    
    @patch('langsmith.Client')
    def test_create_dataset_new(self, mock_client_class):
        """Test creating a new dataset."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock no existing datasets
        mock_client.list_datasets.return_value = iter([])
        
        # Mock dataset creation
        mock_dataset = Mock()
        mock_dataset.id = "dataset-123"
        mock_client.create_dataset.return_value = mock_dataset
        
        tracer = LangSmithTracer(project_name="test", api_key="test-key")
        tracer.client = mock_client
        
        dataset_id = tracer.create_dataset("test-dataset", "Test description")
        
        assert dataset_id == "dataset-123"
        mock_client.create_dataset.assert_called_once()
    
    @patch('langsmith.Client')
    def test_create_dataset_existing(self, mock_client_class):
        """Test that existing dataset is reused."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock existing dataset
        mock_dataset = Mock()
        mock_dataset.id = "existing-123"
        mock_client.list_datasets.return_value = iter([mock_dataset])
        
        tracer = LangSmithTracer(project_name="test", api_key="test-key")
        tracer.client = mock_client
        
        dataset_id = tracer.create_dataset("test-dataset")
        
        assert dataset_id == "existing-123"
        mock_client.create_dataset.assert_not_called()
    
    @patch('langsmith.Client')
    def test_add_examples(self, mock_client_class):
        """Test adding examples to dataset."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock dataset
        mock_dataset = Mock()
        mock_dataset.id = "dataset-123"
        mock_client.list_datasets.return_value = iter([mock_dataset])
        
        # Mock example creation
        mock_example = Mock()
        mock_example.id = "example-456"
        mock_client.create_example.return_value = mock_example
        
        tracer = LangSmithTracer(project_name="test", api_key="test-key")
        tracer.client = mock_client
        
        examples = [
            {
                "inputs": {"question": "What is 2+2?"},
                "outputs": {"answer": "4"}
            }
        ]
        
        example_ids = tracer.add_examples("test-dataset", examples)
        
        assert len(example_ids) == 1
        assert example_ids[0] == "example-456"
        mock_client.create_example.assert_called_once()
    
    @patch('src.langsmith_tracer.Client')
    def test_add_examples_invalid_format(self, mock_client_class):
        """Test that invalid example format raises error."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock dataset
        mock_dataset = Mock()
        mock_dataset.id = "dataset-123"
        mock_client.list_datasets.return_value = iter([mock_dataset])
        
        tracer = LangSmithTracer(project_name="test", api_key="test-key")
        tracer.client = mock_client
        
        # Missing 'outputs' key
        invalid_examples = [
            {"inputs": {"question": "test"}}
        ]
        
        with pytest.raises(Exception, match="Failed to add examples"):
            tracer.add_examples("test-dataset", invalid_examples)
    
    @patch('langsmith.Client')
    def test_get_traces(self, mock_client_class):
        """Test retrieving traces."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock runs
        mock_run1 = Mock()
        mock_run1.id = "run-1"
        mock_run2 = Mock()
        mock_run2.id = "run-2"
        mock_client.list_runs.return_value = iter([mock_run1, mock_run2])
        
        tracer = LangSmithTracer(project_name="test", api_key="test-key")
        tracer.client = mock_client
        
        runs = tracer.get_traces(limit=10)
        
        assert len(runs) == 2
        mock_client.list_runs.assert_called_once()
    
    @patch('langsmith.Client')
    def test_get_trace_metadata(self, mock_client_class):
        """Test extracting metadata from trace."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        tracer = LangSmithTracer(project_name="test", api_key="test-key")
        
        # Create mock run
        mock_run = Mock()
        mock_run.id = "run-123"
        mock_run.name = "test-run"
        mock_run.run_type = "llm"
        mock_run.start_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_run.end_time = datetime(2024, 1, 1, 12, 0, 2)
        mock_run.error = None
        mock_run.outputs = {
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50,
                "total_tokens": 150
            }
        }
        mock_run.extra = {"metadata": {"case_id": "test-001"}}
        
        metadata = tracer.get_trace_metadata(mock_run)
        
        assert metadata["run_id"] == "run-123"
        assert metadata["name"] == "test-run"
        assert metadata["latency_ms"] == 2000.0
        assert metadata["tokens"]["total"] == 150
        assert metadata["metadata"]["case_id"] == "test-001"


class TestFactoryFunction:
    """Tests for factory function."""
    
    @patch('langsmith.Client')
    def test_create_langsmith_tracer(self, mock_client):
        """Test factory function creates tracer."""
        tracer = create_langsmith_tracer(
            project_name="test-project",
            api_key="test-key"
        )
        
        assert isinstance(tracer, LangSmithTracer)
        assert tracer.project_name == "test-project"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
