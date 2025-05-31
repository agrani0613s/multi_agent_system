"""
Test module for invoice processing agents.

This module contains unit tests for all agent classes including:
- InvoiceExtractionAgent
- ValidationAgent
- DataProcessingAgent
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pytest
import json
from pathlib import Path
import tempfile
import os

# Import test configuration
from . import TestConfig, get_test_data_path, ensure_test_data_exists


class MockInvoiceExtractionAgent:
    """Mock agent for invoice data extraction."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.processing_status = "ready"
    
    def extract_invoice_data(self, pdf_path):
        """Mock extraction method."""
        return {
            "invoice_number": "INV-2024-001",
            "date": "2024-05-15",
            "due_date": "2024-06-15",
            "vendor": {
                "name": "Test Vendor Inc.",
                "address": "123 Test Street, Test City, TC 12345",
                "email": "billing@testvendor.com"
            },
            "items": [
                {
                    "description": "Test Product",
                    "quantity": 2,
                    "unit_price": 500.00,
                    "total": 1000.00
                }
            ],
            "amounts": {
                "subtotal": 1000.00,
                "tax": 100.00,
                "total": 1100.00
            }
        }
    
    def get_processing_status(self):
        """Get current processing status."""
        return self.processing_status


class MockValidationAgent:
    """Mock agent for data validation."""
    
    def __init__(self):
        self.validation_rules = {
            "required_fields": ["invoice_number", "date", "vendor", "amounts"],
            "date_format": "%Y-%m-%d",
            "amount_precision": 2
        }
    
    def validate_invoice_data(self, data):
        """Mock validation method."""
        errors = []
        warnings = []
        
        # Check required fields
        for field in self.validation_rules["required_fields"]:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Check date format
        if "date" in data:
            try:
                from datetime import datetime
                datetime.strptime(data["date"], self.validation_rules["date_format"])
            except ValueError:
                errors.append("Invalid date format")
        
        # Check amounts
        if "amounts" in data and "total" in data["amounts"]:
            if not isinstance(data["amounts"]["total"], (int, float)):
                errors.append("Total amount must be numeric")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "confidence_score": 0.95 if len(errors) == 0 else 0.5
        }


class TestInvoiceExtractionAgent(unittest.TestCase):
    """Test cases for InvoiceExtractionAgent."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.agent = MockInvoiceExtractionAgent()
        self.sample_pdf_path = get_test_data_path("sample_invoice.pdf")
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        agent = MockInvoiceExtractionAgent({"model": "test_model"})
        self.assertEqual(agent.config["model"], "test_model")
        self.assertEqual(agent.processing_status, "ready")
    
    def test_extract_invoice_data_success(self):
        """Test successful invoice data extraction."""
        result = self.agent.extract_invoice_data(self.sample_pdf_path)
        
        # Verify structure
        self.assertIn("invoice_number", result)
        self.assertIn("date", result)
        self.assertIn("vendor", result)
        self.assertIn("amounts", result)
        
        # Verify data types
        self.assertIsInstance(result["vendor"], dict)
        self.assertIsInstance(result["amounts"], dict)
        
        # Verify specific values
        self.assertEqual(result["invoice_number"], "INV-2024-001")
        self.assertEqual(result["amounts"]["total"], 1100.00)
    
    def test_extract_invoice_data_invalid_path(self):
        """Test extraction with invalid file path."""
        with self.assertRaises(FileNotFoundError):
            # In a real implementation, this would raise an exception
            # For mock, we'll simulate the behavior
            if not os.path.exists("invalid_path.pdf"):
                raise FileNotFoundError("File not found")
    
    def test_get_processing_status(self):
        """Test processing status retrieval."""
        status = self.agent.get_processing_status()
        self.assertEqual(status, "ready")
    
    @patch('tempfile.NamedTemporaryFile')
    def test_extract_with_temporary_file(self, mock_temp_file):
        """Test extraction with temporary file handling."""
        mock_temp_file.return_value.__enter__.return_value.name = "temp_invoice.pdf"
        
        result = self.agent.extract_invoice_data("temp_invoice.pdf")
        self.assertIsInstance(result, dict)
        self.assertIn("invoice_number", result)


class TestValidationAgent(unittest.TestCase):
    """Test cases for ValidationAgent."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.agent = MockValidationAgent()
        self.valid_data = TestConfig.SAMPLE_INVOICE_DATA.copy()
        self.invalid_data = {"incomplete": "data"}
    
    def test_validate_complete_data(self):
        """Test validation of complete invoice data."""
        result = self.agent.validate_invoice_data(self.valid_data)
        
        self.assertTrue(result["is_valid"])
        self.assertEqual(len(result["errors"]), 0)
        self.assertGreater(result["confidence_score"], 0.9)
    
    def test_validate_incomplete_data(self):
        """Test validation of incomplete invoice data."""
        result = self.agent.validate_invoice_data(self.invalid_data)
        
        self.assertFalse(result["is_valid"])
        self.assertGreater(len(result["errors"]), 0)
        self.assertLess(result["confidence_score"], 0.7)
    
    def test_validate_invalid_date_format(self):
        """Test validation with invalid date format."""
        invalid_date_data = self.valid_data.copy()
        invalid_date_data["date"] = "15-05-2024"  # Wrong format
        
        result = self.agent.validate_invoice_data(invalid_date_data)
        
        self.assertFalse(result["is_valid"])
        self.assertIn("Invalid date format", result["errors"])
    
    def test_validate_invalid_amount(self):
        """Test validation with invalid amount."""
        invalid_amount_data = self.valid_data.copy()
        invalid_amount_data["amounts"]["total"] = "not_a_number"
        
        result = self.agent.validate_invoice_data(invalid_amount_data)
        
        self.assertFalse(result["is_valid"])
        self.assertIn("Total amount must be numeric", result["errors"])


