from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
import logging
from datetime import datetime
import asyncio

from utils.pdf_parser import PDFParser
from utils.validators import EmailValidator, InvoiceValidator, WebhookValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Multi-Agent Document Processing System", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize parsers and validators
pdf_parser = PDFParser()
email_validator = EmailValidator()
invoice_validator = InvoiceValidator()
webhook_validator = WebhookValidator()

# Data models
class DocumentRequest(BaseModel):
    content: str
    document_type: str

class ProcessingResult(BaseModel):
    status: str
    agent_used: str
    processed_data: Dict[str, Any]
    timestamp: str
    confidence_score: Optional[float] = None

class EmailAgent:
    """Agent specialized in processing email content"""
    
    def __init__(self):
        self.name = "EmailAgent"
        self.capabilities = ["email_parsing", "sentiment_analysis", "entity_extraction"]
    
    async def process(self, content: str) -> Dict[str, Any]:
        logger.info(f"{self.name} processing email content")
        
        # Validate email format
        validation_result = email_validator.validate(content)
        if not validation_result["is_valid"]:
            raise ValueError(f"Invalid email format: {validation_result['errors']}")
        
        # Extract email components
        email_data = self._extract_email_data(content)
        
        # Perform sentiment analysis
        sentiment = self._analyze_sentiment(email_data.get('body', ''))
        
        # Extract entities
        entities = self._extract_entities(email_data.get('body', ''))
        
        return {
            "email_data": email_data,
            "sentiment": sentiment,
            "entities": entities,
            "processing_time": datetime.now().isoformat(),
            "confidence": 0.85
        }
    
    def _extract_email_data(self, content: str) -> Dict[str, str]:
        lines = content.strip().split('\n')
        email_data = {}
        
        for line in lines:
            if line.startswith('From:'):
                email_data['from'] = line.replace('From:', '').strip()
            elif line.startswith('To:'):
                email_data['to'] = line.replace('To:', '').strip()
            elif line.startswith('Subject:'):
                email_data['subject'] = line.replace('Subject:', '').strip()
            elif not line.startswith(('From:', 'To:', 'Subject:')) and line.strip():
                email_data['body'] = email_data.get('body', '') + line + '\n'
        
        return email_data
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        # Simple sentiment analysis (in production, use proper NLP libraries)
        positive_words = ['good', 'great', 'excellent', 'happy', 'pleased', 'thanks', 'appreciate']
        negative_words = ['bad', 'terrible', 'awful', 'angry', 'frustrated', 'disappointed']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return {
            "sentiment": sentiment,
            "positive_score": positive_count,
            "negative_score": negative_count
        }
    
    def _extract_entities(self, text: str) -> Dict[str, list]:
        # Simple entity extraction (in production, use NER models)
        import re
        
        # Extract email addresses
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        
        # Extract phone numbers
        phones = re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text)
        
        # Extract dates
        dates = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', text)
        
        return {
            "emails": emails,
            "phones": phones,
            "dates": dates
        }

class InvoiceAgent:
    """Agent specialized in processing invoice documents"""
    
    def __init__(self):
        self.name = "InvoiceAgent"
        self.capabilities = ["invoice_parsing", "amount_extraction", "vendor_identification"]
    
    async def process(self, content: str) -> Dict[str, Any]:
        logger.info(f"{self.name} processing invoice content")
        
        # Parse invoice data
        invoice_data = self._parse_invoice_data(content)
        
        # Validate invoice
        validation_result = invoice_validator.validate(invoice_data)
        if not validation_result["is_valid"]:
            logger.warning(f"Invoice validation issues: {validation_result['warnings']}")
        
        # Extract financial information
        financial_info = self._extract_financial_info(content)
        
        return {
            "invoice_data": invoice_data,
            "financial_info": financial_info,
            "validation_result": validation_result,
            "processing_time": datetime.now().isoformat(),
            "confidence": 0.92
        }
    
    def _parse_invoice_data(self, content: str) -> Dict[str, Any]:
        import re
        
        # Extract invoice number
        invoice_match = re.search(r'Invoice[#\s]*:?\s*([A-Z0-9-]+)', content, re.IGNORECASE)
        invoice_number = invoice_match.group(1) if invoice_match else None
        
        # Extract date
        date_match = re.search(r'Date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', content, re.IGNORECASE)
        date = date_match.group(1) if date_match else None
        
        # Extract vendor information
        vendor_match = re.search(r'From[:\s]*([^\n]+)', content, re.IGNORECASE)
        vendor = vendor_match.group(1).strip() if vendor_match else None
        
        return {
            "invoice_number": invoice_number,
            "date": date,
            "vendor": vendor
        }
    
    def _extract_financial_info(self, content: str) -> Dict[str, Any]:
        import re
        
        # Extract amounts (simple pattern matching)
        amounts = re.findall(r'\$[\d,]+\.?\d*', content)
        
        # Extract total (usually the last or largest amount)
        total = amounts[-1] if amounts else None
        
        return {
            "amounts": amounts,
            "total": total,
            "currency": "USD"  # Default assumption
        }

