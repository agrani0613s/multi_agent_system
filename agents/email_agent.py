import re
from typing import Dict, Any
from datetime import datetime
from agents.base_agent import BaseAgent
from models.schemas import ClassificationResult, EmailData, Urgency, Tone

class EmailAgent(BaseAgent):
    def __init__(self):
        super().__init__("EmailAgent")
        
        self.urgency_keywords = {
            Urgency.CRITICAL: ['critical', 'emergency', 'urgent', 'asap', 'immediate'],
            Urgency.HIGH: ['important', 'priority', 'soon', 'quickly', 'expedite'],
            Urgency.MEDIUM: ['please', 'when possible', 'at your convenience'],
            Urgency.LOW: ['whenever', 'no rush', 'low priority']
        }
        
        self.tone_keywords = {
            Tone.THREATENING: ['lawsuit', 'legal action', 'consequences', 'unacceptable'],
            Tone.ANGRY: ['furious', 'outraged', 'disgusted', 'terrible', 'awful'],
            Tone.ESCALATION: ['manager', 'supervisor', 'escalate', 'complaint'],
            Tone.POLITE: ['please', 'thank you', 'appreciate', 'kindly'],
            Tone.NEUTRAL: []  # Default fallback
        }
    
    async def process(self, input_data: str, classification: ClassificationResult, entry_id: str) -> Dict[str, Any]:
        """Process email data and extract structured information"""
        
        # Extract email fields
        email_data = self._extract_email_fields(input_data)
        
        # Determine urgency and tone
        urgency = self._determine_urgency(input_data)
        tone = self._determine_tone(input_data)
        
        # Create structured result
        result = {
            "agent": self.name,
            "email_data": {
                "sender": email_data.get("sender", "unknown@example.com"),
                "subject": email_data.get("subject", "No Subject"),
                "body": email_data.get("body", input_data),
                "urgency": urgency.value,
                "tone": tone.value,
                "timestamp": datetime.now().isoformat(),
                "extracted_fields": email_data
            },
            "recommended_actions": self._recommend_actions(urgency, tone),
            "processing_metadata": {
                "confidence": classification.confidence_score,
                "keywords_found": self._extract_keywords_found(input_data)
            }
        }
        
        # Log decision
        self.log_decision(entry_id, f"Email processed - Urgency: {urgency.value}, Tone: {tone.value}")
        
        return result
    
    def _extract_email_fields(self, email_text: str) -> Dict[str, Any]:
        """Extract structured fields from email text"""
        fields = {}
        
        # Extract sender
        sender_match = re.search(r'from:\s*([\w\.-]+@[\w\.-]+\.\w+)', email_text, re.IGNORECASE)
        if sender_match:
            fields["sender"] = sender_match.group(1)
        
        # Extract subject
        subject_match = re.search(r'subject:\s*(.+?)(?:\n|$)', email_text, re.IGNORECASE)
        if subject_match:
            fields["subject"] = subject_match.group(1).strip()
        
        # Extract recipient
        to_match = re.search(r'to:\s*([\w\.-]+@[\w\.-]+\.\w+)', email_text, re.IGNORECASE)
        if to_match:
            fields["recipient"] = to_match.group(1)
        
        # Extract body (everything after headers)
        body_match = re.search(r'(?:subject:.*?\n\s*\n|^)(.*)', email_text, re.IGNORECASE | re.DOTALL)
        if body_match:
            fields["body"] = body_match.group(1).strip()
        else:
            fields["body"] = email_text
        
        # Extract specific requests or issues
        if 'request' in email_text.lower():
            request_match = re.search(r'request(?:ing)?\s+(.+?)(?:\.|$)', email_text, re.IGNORECASE)
            if request_match:
                fields["request"] = request_match.group(1).strip()
        
        if 'problem' in email_text.lower() or 'issue' in email_text.lower():
            issue_match = re.search(r'(?:problem|issue)\s+(?:is\s+)?(.+?)(?:\.|$)', email_text, re.IGNORECASE)
            if issue_match:
                fields["issue"] = issue_match.group(1).strip()
        
        return fields
    
    def _determine_urgency(self, email_text: str) -> Urgency:
        """Determine email urgency based on keywords and patterns"""
        text_lower = email_text.lower()
        
        # Check for urgency keywords
        for urgency, keywords in self.urgency_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return urgency
        
        # Check for punctuation patterns (multiple exclamation marks)
        if re.search(r'!{2,}', email_text):
            return Urgency.HIGH
        
        # Check for time constraints
        if re.search(r'by\s+(?:today|tomorrow|end of day|eod)', text_lower):
            return Urgency.HIGH
        
        return Urgency.MEDIUM  # Default
    
    def _determine_tone(self, email_text: str) -> Tone:
        """Determine email tone based on keywords and patterns"""
        text_lower = email_text.lower()
        
        # Check for tone keywords
        for tone, keywords in self.tone_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return tone
        
        # Check for caps (shouting)
        caps_words = len(re.findall(r'\b[A-Z]{3,}\b', email_text))
        total_words = len(email_text.split())
        if total_words > 0 and caps_words / total_words > 0.3:
            return Tone.ANGRY
        
        # Check for polite indicators
        if any(word in text_lower for word in ['please', 'thank', 'appreciate']):
            return Tone.POLITE
        
        return Tone.NEUTRAL
    
    def _recommend_actions(self, urgency: Urgency, tone: Tone) -> list:
        """Recommend actions based on urgency and tone"""
        actions = []
        
        if urgency == Urgency.CRITICAL or tone in [Tone.THREATENING, Tone.ANGRY]:
            actions.append("escalate_to_manager")
            actions.append("create_priority_ticket")
        elif urgency == Urgency.HIGH or tone == Tone.ESCALATION:
            actions.append("create_high_priority_ticket")
            actions.append("notify_team_lead")
        elif tone == Tone.POLITE and urgency in [Urgency.LOW, Urgency.MEDIUM]:
            actions.append("standard_response")
            actions.append("log_and_track")
        else:
            actions.append("standard_processing")
        
        return actions
    
    def _extract_keywords_found(self, email_text: str) -> Dict[str, list]:
        """Extract all keywords found for metadata"""
        found_keywords = {
            "urgency": [],
            "tone": []
        }
        
        text_lower = email_text.lower()
        
        for urgency, keywords in self.urgency_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found_keywords["urgency"].append(keyword)
        
        for tone, keywords in self.tone_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found_keywords["tone"].append(keyword)
        
        return found_keywords