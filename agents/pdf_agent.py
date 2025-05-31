import re
from typing import Dict, Any, List
from datetime import datetime
from agents.base_agent import BaseAgent
from models.schemas import ClassificationResult, PDFData
from utils.pdf_parser import PDFParser

class PDFAgent(BaseAgent):
    def __init__(self):
        super().__init__("PDFAgent")
        self.pdf_parser = PDFParser()
        
        self.compliance_keywords = [
            "gdpr", "fda", "sox", "hipaa", "pci", "compliance",
            "regulation", "policy", "audit", "security"
        ]
        
        self.invoice_patterns = {
            "total": [r'total[:\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', r'amount due[:\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)'],
            "invoice_number": [r'invoice\s*#?\s*:?\s*(\w+)', r'inv\s*#?\s*:?\s*(\w+)'],
            "date": [r'date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'],
            "vendor": [r'from[:\s]+(.+?)(?:\n|$)', r'vendor[:\s]+(.+?)(?:\n|$)']
        }
    
    async def process(self, input_data: str, classification: ClassificationResult, entry_id: str) -> Dict[str, Any]:
        """Process PDF data and extract structured information"""
        
        # For this implementation, we'll treat input_data as extracted text
        # In production, this would use actual PDF parsing
        extracted_text = input_data
        
        # Determine document type
        document_type = self._determine_document_type(extracted_text)
        
        # Extract structured data based on type
        if document_type == "invoice":
            line_items, total_amount = self._extract_invoice_data(extracted_text)
        else:
            line_items, total_amount = [], None
        
        # Check for compliance flags
        flags = self._check_compliance_flags(extracted_text, document_type, total_amount)
        
        # Extract general fields
        extracted_fields = self._extract_general_fields(extracted_text, document_type)
        
        result = {
            "agent": self.name,
            "pdf_data": {
                "document_type": document_type,
                "extracted_text": extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text,
                "line_items": line_items,
                "total_amount": total_amount,
                "flags": flags,
                "extracted_fields": extracted_fields
            },
            "recommended_actions": self._recommend_actions(flags, total_amount, document_type),
            "processing_metadata": {
                "text_length": len(extracted_text),
                "line_count": len(extracted_text.split('\n')),
                "confidence": classification.confidence_score
            }
        }
        
        # Log decision
        self.log_decision(entry_id, f"PDF processed - Type: {document_type}, Flags: {len(flags)}, Total: {total_amount}")
        
        return result
    
    def _determine_document_type(self, text: str) -> str:
        """Determine the type of PDF document"""
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ["invoice", "bill", "payment", "amount due"]):
            return "invoice"
        elif any(keyword in text_lower for keyword in ["policy", "regulation", "compliance", "gdpr", "fda"]):
            return "policy"
        elif any(keyword in text_lower for keyword in ["contract", "agreement", "terms"]):
            return "contract"
        elif any(keyword in text_lower for keyword in ["report", "analysis", "summary"]):
            return "report"
        else:
            return "document"
    
    def _extract_invoice_data(self, text: str) -> tuple[List[Dict[str, Any]], float]:
        """Extract line items and total from invoice"""
        line_items = []
        total_amount = None
        
        # Extract total amount
        for pattern in self.invoice_patterns["total"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '')
                    total_amount = float(amount_str)
                    break
                except ValueError:
                    continue
        
        # Extract line items (simplified pattern)
        line_pattern = r'(\d+)\s+(.+?)\s+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)'
        matches = re.findall(line_pattern, text)
        
        for match in matches:
            try:
                line_items.append({
                    "quantity": int(match[0]),
                    "description": match[1].strip(),
                    "amount": float(match[2].replace(',', ''))
                })
            except ValueError:
                continue
        
        return line_items, total_amount
    
    def _check_compliance_flags(self, text: str, document_type: str, total_amount: float) -> List[str]:
        """Check for compliance and risk flags"""
        flags = []
        text_lower = text.lower()
        
        # Check for high-value invoice
        if document_type == "invoice" and total_amount and total_amount > 10000:
            flags.append("high_value_invoice")
        
        # Check for compliance keywords
        found_compliance = self.extract_keywords(text, self.compliance_keywords)
        if found_compliance:
            flags.append("compliance_document")
            for keyword in found_compliance:
                flags.append(f"contains_{keyword.lower()}")
        
        # Check for specific regulatory mentions
        if "gdpr" in text_lower:
            flags.append("gdpr_related")
        if "fda" in text_lower:
            flags.append("fda_related")
        if "sox" in text_lower:
            flags.append("sox_compliance")
        
        # Check for sensitive information patterns
        if re.search(r'\b\d{3}-\d{2}-\d{4}\b', text):  # SSN pattern
            flags.append("contains_ssn")
        if re.search(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', text):  # Credit card pattern
            flags.append("contains_credit_card")
        
        # Check for urgency indicators
        if re.search(r'urgent|asap|immediate|critical', text_lower):
            flags.append("urgent_document")
        
        return flags
    
    def _extract_general_fields(self, text: str, document_type: str) -> Dict[str, Any]:
        """Extract general fields from document"""
        fields = {}
        
        # Extract dates
        date_patterns = [
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
            r'\b(\d{4}-\d{2}-\d{2})\b'
        ]
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, text))
        if dates:
            fields["dates_found"] = dates[:5]  # Limit to first 5
        
        # Extract amounts/numbers
        amount_pattern = r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)'
        amounts = re.findall(amount_pattern, text)
        if amounts:
            fields["amounts_found"] = [float(amt.replace(',', '')) for amt in amounts[:10]]
        
        # Extract email addresses
        email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            fields["emails_found"] = emails
        
        # Extract phone numbers
        phone_pattern = r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'
        phones = re.findall(phone_pattern, text)
        if phones:
            fields["phones_found"] = phones
        
        # Document-specific extractions
        if document_type == "invoice":
            # Extract invoice number
            for pattern in self.invoice_patterns["invoice_number"]:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    fields["invoice_number"] = match.group(1)
                    break
            
            # Extract vendor
            for pattern in self.invoice_patterns["vendor"]:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    fields["vendor"] = match.group(1).strip()
                    break
        
        # Extract key-value pairs
        kv_pattern = r'(\w+):\s*([^\n]+)'
        key_values = re.findall(kv_pattern, text)
        if key_values:
            fields["key_value_pairs"] = dict(key_values[:10])  # Limit to first 10
        
        return fields
    
    def _recommend_actions(self, flags: List[str], total_amount: float, document_type: str) -> List[str]:
        """Recommend actions based on document analysis"""
        actions = []
        
        # High-value invoice actions
        if "high_value_invoice" in flags:
            actions.append("require_manager_approval")
            actions.append("flag_financial_review")
        
        # Compliance document actions
        if "compliance_document" in flags:
            actions.append("route_to_compliance_team")
            actions.append("log_regulatory_document")
        
        # GDPR specific actions
        if "gdpr_related" in flags:
            actions.append("notify_data_protection_officer")
            actions.append("ensure_gdpr_compliance")
        
        # FDA specific actions
        if "fda_related" in flags:
            actions.append("route_to_regulatory_affairs")
            actions.append("maintain_fda_audit_trail")
        
        # Sensitive information actions
        if any(flag in flags for flag in ["contains_ssn", "contains_credit_card"]):
            actions.append("encrypt_and_secure")
            actions.append("limit_access_permissions")
        
        # Urgent document actions
        if "urgent_document" in flags:
            actions.append("prioritize_processing")
            actions.append("notify_relevant_teams")
        
        # Default actions
        if not actions:
            actions.append("standard_document_processing")
            actions.append("archive_after_processing")
        
        return actions