class WebhookAgent:
    """Agent specialized in processing webhook data"""
    
    def __init__(self):
        self.name = "WebhookAgent"
        self.capabilities = ["webhook_validation", "payload_parsing", "event_classification"]
    
    async def process(self, content: str) -> Dict[str, Any]:
        logger.info(f"{self.name} processing webhook content")
        
        try:
            # Parse JSON payload
            payload = json.loads(content)
            
            # Validate webhook
            validation_result = webhook_validator.validate(payload)
            if not validation_result["is_valid"]:
                raise ValueError(f"Invalid webhook: {validation_result['errors']}")
            
            # Classify event
            event_classification = self._classify_event(payload)
            
            # Extract metadata
            metadata = self._extract_metadata(payload)
            
            return {
                "payload": payload,
                "event_classification": event_classification,
                "metadata": metadata,
                "validation_result": validation_result,
                "processing_time": datetime.now().isoformat(),
                "confidence": 0.88
            }
        
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON payload: {str(e)}")
    
    def _classify_event(self, payload: Dict[str, Any]) -> Dict[str, str]:
        event_type = payload.get('type', 'unknown')
        source = payload.get('source', 'unknown')
        
        # Simple event classification
        if 'payment' in event_type.lower():
            category = 'financial'
        elif 'user' in event_type.lower():
            category = 'user_management'
        elif 'order' in event_type.lower():
            category = 'commerce'
        else:
            category = 'general'
        
        return {
            "event_type": event_type,
            "source": source,
            "category": category
        }
    
    def _extract_metadata(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "timestamp": payload.get('timestamp'),
            "version": payload.get('version'),
            "request_id": payload.get('id'),
            "payload_size": len(str(payload))
        }

class DocumentRouter:
    """Routes documents to appropriate agents based on content type"""
    
    def __init__(self):
        self.agents = {
            "email": EmailAgent(),
            "invoice": InvoiceAgent(),
            "webhook": WebhookAgent()
        }
    
    def route_document(self, content: str, document_type: str = None) -> str:
        """Determine which agent should process the document"""
        
        if document_type and document_type in self.agents:
            return document_type
        
        # Auto-detection logic
        content_lower = content.lower()
        
        # Check for email indicators
        if any(indicator in content_lower for indicator in ['from:', 'to:', 'subject:']):
            return "email"
        
        # Check for invoice indicators
        if any(indicator in content_lower for indicator in ['invoice', 'bill', 'amount', '$']):
            return "invoice"
        
        # Check for webhook indicators (JSON structure)
        try:
            json.loads(content)
            return "webhook"
        except:
            pass
        
        # Default to email if uncertain
        return "email"
    
    async def process_document(self, content: str, document_type: str = None) -> ProcessingResult:
        """Process document using appropriate agent"""
        
        agent_type = self.route_document(content, document_type)
        agent = self.agents[agent_type]
        
        try:
            result = await agent.process(content)
            
            return ProcessingResult(
                status="success",
                agent_used=agent.name,
                processed_data=result,
                timestamp=datetime.now().isoformat(),
                confidence_score=result.get("confidence", 0.0)
            )
        
        except Exception as e:
            logger.error(f"Error processing document with {agent.name}: {str(e)}")
            
            return ProcessingResult(
                status="error",
                agent_used=agent.name,
                processed_data={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

# Initialize router
document_router = DocumentRouter()

# API Routes
@app.get("/", response_class=HTMLResponse)
async def get_index():
    """Serve the main interface"""
    with open("static/index.html", "r") as f:
        return f.read()

@app.post("/process", response_model=ProcessingResult)
async def process_document(request: DocumentRequest):
    """Process a document using the appropriate agent"""
    
    if not request.content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")
    
    result = await document_router.process_document(
        content=request.content,
        document_type=request.document_type if request.document_type != "auto" else None
    )
    
    return result

@app.post("/upload", response_model=ProcessingResult)
async def upload_file(file: UploadFile = File(...)):
    """Upload and process a file"""
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")
    
    # Read file content
    content = await file.read()
    
    # Handle PDF files
    if file.filename.lower().endswith('.pdf'):
        try:
            text_content = pdf_parser.extract_text(content)
            result = await document_router.process_document(
                content=text_content,
                document_type="invoice"  # Assume PDFs are invoices
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    
    # Handle text files
    else:
        try:
            text_content = content.decode('utf-8')
            result = await document_router.process_document(content=text_content)
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="File must be text or PDF format")
    
    return result

@app.get("/agents")
async def get_agents():
    """Get information about available agents"""
    
    agents_info = {}
    for agent_type, agent in document_router.agents.items():
        agents_info[agent_type] = {
            "name": agent.name,
            "capabilities": agent.capabilities
        }
    
    return agents_info

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)