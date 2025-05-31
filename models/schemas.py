from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, List, Any, Literal
from datetime import datetime
from enum import Enum

class FormatType(str, Enum):
    EMAIL = "email"
    JSON = "json"
    PDF = "pdf"

class BusinessIntent(str, Enum):
    RFQ = "rfq"
    COMPLAINT = "complaint"
    INVOICE = "invoice"
    REGULATION = "regulation"
    FRAUD_RISK = "fraud_risk"
    UNKNOWN = "unknown"

class Urgency(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Tone(str, Enum):
    POLITE = "polite"
    NEUTRAL = "neutral"
    ESCALATION = "escalation"
    THREATENING = "threatening"
    ANGRY = "angry"

class ClassificationResult(BaseModel):
    format_type: FormatType
    business_intent: BusinessIntent
    confidence_score: float = Field(ge=0, le=1)
    metadata: Dict[str, Any] = {}

class EmailData(BaseModel):
    sender: EmailStr
    subject: str
    body: str
    urgency: Urgency
    tone: Tone
    timestamp: datetime
    extracted_fields: Dict[str, Any] = {}

class JSONData(BaseModel):
    webhook_type: str
    payload: Dict[str, Any]
    schema_valid: bool
    anomalies: List[str] = []
    extracted_fields: Dict[str, Any] = {}

class PDFData(BaseModel):
    document_type: str
    extracted_text: str
    line_items: List[Dict[str, Any]] = []
    total_amount: Optional[float] = None
    flags: List[str] = []
    extracted_fields: Dict[str, Any] = {}

class ProcessingResult(BaseModel):
    input_id: str
    classification: ClassificationResult
    agent_output: Dict[str, Any]
    actions_triggered: List[str] = []
    timestamp: datetime
    status: Literal["success", "error", "pending"]
    error_message: Optional[str] = None

class ActionRequest(BaseModel):
    action_type: str
    payload: Dict[str, Any]
    source_agent: str
    input_id: str
    priority: Urgency = Urgency.MEDIUM

class MemoryEntry(BaseModel):
    id: str
    input_metadata: Dict[str, Any]
    classification: ClassificationResult
    agent_outputs: Dict[str, Any] = {}
    actions_triggered: List[str] = []
    decision_trace: List[str] = []
    timestamp: datetime
    status: str = "processing"