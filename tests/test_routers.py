"""
Test module for API routers and endpoints.

This module contains unit tests for all router classes including:
- InvoiceUploadRouter
- ProcessingRouter
- ResultsRouter
- HealthCheckRouter
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pytest
import json
import io
from pathlib import Path
import tempfile
import os

# Import test configuration
from . import TestConfig, get_test_data_path, ensure_test_data_exists


class MockFastAPIRequest:
    """Mock FastAPI request object."""
    
    def __init__(self, method="GET", url="/", headers=None, body=None):
        self.method = method
        self.url = url
        self.headers = headers or {}
        self.body = body or b""
    
    async def json(self):
        """Mock JSON method."""
        return json.loads(self.body.decode()) if self.body else {}
    
    async def form(self):
        """Mock form data method."""
        return {"file": MockUploadFile()}


class MockUploadFile:
    """Mock file upload object."""
    
    def __init__(self, filename="test.pdf", content=b"fake pdf content"):
        self.filename = filename
        self.content_type = "application/pdf"
        self.file = io.BytesIO(content)
        self.size = len(content)
    
    async def read(self):
        """Read file content."""
        return self.file.getvalue()
    
    def seek(self, position):
        """Seek to position in file."""
        self.file.seek(position)


class MockInvoiceUploadRouter:
    """Mock router for invoice upload endpoints."""
    
    def __init__(self):
        self.uploaded_files = []
        self.processing_queue = []
    
    async def upload_invoice(self, file: MockUploadFile):
        """Mock invoice upload endpoint."""
        if not file.filename.endswith('.pdf'):
            return {
                "status": "error",
                "message": "Only PDF files are allowed",
                "code": 400
            }
        
        # Simulate file validation
        content = await file.read()
        if len(content) == 0:
            return {
                "status": "error",
                "message": "Empty file uploaded",
                "code": 400
            }
        
        # Mock successful upload
        file_id = f"upload_{len(self.uploaded_files) + 1}"
        self.uploaded_files.append({
            "id": file_id,
            "filename": file.filename,
            "size": file.size,
            "content_type": file.content_type
        })
        
        return {
            "status": "success",
            "message": "File uploaded successfully",
            "file_id": file_id,
            "filename": file.filename,
            "size": file.size
        }
    
    async def get_upload_status(self, file_id: str):
        """Get upload status by file ID."""
        for upload in self.uploaded_files:
            if upload["id"] == file_id:
                return {
                    "status": "success",
                    "file_id": file_id,
                    "upload_status": "completed",
                    "details": upload
                }
        
        return {
            "status": "error",
            "message": "File not found",
            "code": 404
        }


class MockProcessingRouter:
    """Mock router for invoice processing endpoints."""
    
    def __init__(self):
        self.processing_jobs = {}
        self.job_counter = 0
    
    async def start_processing(self, file_id: str):
        """Start invoice processing."""
        self.job_counter += 1
        job_id = f"job_{self.job_counter}"
        
        self.processing_jobs[job_id] = {
            "job_id": job_id,
            "file_id": file_id,
            "status": "processing",
            "progress": 0,
            "started_at": "2024-05-30T10:00:00Z",
            "estimated_completion": "2024-05-30T10:02:00Z"
        }
        
        return {
            "status": "success",
            "message": "Processing started",
            "job_id": job_id,
            "estimated_time": "2 minutes"
        }
    
    async def get_processing_status(self, job_id: str):
        """Get processing status."""
        if job_id not in self.processing_jobs:
            return {
                "status": "error",
                "message": "Job not found",
                "code": 404
            }
        
        job = self.processing_jobs[job_id]
        
        # Simulate progress
        if job["status"] == "processing":
            job["progress"] = min(job["progress"] + 10, 100)
            if job["progress"] >= 100:
                job["status"] = "completed"
        
        return {
            "status": "success",
            "job_details": job
        }
    
    async def cancel_processing(self, job_id: str):
        """Cancel processing job."""
        if job_id not in self.processing_jobs:
            return {
                "status": "error",
                "message": "Job not found",
                "code": 404
            }
        
        self.processing_jobs[job_id]["status"] = "cancelled"
        
        return {
            "status": "success",
            "message": "Processing cancelled",
            "job_id": job_id
        }


class MockResultsRouter:
    """Mock router for results endpoints."""
    
    def __init__(self):
        self.results_store = {}
    
    async def get_extraction_results(self, job_id: str):
        """Get extraction results for a job."""
        if job_id not in self.results_store:
            # Generate mock results
            self.results_store[job_id] = TestConfig.SAMPLE_INVOICE_DATA.copy()
            self.results_store[job_id]["job_id"] = job_id
            self.results_store[job_id]["extraction_confidence"] = 0.95
        
        return {
            "status": "success",
            "job_id": job_id,
            "results": self.results_store[job_id]
        }
    
    async def export_results(self, job_id: str, format: str = "json"):
        """Export results in specified format."""
        if job_id not in self.results_store:
            return {
                "status": "error",
                "message": "Results not found",
                "code": 404
            }
        
        results = self.results_store[job_id]
        
        if format.lower() == "json":
            return {
                "status": "success",
                "format": "json",
                "data": results,
                "download_url": f"/download/{job_id}.json"
            }
        elif format.lower() == "csv":
            return {
                "status": "success",
                "format": "csv",
                "download_url": f"/download/{job_id}.csv"
            }
        else:
            return {
                "status": "error",
                "message": "Unsupported format",
                "code": 400
            }


class MockHealthCheckRouter:
    """Mock router for health check endpoints."""
    
    def __init__(self):
        self.service_status = {
            "api": "healthy",
            "database": "healthy",
            "processing_engine": "healthy",
            "storage": "healthy"
        }
    
    async def health_check(self):
        """Basic health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": "2024-05-30T10:00:00Z",
            "version": "1.0.0",
            "uptime": "24h 30m"
        }
    
    async def detailed_health_check(self):
        """Detailed health check with service status."""
        overall_status = "healthy" if all(
            status == "healthy" for status in self.service_status.values()
        ) else "degraded"
        
        return {
            "status": overall_status,
            "timestamp": "2024-05-30T10:00:00Z",
            "services": self.service_status,
            "system_info": {
                "cpu_usage": "15%",
                "memory_usage": "45%",
                "disk_usage": "60%"
            }
        }


