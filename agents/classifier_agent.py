import re
from typing import Dict, Any
from agents.base_agent import BaseAgent
from models.schemas import ClassificationResult, FormatType, BusinessIntent

class ClassifierAgent(BaseAgent):
    def __init__(self):
        super().__init__("ClassifierAgent")
        
        # Few-shot examples for classification
        self.format_patterns = {
            FormatType.EMAIL: [
                r'subject:', r'from:', r'to:', r'@\w+\.\w+',
                r'dear', r'regards', r'sincerely'
            ],
            FormatType.JSON: [
                r'^\s*\{', r':\s*["\[\{]', r'":\s*\d+',
                r'webhook', r'payload', r'data'
            ],
            FormatType.PDF: [
                r'%PDF', r'invoice', r'total:', r'amount:',
                r'policy', r'regulation', r'compliance'
            ]
        }
        
        self.intent_keywords = {
            BusinessIntent.RFQ: [
                'request for quote', 'rfq', 'quotation', 'bid',
                'proposal', 'pricing', 'estimate'
            ],
            BusinessIntent.COMPLAINT: [
                'complaint', 'dissatisfied', 'problem', 'issue',
                'unhappy', 'angry', 'disappointed', 'terrible'
            ],
            BusinessIntent.INVOICE: [
                'invoice', 'bill', 'payment', 'amount due',
                'total:', 'line item', 'tax', 'subtotal'
            ],
            BusinessIntent.REGULATION: [
                'gdpr', 'compliance', 'regulation', 'policy',
                'fda', 'sox', 'hipaa', 'regulatory'
            ],
            BusinessIntent.FRAUD_RISK: [
                'suspicious', 'fraud', 'anomaly', 'unusual',
                'security', 'breach', 'unauthorized', 'alert'
            ]
        }
    
    async def process(self, input_data: str, classification: ClassificationResult = None, entry_id: str = None) -> ClassificationResult:
        """Classify input format and business intent"""
        
        # Detect format
        format_type = self._detect_format(input_data)
        
        # Detect business intent
        business_intent = self._detect_intent(input_data)
        
        # Calculate confidence
        confidence = self._calculate_confidence(input_data, format_type, business_intent)
        
        # Extract metadata
        metadata = self._extract_metadata(input_data, format_type)
        
        result = ClassificationResult(
            format_type=format_type,
            business_intent=business_intent,
            confidence_score=confidence,
            metadata=metadata
        )
        
        if entry_id:
            self.log_decision(entry_id, f"Classified as {format_type.value} with intent {business_intent.value}")
        
        return result
    
    def _detect_format(self, input_data: str) -> FormatType:
        """Detect input format using pattern matching"""
        format_scores = {}
        
        for format_type, patterns in self.format_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, input_data, re.IGNORECASE))
                score += matches
            format_scores[format_type] = score
        
        # Return format with highest score
        if format_scores:
            best_format = max(format_scores, key=format_scores.get)
            if format_scores[best_format] > 0:
                return best_format
        
        # Default fallback
        if input_data.strip().startswith('{'):
            return FormatType.JSON
        elif '@' in input_data and ('subject:' in input_data.lower() or 'from:' in input_data.lower()):
            return FormatType.EMAIL
        else:
            return FormatType.PDF
    
    def _detect_intent(self, input_data: str) -> BusinessIntent:
        """Detect business intent using keyword matching"""
        intent_scores = {}
        
        for intent, keywords in self.intent_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in input_data.lower():
                    score += 1
            intent_scores[intent] = score
        
        # Return intent with highest score
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            if intent_scores[best_intent] > 0:
                return best_intent
        
        return BusinessIntent.UNKNOWN
    
    def _calculate_confidence(self, input_data: str, format_type: FormatType, business_intent: BusinessIntent) -> float:
        """Calculate confidence score based on pattern matches"""
        format_matches = 0
        for pattern in self.format_patterns.get(format_type, []):
            if re.search(pattern, input_data, re.IGNORECASE):
                format_matches += 1
        
        intent_matches = 0
        for keyword in self.intent_keywords.get(business_intent, []):
            if keyword.lower() in input_data.lower():
                intent_matches += 1
        
        total_format_patterns = len(self.format_patterns.get(format_type, []))
        total_intent_keywords = len(self.intent_keywords.get(business_intent, []))
        
        format_confidence = format_matches / max(total_format_patterns, 1)
        intent_confidence = intent_matches / max(total_intent_keywords, 1)
        
        return (format_confidence + intent_confidence) / 2
    
    def _extract_metadata(self, input_data: str, format_type: FormatType) -> Dict[str, Any]:
        """Extract format-specific metadata"""
        metadata = {
            "length": len(input_data),
            "word_count": len(input_data.split()),
            "format_type": format_type.value
        }
        
        if format_type == FormatType.EMAIL:
            # Extract email-specific metadata
            if re.search(r'urgent|asap|immediate', input_data, re.IGNORECASE):
                metadata["urgency_indicators"] = True
            
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', input_data)
            if email_match:
                metadata["sender_domain"] = email_match.group().split('@')[1]
        
        elif format_type == FormatType.JSON:
            # Check for webhook indicators
            if 'webhook' in input_data.lower():
                metadata["webhook_detected"] = True
        
        elif format_type == FormatType.PDF:
            # Check for document type indicators
            if 'invoice' in input_data.lower():
                metadata["document_type"] = "invoice"
            elif any(term in input_data.lower() for term in ['policy', 'regulation', 'compliance']):
                metadata["document_type"] = "regulation"
        
        return metadata