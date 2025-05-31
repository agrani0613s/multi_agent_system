import json
from typing import Dict, Any, List
from datetime import datetime
from agents.base_agent import BaseAgent
from models.schemas import ClassificationResult, JSONData

class JSONAgent(BaseAgent):
    def __init__(self):
        super().__init__("JSONAgent")
        
        # Common webhook schemas to validate against
        self.webhook_schemas = {
            "payment": {
                "required_fields": ["transaction_id", "amount", "currency", "status"],
                "optional_fields": ["user_id", "timestamp", "method"]
            },
            "user_event": {
                "required_fields": ["user_id", "event_type", "timestamp"],
                "optional_fields": ["data", "session_id", "ip_address"]
            },
            "order": {
                "required_fields": ["order_id", "customer_id", "items", "total"],
                "optional_fields": ["shipping_address", "billing_address", "status"]
            },
            "system_alert": {
                "required_fields": ["alert_type", "severity", "message", "timestamp"],
                "optional_fields": ["source", "details", "correlation_id"]
            }
        }
        
        self.anomaly_patterns = [
            "missing_required_field",
            "type_mismatch",
            "invalid_enum_value",
            "suspicious_amount",
            "unusual_timestamp",
            "malformed_structure"
        ]
    
    async def process(self, input_data: str, classification: ClassificationResult, entry_id: str) -> Dict[str, Any]:
        """Process JSON data and validate schema"""
        
        try:
            # Parse JSON
            json_data = json.loads(input_data)
            
            # Detect webhook type
            webhook_type = self._detect_webhook_type(json_data)
            
            # Validate schema
            schema_valid, validation_errors = self._validate_schema(json_data, webhook_type)
            
            # Detect anomalies
            anomalies = self._detect_anomalies(json_data, webhook_type)
            
            # Extract structured fields
            extracted_fields = self._extract_fields(json_data)
            
            result = {
                "agent": self.name,
                "json_data": {
                    "webhook_type": webhook_type,
                    "payload": json_data,
                    "schema_valid": schema_valid,
                    "validation_errors": validation_errors,
                    "anomalies": anomalies,
                    "extracted_fields": extracted_fields
                },
                "recommended_actions": self._recommend_actions(anomalies, schema_valid),
                "processing_metadata": {
                    "parsed_successfully": True,
                    "field_count": len(json_data) if isinstance(json_data, dict) else 0,
                    "confidence": classification.confidence_score
                }
            }
            
            # Log decision
            self.log_decision(entry_id, f"JSON processed - Type: {webhook_type}, Valid: {schema_valid}, Anomalies: {len(anomalies)}")
            
        except json.JSONDecodeError as e:
            result = {
                "agent": self.name,
                "json_data": {
                    "webhook_type": "invalid",
                    "payload": {},
                    "schema_valid": False,
                    "validation_errors": [f"JSON Parse Error: {str(e)}"],
                    "anomalies": ["malformed_json"],
                    "extracted_fields": {}
                },
                "recommended_actions": ["log_error", "alert_admin"],
                "processing_metadata": {
                    "parsed_successfully": False,
                    "error": str(e),
                    "confidence": 0.0
                }
            }
            
            self.log_decision(entry_id, f"JSON parsing failed: {str(e)}")
        
        return result
    
    def _detect_webhook_type(self, json_data: Dict[str, Any]) -> str:
        """Detect the type of webhook based on field patterns"""
        if not isinstance(json_data, dict):
            return "unknown"
        
        # Check for payment webhook
        if any(field in json_data for field in ["transaction_id", "payment_id", "amount", "currency"]):
            return "payment"
        
        # Check for user event webhook
        if any(field in json_data for field in ["user_id", "event_type", "session_id"]):
            return "user_event"
        
        # Check for order webhook
        if any(field in json_data for field in ["order_id", "customer_id", "items"]):
            return "order"
        
        # Check for system alert
        if any(field in json_data for field in ["alert_type", "severity", "message"]):
            return "system_alert"
        
        return "generic"
    
    def _validate_schema(self, json_data: Dict[str, Any], webhook_type: str) -> tuple[bool, List[str]]:
        """Validate JSON against expected schema"""
        errors = []
        
        if webhook_type not in self.webhook_schemas:
            return True, []  # No validation for unknown types
        
        schema = self.webhook_schemas[webhook_type]
        
        # Check required fields
        for field in schema["required_fields"]:
            if field not in json_data:
                errors.append(f"Missing required field: {field}")
            elif json_data[field] is None:
                errors.append(f"Required field '{field}' is null")
        
        # Type validation
        self._validate_field_types(json_data, errors)
        
        return len(errors) == 0, errors
    
    def _validate_field_types(self, json_data: Dict[str, Any], errors: List[str]) -> None:
        """Validate field types"""
        # Amount fields should be numeric
        if "amount" in json_data and not isinstance(json_data["amount"], (int, float)):
            errors.append("Field 'amount' should be numeric")
        
        # Timestamp fields should be strings or numbers
        if "timestamp" in json_data:
            if not isinstance(json_data["timestamp"], (str, int, float)):
                errors.append("Field 'timestamp' should be string or number")
        
        # ID fields should be strings or numbers
        for field in json_data:
            if field.endswith("_id") and not isinstance(json_data[field], (str, int)):
                errors.append(f"ID field '{field}' should be string or number")
    
    def _detect_anomalies(self, json_data: Dict[str, Any], webhook_type: str) -> List[str]:
        """Detect anomalies in JSON data"""
        anomalies = []
        
        # Check for suspicious amounts
        if "amount" in json_data:
            try:
                amount = float(json_data["amount"])
                if amount < 0:
                    anomalies.append("negative_amount")
                elif amount > 100000:  # Configurable threshold
                    anomalies.append("unusually_high_amount")
            except (ValueError, TypeError):
                anomalies.append("invalid_amount_format")
        
        # Check for unusual timestamps
        if "timestamp" in json_data:
            try:
                if isinstance(json_data["timestamp"], str):
                    # Try to parse timestamp
                    datetime.fromisoformat(json_data["timestamp"].replace('Z', '+00:00'))
                elif isinstance(json_data["timestamp"], (int, float)):
                    # Unix timestamp validation
                    if json_data["timestamp"] < 0 or json_data["timestamp"] > 2147483647:
                        anomalies.append("invalid_timestamp_range")
            except ValueError:
                anomalies.append("malformed_timestamp")
        
        # Check for empty required arrays
        if webhook_type == "order" and "items" in json_data:
            if isinstance(json_data["items"], list) and len(json_data["items"]) == 0:
                anomalies.append("empty_items_array")
        
        # Check for suspicious field values
        if "status" in json_data:
            suspicious_statuses = ["test", "debug", "fake", "dummy"]
            if str(json_data["status"]).lower() in suspicious_statuses:
                anomalies.append("suspicious_status_value")
        
        return anomalies
    
    def _extract_fields(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract important fields for further processing"""
        extracted = {}
        
        # Extract common fields
        important_fields = [
            "user_id", "customer_id", "transaction_id", "order_id",
            "amount", "currency", "status", "timestamp", "event_type"
        ]
        
        for field in important_fields:
            if field in json_data:
                extracted[field] = json_data[field]
        
        # Extract nested data
        if "data" in json_data and isinstance(json_data["data"], dict):
            extracted["nested_data_keys"] = list(json_data["data"].keys())
        
        # Calculate payload size
        extracted["payload_size"] = len(str(json_data))
        extracted["field_count"] = len(json_data)
        
        return extracted
    
    def _recommend_actions(self, anomalies: List[str], schema_valid: bool) -> List[str]:
        """Recommend actions based on validation results"""
        actions = []
        
        if not schema_valid:
            actions.append("log_schema_violation")
            actions.append("notify_integration_team")
        
        if anomalies:
            if any(anomaly in ["negative_amount", "unusually_high_amount"] for anomaly in anomalies):
                actions.append("flag_financial_review")
            
            if "malformed_timestamp" in anomalies:
                actions.append("log_data_quality_issue")
            
            if len(anomalies) > 2:
                actions.append("quarantine_for_review")
        else:
            actions.append("process_normally")
        
        return actions