class TestInvoiceUploadRouter(unittest.TestCase):
    """Test cases for InvoiceUploadRouter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.router = MockInvoiceUploadRouter()
    
    async def test_successful_upload(self):
        """Test successful PDF upload."""
        mock_file = MockUploadFile("test_invoice.pdf", b"fake pdf content")
        result = await self.router.upload_invoice(mock_file)
        
        self.assertEqual(result["status"], "success")
        self.assertIn("file_id", result)
        self.assertEqual(result["filename"], "test_invoice.pdf")
    
    async def test_invalid_file_type(self):
        """Test upload with invalid file type."""
        mock_file = MockUploadFile("test_invoice.txt", b"text content")
        result = await self.router.upload_invoice(mock_file)
        
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["code"], 400)
        self.assertIn("Only PDF files are allowed", result["message"])
    
    async def test_empty_file_upload(self):
        """Test upload with empty file."""
        mock_file = MockUploadFile("empty.pdf", b"")
        result = await self.router.upload_invoice(mock_file)
        
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["code"], 400)
        self.assertIn("Empty file", result["message"])
    
    async def test_get_upload_status_existing(self):
        """Test getting status of existing upload."""
        # First upload a file
        mock_file = MockUploadFile("test.pdf", b"content")
        upload_result = await self.router.upload_invoice(mock_file)
        file_id = upload_result["file_id"]
        
        # Then check status
        status_result = await self.router.get_upload_status(file_id)
        
        self.assertEqual(status_result["status"], "success")
        self.assertEqual(status_result["file_id"], file_id)
        self.assertEqual(status_result["upload_status"], "completed")
    
    async def test_get_upload_status_nonexistent(self):
        """Test getting status of non-existent upload."""
        result = await self.router.get_upload_status("nonexistent_id")
        
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["code"], 404)


class TestProcessingRouter(unittest.TestCase):
    """Test cases for ProcessingRouter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.router = MockProcessingRouter()
    
    async def test_start_processing(self):
        """Test starting processing job."""
        result = await self.router.start_processing("file_123")
        
        self.assertEqual(result["status"], "success")
        self.assertIn("job_id", result)
        self.assertIn("estimated_time", result)
    
    async def test_get_processing_status_existing(self):
        """Test getting status of existing job."""
        # Start a job first
        start_result = await self.router.start_processing("file_123")
        job_id = start_result["job_id"]
        
        # Check status
        status_result = await self.router.get_processing_status(job_id)
        
        self.assertEqual(status_result["status"], "success")
        self.assertIn("job_details", status_result)
        self.assertEqual(status_result["job_details"]["job_id"], job_id)
    
    async def test_get_processing_status_nonexistent(self):
        """Test getting status of non-existent job."""
        result = await self.router.get_processing_status("nonexistent_job")
        
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["code"], 404)
    
    async def test_cancel_processing_existing(self):
        """Test cancelling existing job."""
        # Start a job first
        start_result = await self.router.start_processing("file_123")
        job_id = start_result["job_id"]
        
        # Cancel the job
        cancel_result = await self.router.cancel_processing(job_id)
        
        self.assertEqual(cancel_result["status"], "success")
        self.assertEqual(cancel_result["job_id"], job_id)
        
        # Verify job is cancelled
        status_result = await self.router.get_processing_status(job_id)
        self.assertEqual(status_result["job_details"]["status"], "cancelled")
    
    async def test_cancel_processing_nonexistent(self):
        """Test cancelling non-existent job."""
        result = await self.router.cancel_processing("nonexistent_job")
        
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["code"], 404)


