# Multi-Agent Document Processing System

A modular, extensible document-processing system powered by specialized agents to intelligently handle emails, invoices (PDFs), and webhooks (JSON payloads).

## Architecture Overview

The system is built as a FastAPI application with the following layered components:

- **API Layer**: Exposes HTTP endpoints for document processing, file upload, agent information, and health checks.
- **Routing Layer**: Determines the document type (email, invoice, webhook) and delegates processing to the correct agent.
- **Agent Layer**: Specialized classes that encapsulate logic for email, invoice, and webhook document processing.
- **Utility Layer**: Utilities for PDF extraction, validation, and data parsing.

### Key Files & Structure

```
main.py                  # Main workflow and API
utils/pdf_parser.py      # PDF text extraction
utils/validators.py      # Email, invoice, webhook validation logic
static/index.html        # Main web interface
static/                  # Static assets (images, etc.)
```

## Agent Logic and Chaining

### Document Flow

1. **Input**: User submits content via the `/process` or `/upload` endpoint.
2. **Routing**: The `DocumentRouter` inspects content or uses the provided type to select an agent.
3. **Agent Processing**:
   - **EmailAgent**: Parses email, validates, extracts sentiment/entities.
   - **InvoiceAgent**: Parses invoice data, validates, extracts amounts/vendor.
   - **WebhookAgent**: Parses JSON, validates schema, classifies event.
4. **Output**: A structured result object with status, agent used, extracted data, and (optionally) a confidence score.

### Agent Chaining
The current system routes to a single best-fit agent, but the architecture supports agent chaining by updating the `DocumentRouter` to allow multiple agents to process or enrich a document sequentially.

---

## Diagram: Agent Flow and Chaining


```
flowchart TD
    A[User/API Request] --> B[DocumentRouter]
    B -->|Email| C[EmailAgent]
    B -->|Invoice (PDF)| D[InvoiceAgent]
    B -->|Webhook (JSON)| E[WebhookAgent]
    C --> F[ProcessingResult]
    D --> F
    E --> F
    F --> G[API Response / Output]
```

```
                        ┌──────────────────────┐
                        │      User/API        │
                        └────────┬─────────────┘
                                 │
                        HTTP POST /process
                                 │
                       ┌─────────▼────────────┐
                       │     main.py (API)    │
                       └────────┬─────────────┘
                                │
                     Determines document_type
                                │
               ┌────────────────┼─────────────────┐
               ▼                ▼                 ▼
        ┌────────────┐   ┌────────────┐    ┌────────────┐
        │ EmailAgent │   │ PDFParser  │    │ JSONAgent  │
        └────────────┘   └────────────┘    └────────────┘
               │                │                 │
        Validation     Text/Entity Extraction   Analysis
               ▼                ▼                 ▼
        ┌────────────┐   ┌────────────┐    ┌────────────┐
        │  Results    │◄─┴──┬──────────┴───►│ Confidence │
        └────────────┘     │                └────────────┘
                           ▼
                  Response to User

```

---

## Sample Inputs

### Email
```
From: alice@example.com
To: bob@example.com
Subject: Meeting Tomorrow

Hi Bob,
Let's meet tomorrow at 10am to discuss the project.
Best,
Alice
```

### PDF (Invoice)
Upload a PDF file containing an invoice with headers like "Invoice #", "Date", "From", and a list of items/amounts. The system will extract text using PDFParser.

### Webhook (JSON)
```json
{
  "type": "payment_succeeded",
  "source": "stripe",
  "timestamp": "2025-06-01T12:30:00Z",
  "version": "1.2",
  "id": "req_123abc",
  "amount": 120.75
}
```

---

## Sample Output Log

```json
{
  "status": "success",
  "agent_used": "EmailAgent",
  "processed_data": {
    "email_data": {
      "from": "alice@example.com",
      "to": "bob@example.com",
      "subject": "Meeting Tomorrow",
      "body": "Hi Bob,\nLet's meet tomorrow at 10am to discuss the project.\nBest,\nAlice\n"
    },
    "sentiment": {
      "sentiment": "positive",
      "positive_score": 2,
      "negative_score": 0
    },
    "entities": {
      "emails": [],
      "phones": [],
      "dates": ["tomorrow at 10am"]
    },
    "processing_time": "2025-06-01T13:08:42",
    "confidence": 0.85
  },
  "timestamp": "2025-06-01T13:08:42",
  "confidence_score": 0.85
}
```

---

## Post-Action Output / Screenshots

![Agent Flow](screenshots\image1.png)
![Agent Flow](screenshots\image2.png)
![Agent Flow](screenshots\image3.png)
![Agent Flow](screenshots\image4.png)
![Agent Flow](screenshots\image5.png)

---

## Extending/Customizing

- **Add new agents**: Implement a new agent class and register it in `DocumentRouter`.
- **Add new validations**: Extend `utils/validators.py`.
- **Chain agents**: Modify `DocumentRouter.process_document` to call multiple agents (or implement hooks).

---

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt
py -m pip install fastapi==0.104.1 uvicorn==0.24.0 pydantic==2.5.0 redis==5.0.1 sqlalchemy==2.0.23 PyPDF2==3.0.1 python-multipart==0.0.6 faker==19.13.0 requests==2.31.0 email-validator==2.1.1
pip install fastapi uvicorn python-multipart pydantic python-jose[cryptography] passlib[bcrypt] aiofiles
py -m pip install python-multipart 
py -m pip install "uvicorn[standard]"
py -m pip install fastapi


# Run the API
py -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

```
Visit [localhost:8000](http://localhost:8000) for the web interface.
oe
Run index.html


---

## License

MIT

---

## Further Reading

- [main.py full source](https://github.com/agrani0613s/multi_agent_system/blob/main/main.py)
- [Code search for more files in this repo](https://github.com/agrani0613s/multi_agent_system/search?type=code)

---

_This README is generated and may need to be updated as the project evolves. For questions or contributions, please open an issue or pull request!_