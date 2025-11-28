"""Unit tests for CLI interface."""

import pytest
import sys
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import the CLI module
import evaluate


def test_parse_arguments_basic():
    """Test basic argument parsing."""
    test_args = ['evaluate.py', '--config', 'config/test.yaml']
    
    with patch.object(sys, 'argv', test_args):
        args = evaluate.parse_arguments()
        
        assert args.config == 'config/test.yaml'
        assert args.dataset is None
        assert args.verbose is False


def test_parse_arguments_all_flags():
    """Test parsing all available flags."""
    test_args = [
        'evaluate.py',
        '--config', 'config/test.yaml',
        '--dataset', 'data/test.json',
        '--output-dir', './output',
        '--subset', '10',
        '--verbose',
        '--no-dashboard',
        '--no-reports'
    ]
    
    with patch.object(sys, 'argv', test_args):
        args = evaluate.parse_arguments()
        
        assert args.config == 'config/test.yaml'
        assert args.dataset == 'data/test.json'
        assert args.output_dir == './output'
        assert args.subset == 10
        assert args.verbose is True
        assert args.no_dashboard is True
        assert args.no_reports is True


def test_parse_arguments_missing_required():
    """Test that missing required arguments raises error."""
    test_args = ['evaluate.py']  # Missing --config
    
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit):
            evaluate.parse_arguments()


def test_main_with_mock_evaluator():
    """Test main function with mocked evaluator."""
    test_args = ['evaluate.py', '--config', 'config/test.yaml', '--no-dashboard', '--no-reports']
    
    # Create mock results
    mock_results = Mock()
    mock_results.metrics = {
        "total_cases": 10,
        "successful_cases": 10,
        "all_thresholds_met": True,
        "thresholds_met": {}
    }
    mock_results.case_results = []
    
    # Create mock config
    mock_config = Mock()
    mock_config.output_dir = "./test_output"
    mock_config.golden_dataset_path = "data/test.json"
    mock_config.subset_size = None
    mock_config.verbose = False
    
    with patch.object(sys, 'argv', test_args), \
         patch('evaluate.load_config_from_yaml', return_value=mock_config), \
         patch('evaluate.Evaluator') as mock_evaluator_class:
        
        # Setup mock evaluator instance
        mock_evaluator = Mock()
        mock_evaluator.run_evaluation.return_value = mock_results
        mock_evaluator_class.return_value = mock_evaluator
        
        exit_code = evaluate.main()
        
        assert exit_code == 0  # Success
        assert mock_evaluator.run_evaluation.called


def test_main_with_failed_thresholds():
    """Test main function when thresholds fail."""
    test_args = ['evaluate.py', '--config', 'config/test.yaml', '--no-dashboard', '--no-reports']
    
    # Create mock results with failed thresholds
    mock_results = Mock()
    mock_results.metrics = {
        "total_cases": 10,
        "successful_cases": 10,
        "all_thresholds_met": False,
        "thresholds_met": {
            "accuracy": True,
            "safety": False
        }
    }
    mock_results.case_results = []
    
    mock_config = Mock()
    mock_config.output_dir = "./test_output"
    mock_config.golden_dataset_path = "data/test.json"
    mock_config.subset_size = None
    mock_config.verbose = False
    
    with patch.object(sys, 'argv', test_args), \
         patch('evaluate.load_config_from_yaml', return_value=mock_config), \
         patch('evaluate.Evaluator') as mock_evaluator_class:
        
        mock_evaluator = Mock()
        mock_evaluator.run_evaluation.return_value = mock_results
        mock_evaluator_class.return_value = mock_evaluator
        
        exit_code = evaluate.main()
        
        assert exit_code == 1  # Failure


def test_main_with_file_not_found():
    """Test main function handles file not found error."""
    test_args = ['evaluate.py', '--config', 'nonexistent.yaml']
    
    with patch.object(sys, 'argv', test_args), \
         patch('evaluate.load_config_from_yaml', side_effect=FileNotFoundError("File not found")):
        
        exit_code = evaluate.main()
        
        assert exit_code == 2  # Configuration error


def test_main_with_value_error():
    """Test main function handles value error."""
    test_args = ['evaluate.py', '--config', 'config/test.yaml']
    
    with patch.object(sys, 'argv', test_args), \
         patch('evaluate.load_config_from_yaml', side_effect=ValueError("Invalid config")):
        
        exit_code = evaluate.main()
        
        assert exit_code == 2  # Configuration error


def test_main_with_keyboard_interrupt():
    """Test main function handles keyboard interrupt."""
    test_args = ['evaluate.py', '--config', 'config/test.yaml']
    
    mock_config = Mock()
    mock_config.output_dir = "./test_output"
    
    with patch.object(sys, 'argv', test_args), \
         patch('evaluate.load_config_from_yaml', return_value=mock_config), \
         patch('evaluate.Evaluator', side_effect=KeyboardInterrupt()):
        
        exit_code = evaluate.main()
        
        assert exit_code == 130  # Interrupted


