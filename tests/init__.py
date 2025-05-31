"""
Test package for invoice processing system.

This package contains all test modules for the invoice processing application,
including tests for agents, routers, and other core components.
"""

__version__ = "1.0.0"
__author__ = "Invoice Processing Team"

# Test configuration constants
TEST_DATA_DIR = "sample_data"
SAMPLE_INVOICE_PATH = f"{TEST_DATA_DIR}/sample_invoice.pdf"

# Common test utilities
import os
import sys
from pathlib import Path

# Add the parent directory to the Python path for imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

def get_test_data_path(filename):
    """
    Get the full path to a test data file.
    
    Args:
        filename (str): Name of the test data file
        
    Returns:
        str: Full path to the test data file
    """
    return os.path.join(TEST_DATA_DIR, filename)

def ensure_test_data_exists():
    """
    Ensure that the test data directory and files exist.
    
    Returns:
        bool: True if test data exists, False otherwise
    """
    test_data_path = Path(TEST_DATA_DIR)
    return test_data_path.exists() and test_data_path.is_dir()

# Test fixtures and common setup
class TestConfig:
    """Common test configuration settings."""
    
    # API endpoints for testing
    BASE_URL = "http://localhost:8000"
    API_VERSION = "v1"
    
    # Test timeouts
    DEFAULT_TIMEOUT = 30
    UPLOAD_TIMEOUT = 60
    
    # Test data
    SAMPLE_INVOICE_DATA = {
        "invoice_number": "INV-2024-001",
        "date": "2024-05-15",
        "due_date": "2024-06-15",
        "vendor": {
            "name": "Test Vendor Inc.",
            "address": "123 Test Street, Test City, TC 12345",
            "email": "billing@testvendor.com"
        },
        "amounts": {
            "subtotal": 1000.00,
            "tax": 100.00,
            "total": 1100.00
        }
    }

# Import commonly used test utilities
try:
    import pytest
    import unittest
    from unittest.mock import Mock, patch, MagicMock
    
    # Make these available at package level
    __all__ = [
        'TestConfig',
        'get_test_data_path',
        'ensure_test_data_exists',
        'Mock',
        'patch',
        'MagicMock',
        'pytest',
        'unittest'
    ]
except ImportError as e:
    print(f"Warning: Some test dependencies not available: {e}")
    __all__ = [
        'TestConfig',
        'get_test_data_path',
        'ensure_test_data_exists'
    ]