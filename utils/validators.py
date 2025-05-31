"""
Validators Module

This module contains validation classes for different document types
including emails, invoices, and webhooks.
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseValidator:
    """Base validator class with common validation methods."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def reset(self):
        """Reset error and warning lists."""
        self.errors = []
        self.warnings = []
    
    def add_error(self, message: str):
        """Add an error message."""
        self.errors.append(message)
        logger.error(f"Validation error: {message}")
    
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)
        logger.warning(f"Validation warning: {message}")
    
    def is_valid_email(self, email: str) -> bool:
        """Validate email address format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def is_valid_phone(self, phone: str) -> bool:
        """Validate phone number format."""
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        return len(digits_only) >= 10
    
    def is_valid_date(self, date_str: str) -> bool:
        """Validate date string format."""
        date_patterns = [
            '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y',
            '%Y/%m/%d', '%m-%d-%Y', '%d-%m-%Y'
        ]
        
        for pattern in date_patterns:
            try:
                datetime.strptime(date_str.strip(), pattern)
                return True
            except ValueError:
                continue
        return False

class EmailValidator(BaseValidator):
    """Validator for email documents."""
    
    def __init__(self):
        super().__init__()
        self.required_fields = ['from', 'to', 'subject']
        self.optional_fields = ['body', 'cc', 'bcc', 'date']
    
    def validate(self, content: str) -> Dict[str, Any]:
        """
        Validate email content and structure.
        
        Args:
            content (str): Email content to validate
            
        Returns:
            Dict[str, Any]: Validation result with errors and warnings
        """
        self.reset()
        
        if not content or not content.strip():
            self.add_error("Email content is empty")
            return self._build_result()
        
        # Parse email content
        email_data = self._parse_email_content(content)
        
        # Validate required fields
        self._validate_required_fields(email_data)
        
        # Validate email addresses
        self._validate_email_addresses(email_data)
        
        # Validate content structure
        self._validate_content_structure(email_data)
        
        # Additional checks
        self._check_spam_indicators(content)
        
        return self._build_result()
    
    def _parse_email_content(self, content: str) -> Dict[str, str]:
        """Parse email content into structured data."""
        lines = content.strip().split('\n')
        email_data = {}
        body_lines = []
        in_body = False
        
        for line in lines:
            line = line.strip()
            if not line and not in_body:
                continue
            
            if line.startswith('From:'):
                email_data['from'] = line.replace('From:', '').strip()
            elif line.startswith('To:'):
                email_data['to'] = line.replace('To:', '').strip()
            elif line.startswith('CC:') or line.startswith('Cc:'):
                email_data['cc'] = line.replace('CC:', '').replace('Cc:', '').strip()
            elif line.startswith('BCC:') or line.startswith('Bcc:'):
                email_data['bcc'] = line.replace('BCC:', '').replace('Bcc:', '').strip()
            elif line.startswith('Subject:'):
                email_data['subject'] = line.replace('Subject:', '').strip()
            elif line.startswith('Date:'):
                email_data['date'] = line.replace('Date:', '').strip()
            else:
                in_body = True
                if line:
                    body_lines.append(line)
        
        if body_lines:
            email_data['body'] = '\n'.join(body_lines)
        
        return email_data
    
    def _validate_required_fields(self, email_data: Dict[str, str]):
        """Validate that all required fields are present."""
        for field in self.required_fields:
            if field not in email_data or not email_data[field]:
                self.add_error(f"Missing required field: {field}")
    
    def _validate_email_addresses(self, email_data: Dict[str, str]):
        """Validate email address formats."""
        email_fields = ['from', 'to', 'cc', 'bcc']
        
        for field in email_fields:
            if field in email_data and email_data[field]:
                # Handle multiple email addresses separated by commas
                addresses = [addr.strip() for addr in email_data[field].split(',')]
                
                for addr in addresses:
                    if not self.is_valid_email(addr):
                        self.add_error(f"Invalid email address in {field}: {addr}")
    
    def _validate_content_structure(self, email_data: Dict[str, str]):
        """Validate email content structure."""
        # Check subject length
        if 'subject' in email_data:
            subject = email_data['subject']
            if len(subject) > 200:
                self.add_warning("Subject line is very long (>200 characters)")
            elif len(subject) < 5:
                self.add_warning("Subject line is very short (<5 characters)")
        
        # Check body content
        if 'body' in email_data:
            body = email_data['body']
            if len(body) > 10000:
                self.add_warning("Email body is very long (>10,000 characters)")
            elif len(body) < 10:
                self.add_warning("Email body is very short (<10 characters)")
    
    def _check_spam_indicators(self, content: str):
        """Check for common spam indicators."""
        spam_keywords = [
            'urgent', 'act now', 'limited time', 'click here',
            'free money', 'guaranteed', 'risk free', 'no obligation'
        ]
        
        content_lower = content.lower()
        found_spam_words = [word for word in spam_keywords if word in content_lower]
        
        if found_spam_words:
            self.add_warning(f"Potential spam indicators found: {', '.join(found_spam_words)}")
    
    def _build_result(self) -> Dict[str, Any]:
        """Build validation result."""
        return {
            'is_valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'score': self._calculate_quality_score()
        }
    
    def _calculate_quality_score(self) -> float:
        """Calculate email quality score (0-1)."""
        score = 1.0
        score -= len(self.errors) * 0.2  # Errors heavily penalized
        score -= len(self.warnings) * 0.1  # Warnings lightly penalized
        return max(0.0, score)

class InvoiceValidator(BaseValidator):
    """Validator for invoice documents."""
    
    def __init__(self):
        super().__init__()
        self.required_fields = ['invoice_number', 'date', 'total']
        self.optional_fields = ['vendor', 'po_number', 'due_date', 'items']
    
    def validate(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate invoice data structure and content.
        
        Args:
            invoice_data (Dict[str, Any]): Invoice data to validate
            
        Returns:
            Dict[str, Any]: Validation result with errors and warnings
        """
        self.reset()
        
        if not invoice_data:
            self.add_error("Invoice data is empty")
            return self._build_result()
        
        # Validate required fields
        self._validate_required_fields(invoice_data)
        
        # Validate data formats
        self._validate_data_formats(invoice_data)
        
        # Business logic validation
        self._validate_business_logic(invoice_data)
        
        return self._build_result()
    
    def _validate_required_fields(self, invoice_data: Dict[str, Any]):
        """Validate that all required fields are present."""
        for field in self.required_fields:
            if field not in invoice_data or not invoice_data[field]:
                self.add_error(f"Missing required field: {field}")
    
    def _validate_data_formats(self, invoice_data: Dict[str, Any]):
        """Validate data format consistency."""
        # Validate invoice number format
        if 'invoice_number' in invoice_data:
            inv_num = str(invoice_data['invoice_number'])
            if not re.match(r'^[A-Z0-9-]+$', inv_num):
                self.add_warning("Invoice number contains unusual characters")
        
        # Validate date format
        if 'date' in invoice_data and invoice_data['date']:
            if not self.is_valid_date(str(invoice_data['date'])):
                self.add_error("Invalid date format")
        
        # Validate due date if present
        if 'due_date' in invoice_data and invoice_data['due_date']:
            if not self.is_valid_date(str(invoice_data['due_date'])):
                self.add_error("Invalid due date format")
        
        # Validate total amount
        if 'total' in invoice_data:
            total = str(invoice_data['total']).replace('$', '').replace(',', '')
            try:
                float(total)
            except ValueError:
                self.add_error("Invalid total amount format")
    
    def _validate_business_logic(self, invoice_data: Dict[str, Any]):
        """Validate business logic rules."""
        # Check if due date is after invoice date
        if 'date' in invoice_data and 'due_date' in invoice_data:
            try:
                invoice_date = self._parse_date(str(invoice_data['date']))
                due_date = self._parse_date(str(invoice_data['due_date']))
                
                if due_date and invoice_date and due_date < invoice_date:
                    self.add_error("Due date cannot be before invoice date")
            except:
                pass  # Date parsing issues already caught above
        
        # Check for reasonable total amount
        if 'total' in invoice_data:
            try:
                total = float(str(invoice_data['total']).replace('$', '').replace(',', ''))
                if total < 0:
                    self.add_error("Total amount cannot be negative")
                elif total > 1000000:  # $1M threshold
                    self.add_warning("Total amount is very large (>$1,000,000)")
                elif total == 0:
                    self.add_warning("Total amount is zero")
            except:
                pass  # Format issues already caught above
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object."""
        date_patterns = [
            '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y',
            '%Y/%m/%d', '%m-%d-%Y', '%d-%m-%Y'
        ]
        
        for pattern in date_patterns:
            try:
                return datetime.strptime(date_str.strip(), pattern)
            except ValueError:
                continue
        return None
    
    def _build_result(self) -> Dict[str, Any]:
        """Build validation result."""
        return {
            'is_valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'score': self._calculate_quality_score()
        }
    
    def _calculate_quality_score(self) -> float:
        """Calculate invoice quality score (0-1)."""
        score = 1.0
        score -= len(self.errors) * 0.25  # Errors heavily penalized
        score -= len(self.warnings) * 0.1  # Warnings lightly penalized
        return max(0.0, score)

class WebhookValidator(BaseValidator):
    """Validator for webhook payloads."""
    
    def __init__(self):
        super().__init__()
        self.required_fields = ['type', 'data']
        self.optional_fields = ['id', 'timestamp', 'source', 'version']
    
    def validate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate webhook payload structure and content.
        
        Args:
            payload (Dict[str, Any]): Webhook payload to validate
            
        Returns:
            Dict[str, Any]: Validation result with errors and warnings
        """
        self.reset()
        
        if not payload:
            self.add_error("Webhook payload is empty")
            return self._build_result()
        
        # Validate JSON structure
        self._validate_structure(payload)
        
        # Validate required fields
        self._validate_required_fields(payload)
        
        # Validate field formats
        self._validate_field_formats(payload)
        
        # Validate payload size
        self._validate_payload_size(payload)
        
        return self._build_result()
    
    def _validate_structure(self, payload: Dict[str, Any]):
        """Validate basic JSON structure."""
        if not isinstance(payload, dict):
            self.add_error("Webhook payload must be a JSON object")
            return
        
        # Check for nested data structure
        if 'data' in payload:
            if not isinstance(payload['data'], (dict, list)):
                self.add_error("Webhook data field must be an object or array")
    
    def _validate_required_fields(self, payload: Dict[str, Any]):
        """Validate that all required fields are present."""
        for field in self.required_fields:
            if field not in payload:
                self.add_error(f"Missing required field: {field}")
            elif payload[field] is None or payload[field] == "":
                self.add_error(f"Required field cannot be empty: {field}")
    
    def _validate_field_formats(self, payload: Dict[str, Any]):
        """Validate specific field formats."""
        # Validate timestamp format if present
        if 'timestamp' in payload and payload['timestamp']:
            timestamp = payload['timestamp']
            if not self._is_valid_timestamp(timestamp):
                self.add_error("Invalid timestamp format")
        
        # Validate event type
        if 'type' in payload:
            event_type = payload['type']
            if not isinstance(event_type, str) or len(event_type) < 1:
                self.add_error("Event type must be a non-empty string")
            elif not re.match(r'^[a-zA-Z0-9._-]+$', event_type):
                self.add_warning("Event type contains unusual characters")
        
        # Validate ID format if present
        if 'id' in payload and payload['id']:
            webhook_id = str(payload['id'])
            if len(webhook_id) < 3:
                self.add_warning("Webhook ID is very short")
        
        # Validate source if present
        if 'source' in payload and payload['source']:
            source = payload['source']
            if not isinstance(source, str):
                self.add_error("Source must be a string")
    
    def _validate_payload_size(self, payload: Dict[str, Any]):
        """Validate webhook payload size."""
        payload_str = json.dumps(payload)
        size_bytes = len(payload_str.encode('utf-8'))
        
        # Common webhook size limits
        if size_bytes > 1048576:  # 1MB
            self.add_error("Webhook payload exceeds 1MB limit")
        elif size_bytes > 65536:  # 64KB
            self.add_warning("Webhook payload is large (>64KB)")
        elif size_bytes < 10:
            self.add_warning("Webhook payload is very small (<10 bytes)")
    
    def _is_valid_timestamp(self, timestamp: Any) -> bool:
        """Validate timestamp format."""
        if isinstance(timestamp, (int, float)):
            # Unix timestamp
            try:
                datetime.fromtimestamp(timestamp)
                return True
            except (ValueError, OSError):
                return False
        
        elif isinstance(timestamp, str):
            # ISO format timestamps
            iso_patterns = [
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%dT%H:%M:%S.%fZ',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S%z'
            ]
            
            for pattern in iso_patterns:
                try:
                    datetime.strptime(timestamp, pattern)
                    return True
                except ValueError:
                    continue
        
        return False
    
    def _build_result(self) -> Dict[str, Any]:
        """Build validation result."""
        return {
            'is_valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'score': self._calculate_quality_score()
        }
    
    def _calculate_quality_score(self) -> float:
        """Calculate webhook quality score (0-1)."""
        score = 1.0
        score -= len(self.errors) * 0.3  # Errors heavily penalized
        score -= len(self.warnings) * 0.05  # Warnings lightly penalized
        return max(0.0, score)