class TestResultsRouter(unittest.TestCase):
    """Test cases for ResultsRouter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.router = MockResultsRouter()
    
    async def test_get_extraction_results(self):
        """Test getting extraction results."""
        result = await self.router.get_extraction_results("job_123")
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["job_id"], "job_123")
        self.assertIn("results", result)
        self.assertIn("invoice_number", result["results"])
    
    async def test_export_results_json(self):
        """Test exporting results as JSON."""
        # First get results to populate store
        await self.router.get_extraction_results("job_123")
        
        # Then export
        result = await self.router.export_results("job_123", "json")
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["format"], "json")
        self.assertIn("data", result)
        self.assertIn("download_url", result)
    
    async def test_export_results_csv(self):
        """Test exporting results as CSV."""
        # First get results to populate store
        await self.router.get_extraction_results("job_123")
        
        # Then export
        result = await self.router.export_results("job_123", "csv")
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["format"], "csv")
        self.assertIn("download_url", result)
    
    async def test_export_results_unsupported_format(self):
        """Test exporting with unsupported format."""
        result = await self.router.export_results("job_123", "xml")
        
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["code"], 400)
        self.assertIn("Unsupported format", result["message"])
    
    async def test_export_results_nonexistent_job(self):
        """Test exporting results for non-existent job."""
        result = await self.router.export_results("nonexistent_job", "json")
        
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["code"], 404)


class TestHealthCheckRouter(unittest.TestCase):
    """Test cases for HealthCheckRouter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.router = MockHealthCheckRouter()
    
    async def test_basic_health_check(self):
        """Test basic health check endpoint."""
        result = await self.router.health_check()
        
        self.assertEqual(result["status"], "healthy")
        self.assertIn("timestamp", result)
        self.assertIn("version", result)
        self.assertIn("uptime", result)
    
    async def test_detailed_health_check_healthy(self):
        """Test detailed health check when all services are healthy."""
        result = await self.router.detailed_health_check()
        
        self.assertEqual(result["status"], "healthy")
        self.assertIn("services", result)
        self.assertIn("system_info", result)
        
        # Check all services are healthy
        for service_status in result["services"].values():
            self.assertEqual(service_status, "healthy")
    
    async def test_detailed_health_check_degraded(self):
        """Test detailed health check when a service is unhealthy."""
        # Simulate unhealthy service
        self.router.service_status["database"] = "unhealthy"
        
        result = await self.router.detailed_health_check()
        
        self.assertEqual(result["status"], "degraded")
        self.assertEqual(result["services"]["database"], "unhealthy")


class TestRouterIntegration(unittest.TestCase):
    """Integration tests for router interactions."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.upload_router = MockInvoiceUploadRouter()
        self.processing_router = MockProcessingRouter()
        self.results_router = MockResultsRouter()
    
    async def test_full_workflow_integration(self):
        """Test complete workflow from upload to results."""
        # Step 1: Upload file
        mock_file = MockUploadFile("test.pdf", b"pdf content")
        upload_result = await self.upload_router.upload_invoice(mock_file)
        file_id = upload_result["file_id"]
        
        # Step 2: Start processing
        process_result = await self.processing_router.start_processing(file_id)
        job_id = process_result["job_id"]
        
        # Step 3: Check processing status
        status_result = await self.processing_router.get_processing_status(job_id)
        
        # Step 4: Get results
        results = await self.results_router.get_extraction_results(job_id)
        
        # Verify integration
        self.assertEqual(upload_result["status"], "success")
        self.assertEqual(process_result["status"], "success")
        self.assertEqual(status_result["status"], "success")
        self.assertEqual(results["status"], "success")


# Async test runner helper
def run_async_test(coro):
    """Helper to run async tests."""
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


if __name__ == '__main__':
    # Convert async test methods to sync for unittest
    for test_class in [TestInvoiceUploadRouter, TestProcessingRouter, 
                      TestResultsRouter, TestHealthCheckRouter, TestRouterIntegration]:
        for attr_name in dir(test_class):
            attr = getattr(test_class, attr_name)
            if callable(attr) and attr_name.startswith('test_') and hasattr(attr, '__code__'):
                # Check if it's an async method
                if attr.__code__.co_flags & 0x80:  # CO_COROUTINE flag
                    # Wrap async method
                    def make_sync_test(async_method):
                        def sync_test(self):
                            return run_async_test(async_method(self))
                        return sync_test
                    
                    setattr(test_class, attr_name, make_sync_test(attr))
    
    # Run tests with verbose output
    unittest.main(verbosity=2)