def test_main_applies_command_line_overrides():
    """Test that command-line arguments override config."""
    test_args = [
        'evaluate.py',
        '--config', 'config/test.yaml',
        '--dataset', 'custom_data.json',
        '--output-dir', './custom_output',
        '--subset', '5',
        '--verbose',
        '--no-dashboard',
        '--no-reports'
    ]
    
    mock_results = Mock()
    mock_results.metrics = {
        "total_cases": 5,
        "successful_cases": 5,
        "all_thresholds_met": True,
        "thresholds_met": {}
    }
    mock_results.case_results = []
    
    mock_config = Mock()
    mock_config.output_dir = "./default_output"
    mock_config.golden_dataset_path = "data/default.json"
    mock_config.subset_size = None
    mock_config.verbose = False
    
    with patch.object(sys, 'argv', test_args), \
         patch('evaluate.load_config_from_yaml', return_value=mock_config), \
         patch('evaluate.Evaluator') as mock_evaluator_class:
        
        mock_evaluator = Mock()
        mock_evaluator.run_evaluation.return_value = mock_results
        mock_evaluator_class.return_value = mock_evaluator
        
        exit_code = evaluate.main()
        
        # Check that config was modified
        assert mock_config.golden_dataset_path == 'custom_data.json'
        assert mock_config.output_dir == './custom_output'
        assert mock_config.subset_size == 5
        assert mock_config.verbose is True


def test_main_generates_dashboard_by_default():
    """Test that dashboard is generated by default."""
    test_args = ['evaluate.py', '--config', 'config/test.yaml', '--no-reports']
    
    mock_results = Mock()
    mock_results.metrics = {"all_thresholds_met": True, "thresholds_met": {}}
    mock_results.case_results = []
    
    mock_config = Mock()
    mock_config.output_dir = "./test_output"
    mock_config.golden_dataset_path = "data/test.json"
    mock_config.subset_size = None
    mock_config.verbose = False
    
    with patch.object(sys, 'argv', test_args), \
         patch('evaluate.load_config_from_yaml', return_value=mock_config), \
         patch('evaluate.Evaluator') as mock_evaluator_class, \
         patch('evaluate.generate_dashboard_with_charts') as mock_dashboard:
        
        mock_evaluator = Mock()
        mock_evaluator.run_evaluation.return_value = mock_results
        mock_evaluator_class.return_value = mock_evaluator
        
        evaluate.main()
        
        assert mock_dashboard.called


def test_main_skips_dashboard_when_flag_set():
    """Test that dashboard is skipped with --no-dashboard flag."""
    test_args = ['evaluate.py', '--config', 'config/test.yaml', '--no-dashboard', '--no-reports']
    
    mock_results = Mock()
    mock_results.metrics = {"all_thresholds_met": True, "thresholds_met": {}}
    mock_results.case_results = []
    
    mock_config = Mock()
    mock_config.output_dir = "./test_output"
    mock_config.golden_dataset_path = "data/test.json"
    mock_config.subset_size = None
    mock_config.verbose = False
    
    with patch.object(sys, 'argv', test_args), \
         patch('evaluate.load_config_from_yaml', return_value=mock_config), \
         patch('evaluate.Evaluator') as mock_evaluator_class, \
         patch('evaluate.generate_dashboard_with_charts') as mock_dashboard:
        
        mock_evaluator = Mock()
        mock_evaluator.run_evaluation.return_value = mock_results
        mock_evaluator_class.return_value = mock_evaluator
        
        evaluate.main()
        
        assert not mock_dashboard.called


def test_main_generates_reports_by_default():
    """Test that reports are generated by default."""
    test_args = ['evaluate.py', '--config', 'config/test.yaml', '--no-dashboard']
    
    mock_results = Mock()
    mock_results.metrics = {"all_thresholds_met": True, "thresholds_met": {}}
    mock_results.case_results = []
    
    mock_config = Mock()
    mock_config.output_dir = "./test_output"
    mock_config.golden_dataset_path = "data/test.json"
    mock_config.subset_size = None
    mock_config.verbose = False
    
    with patch.object(sys, 'argv', test_args), \
         patch('evaluate.load_config_from_yaml', return_value=mock_config), \
         patch('evaluate.Evaluator') as mock_evaluator_class, \
         patch('evaluate.save_all_reports') as mock_reports:
        
        mock_evaluator = Mock()
        mock_evaluator.run_evaluation.return_value = mock_results
        mock_evaluator_class.return_value = mock_evaluator
        
        evaluate.main()
        
        assert mock_reports.called


def test_cli_help_message():
    """Test that help message can be displayed."""
    test_args = ['evaluate.py', '--help']
    
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit) as exc_info:
            evaluate.parse_arguments()
        
        # Help should exit with code 0
        assert exc_info.value.code == 0