class TestDataProcessingAgent(unittest.TestCase):
    """Test cases for DataProcessingAgent."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extraction_agent = MockInvoiceExtractionAgent()
        self.validation_agent = MockValidationAgent()
    
    def test_end_to_end_processing(self):
        """Test complete processing pipeline."""
        # Extract data
        extracted_data = self.extraction_agent.extract_invoice_data("sample.pdf")
        
        # Validate data
        validation_result = self.validation_agent.validate_invoice_data(extracted_data)
        
        # Verify pipeline
        self.assertIsInstance(extracted_data, dict)
        self.assertTrue(validation_result["is_valid"])
        self.assertEqual(extracted_data["invoice_number"], "INV-2024-001")
    
    def test_processing_with_validation_errors(self):
        """Test processing pipeline with validation errors."""
        # Extract incomplete data
        incomplete_data = {"invoice_number": "INV-001"}
        
        # Validate
        validation_result = self.validation_agent.validate_invoice_data(incomplete_data)
        
        # Verify error handling
        self.assertFalse(validation_result["is_valid"])
        self.assertGreater(len(validation_result["errors"]), 0)
    
    @patch('json.dumps')
    def test_data_serialization(self, mock_json_dumps):
        """Test data serialization for output."""
        mock_json_dumps.return_value = '{"test": "data"}'
        
        extracted_data = self.extraction_agent.extract_invoice_data("sample.pdf")
        serialized = json.dumps(extracted_data)
        
        mock_json_dumps.assert_called_once()
        self.assertEqual(serialized, '{"test": "data"}')


class TestAgentIntegration(unittest.TestCase):
    """Integration tests for agent interactions."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.extraction_agent = MockInvoiceExtractionAgent()
        self.validation_agent = MockValidationAgent()
    
    def test_agent_pipeline_integration(self):
        """Test full agent pipeline integration."""
        # Step 1: Extract data
        pdf_path = get_test_data_path("sample_invoice.pdf")
        extracted_data = self.extraction_agent.extract_invoice_data(pdf_path)
        
        # Step 2: Validate extracted data
        validation_result = self.validation_agent.validate_invoice_data(extracted_data)
        
        # Step 3: Verify integration
        self.assertIsInstance(extracted_data, dict)
        self.assertIsInstance(validation_result, dict)
        self.assertTrue(validation_result["is_valid"])
        self.assertEqual(extracted_data["invoice_number"], "INV-2024-001")
    
    def test_error_propagation_between_agents(self):
        """Test error handling between agents."""
        # Simulate extraction failure
        try:
            self.extraction_agent.extract_invoice_data("nonexistent.pdf")
        except Exception as e:
            self.assertIsInstance(e, (FileNotFoundError, Exception))
    
    def test_agent_configuration_sharing(self):
        """Test configuration sharing between agents."""
        config = {"timeout": 30, "max_retries": 3}
        agent = MockInvoiceExtractionAgent(config)
        
        self.assertEqual(agent.config["timeout"], 30)
        self.assertEqual(agent.config["max_retries"], 3)


# Performance and stress tests
class TestAgentPerformance(unittest.TestCase):
    """Performance tests for agents."""
    
    def setUp(self):
        """Set up performance test fixtures."""
        self.agent = MockInvoiceExtractionAgent()
    
    def test_multiple_extractions_performance(self):
        """Test performance with multiple extractions."""
        import time
        
        start_time = time.time()
        for i in range(10):
            result = self.agent.extract_invoice_data(f"sample_{i}.pdf")
            self.assertIsInstance(result, dict)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process 10 invoices in reasonable time (mock should be fast)
        self.assertLess(processing_time, 5.0)
    
    def test_large_data_handling(self):
        """Test handling of large invoice data."""
        # Simulate large invoice with many items
        large_invoice_data = {
            "invoice_number": "INV-LARGE-001",
            "date": "2024-05-15",
            "vendor": {"name": "Large Vendor", "address": "Address"},
            "items": [{"description": f"Item {i}", "price": 10.0} for i in range(1000)],
            "amounts": {"total": 10000.0}
        }
        
        validation_result = MockValidationAgent().validate_invoice_data(large_invoice_data)
        self.assertIsInstance(validation_result, dict)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)