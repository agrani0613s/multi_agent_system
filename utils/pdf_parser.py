"""
PDF Parser Utility

This module provides functionality to extract text and metadata from PDF documents.
"""

import io
import logging
from typing import Dict, Any, Optional
from PyPDF2 import PdfReader
import re

logger = logging.getLogger(__name__)

class PDFParser:
    """A utility class for parsing PDF documents and extracting text content."""
    
    def __init__(self):
        self.supported_formats = ['.pdf']
    
    def extract_text(self, pdf_content: bytes) -> str:
        """
        Extract text content from PDF bytes.
        
        Args:
            pdf_content (bytes): Raw PDF file content
            
        Returns:
            str: Extracted text content
            
        Raises:
            Exception: If PDF parsing fails
        """
        try:
            # Create a PDF reader from bytes
            pdf_stream = io.BytesIO(pdf_content)
            pdf_reader = PdfReader(pdf_stream)
            
            # Extract text from all pages
            text_content = ""
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += f"\n--- Page {page_num + 1} ---\n"
                        text_content += page_text
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {str(e)}")
                    continue
            
            if not text_content.strip():
                raise Exception("No text content found in PDF")
            
            return self._clean_text(text_content)
            
        except Exception as e:
            logger.error(f"PDF parsing failed: {str(e)}")
            raise Exception(f"Failed to parse PDF: {str(e)}")
    
    def extract_metadata(self, pdf_content: bytes) -> Dict[str, Any]:
        """
        Extract metadata from PDF document.
        
        Args:
            pdf_content (bytes): Raw PDF file content
            
        Returns:
            Dict[str, Any]: PDF metadata including title, author, creation date, etc.
        """
        try:
            pdf_stream = io.BytesIO(pdf_content)
            pdf_reader = PdfReader(pdf_stream)
            
            metadata = {}
            
            # Basic document info
            metadata['num_pages'] = len(pdf_reader.pages)
            metadata['is_encrypted'] = pdf_reader.is_encrypted
            
            # Document metadata
            if pdf_reader.metadata:
                doc_info = pdf_reader.metadata
                metadata.update({
                    'title': getattr(doc_info, 'title', None),
                    'author': getattr(doc_info, 'author', None),
                    'subject': getattr(doc_info, 'subject', None),
                    'creator': getattr(doc_info, 'creator', None),
                    'producer': getattr(doc_info, 'producer', None),
                    'creation_date': str(getattr(doc_info, 'creation_date', None)),
                    'modification_date': str(getattr(doc_info, 'modification_date', None))
                })
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to extract PDF metadata: {str(e)}")
            return {}
    
    def extract_structured_data(self, pdf_content: bytes) -> Dict[str, Any]:
        """
        Extract structured data from PDF (invoices, forms, etc.).
        
        Args:
            pdf_content (bytes): Raw PDF file content
            
        Returns:
            Dict[str, Any]: Structured data extracted from PDF
        """
        try:
            text_content = self.extract_text(pdf_content)
            metadata = self.extract_metadata(pdf_content)
            
            # Extract common structured elements
            structured_data = {
                'metadata': metadata,
                'text_content': text_content,
                'extracted_fields': {}
            }
            
            # Extract dates
            dates = self._extract_dates(text_content)
            if dates:
                structured_data['extracted_fields']['dates'] = dates
            
            # Extract amounts/currency
            amounts = self._extract_amounts(text_content)
            if amounts:
                structured_data['extracted_fields']['amounts'] = amounts
            
            # Extract email addresses
            emails = self._extract_emails(text_content)
            if emails:
                structured_data['extracted_fields']['emails'] = emails
            
            # Extract phone numbers
            phones = self._extract_phone_numbers(text_content)
            if phones:
                structured_data['extracted_fields']['phone_numbers'] = phones
            
            # Extract invoice-specific data
            invoice_data = self._extract_invoice_data(text_content)
            if invoice_data:
                structured_data['extracted_fields']['invoice_data'] = invoice_data
            
            return structured_data
            
        except Exception as e:
            logger.error(f"Failed to extract structured data: {str(e)}")
            return {'error': str(e)}
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page markers we added
        text = re.sub(r'\n--- Page \d+ ---\n', '\n', text)
        
        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        return text.strip()
    
    def _extract_dates(self, text: str) -> list:
        """Extract date patterns from text."""
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # MM/DD/YYYY or MM-DD-YYYY
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',    # YYYY/MM/DD or YYYY-MM-DD
            r'\b\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}\b',  # DD Month YYYY
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4}\b'  # Month DD, YYYY
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        return list(set(dates))  # Remove duplicates
    
    def _extract_amounts(self, text: str) -> list:
        """Extract monetary amounts from text."""
        amount_patterns = [
            r'\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # $1,000.00
            r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*USD',  # 1000.00 USD
            r'USD\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # USD 1000.00
        ]
        
        amounts = []
        for pattern in amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            amounts.extend(matches)
        
        return list(set(amounts))
    
    def _extract_emails(self, text: str) -> list:
        """Extract email addresses from text."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return list(set(emails))
    
    def _extract_phone_numbers(self, text: str) -> list:
        """Extract phone numbers from text."""
        phone_patterns = [
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # 123-456-7890
            r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}',      # (123) 456-7890
            r'\+\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'  # +1-123-456-7890
        ]
        
        phones = []
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            phones.extend(matches)
        
        return list(set(phones))
    
    def _extract_invoice_data(self, text: str) -> Dict[str, Any]:
        """Extract invoice-specific information."""
        invoice_data = {}
        
        # Invoice number
        invoice_patterns = [
            r'Invoice\s*#?\s*:?\s*([A-Z0-9-]+)',
            r'Invoice\s+Number\s*:?\s*([A-Z0-9-]+)',
            r'Inv\.\s*#?\s*:?\s*([A-Z0-9-]+)'
        ]
        
        for pattern in invoice_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_data['invoice_number'] = match.group(1)
                break
        
        # Purchase Order number
        po_patterns = [
            r'P\.?O\.?\s*#?\s*:?\s*([A-Z0-9-]+)',
            r'Purchase\s+Order\s*:?\s*([A-Z0-9-]+)'
        ]
        
        for pattern in po_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_data['po_number'] = match.group(1)
                break
        
        # Due date
        due_date_patterns = [
            r'Due\s+Date\s*:?\s*([^\\n]+)',
            r'Payment\s+Due\s*:?\s*([^\\n]+)'
        ]
        
        for pattern in due_date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_data['due_date'] = match.group(1).strip()
                break
        
        # Total amount
        total_patterns = [
            r'Total\s*:?\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'Amount\s+Due\s*:?\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'Grand\s+Total\s*:?\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        ]
        
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_data['total_amount'] = match.group(1)
                break
        
        return invoice_data