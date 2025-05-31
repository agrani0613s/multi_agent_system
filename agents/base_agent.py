from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from models.schemas import ClassificationResult
from memory.shared_memory import memory_store
import uuid
from datetime import datetime

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.agent_id = str(uuid.uuid4())
        
    @abstractmethod
    async def process(self, input_data: Any, classification: ClassificationResult, entry_id: str) -> Dict[str, Any]:
        """Process input data and return structured output"""
        pass
    
    def log_decision(self, entry_id: str, decision: str) -> None:
        """Log agent decision to memory"""
        memory_store.add_agent_output(entry_id, self.name, {
            "decision": decision,
            "timestamp": datetime.now().isoformat(),
            "agent_id": self.agent_id
        })
    
    def extract_keywords(self, text: str, keywords: list) -> list:
        """Extract keywords from text"""
        found_keywords = []
        text_lower = text.lower()
        for keyword in keywords:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)
        return found_keywords
    
    def calculate_confidence(self, matches: int, total_possible: int) -> float:
        """Calculate confidence score"""
        if total_possible == 0:
            return 0.0
        return min(matches / total_possible, 1.0)