import asyncio
import requests
from typing import Dict, Any, List
from datetime import datetime
from models.schemas import ActionRequest, Urgency
from memory.shared_memory import memory_store
from config.settings import settings

class ActionRouter:
    def __init__(self):
        self.action_handlers = {
            # Email actions
            "escalate_to_manager": self._escalate_to_manager,
            "create_priority_ticket": self._create_priority_ticket,
            "create_high_priority_ticket": self._create_high_priority_ticket,
            "notify_team_lead": self._notify_team_lead,
            "standard_response": self._standard_response,
            "log_and_track": self._log_and_track,
            
            # JSON actions
            "log_schema_violation": self._log_schema_violation,
            "notify_integration_team": self._notify_integration_team,
            "flag_financial_review": self._flag_financial_review,
            "log_data_quality_issue": self._log_data_quality_issue,
            "quarantine_for_review": self._quarantine_for_review,
            
            # PDF actions
            "require_manager_approval": self._require_manager_approval,
            "route_to_compliance_team": self._route_to_compliance_team,
            "notify_data_protection_officer": self._notify_data_protection_officer,
            "route_to_regulatory_affairs": self._route_to_regulatory_affairs,
            "encrypt_and_secure": self._encrypt_and_secure,
            "prioritize_processing": self._prioritize_processing,
            
            # General actions
            "log_error": self._log_error,
            "alert_admin": self._alert_admin,
            "process_normally": self._process_normally,
            "standard_processing": self._standard_processing
        }
        
        self.external_apis = {
            "crm": settings.CRM_API_URL,
            "risk": settings.RISK_API_URL
        }
    
    async def route_actions(self, actions: List[str], context: Dict[str, Any], entry_id: str) -> Dict[str, Any]:
        """Route and execute actions based on agent recommendations"""
        results = {}
        
        for action in actions:
            try:
                if action in self.action_handlers:
                    result = await self.action_handlers[action](context, entry_id)
                    results[action] = result
                    
                    # Log action to memory
                    memory_store.add_action_triggered(entry_id, f"{action}: {result.get('status', 'completed')}")
                else:
                    results[action] = {"status": "unknown_action", "message": f"No handler for action: {action}"}
                    
            except Exception as e:
                results[action] = {"status": "error", "message": str(e)}
        
        return results
    
    # Email Action Handlers
    async def _escalate_to_manager(self, context: Dict[str, Any], entry_id: str) -> Dict[str, Any]:
        """Escalate issue to manager"""
        payload = {
            "type": "escalation",
            "entry_id": entry_id,
            "urgency": "high",
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        
        # Simulate CRM API call
        response = await self._call_external_api("crm", "/escalate", payload)
        
        return {
            "status": "escalated",
            "ticket_id": response.get("ticket_id", f"ESC-{entry_id[:8]}"),
            "assigned_to": "manager@company.com",
            "message": "Issue escalated to management"
        }
    
    async def _create_priority_ticket(self, context: Dict[str, Any], entry_id: str) -> Dict[str, Any]:
        """Create high priority ticket"""
        payload = {
            "type": "priority_ticket",
            "entry_id": entry_id,
            "priority": "high",
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        
        response = await self._call_external_api("crm", "/tickets", payload)
        
        return {
            "status": "ticket_created",
            "ticket_id": response.get("ticket_id", f"PRI-{entry_id[:8]}"),
            "priority": "high",
            "message": "Priority ticket created"
        }
    
    async def _create_high_priority_ticket(self, context: Dict[str, Any], entry_id: str) -> Dict[str, Any]:
        """Create high priority ticket"""
        return await self._create_priority_ticket(context, entry_id)
    
    async def _notify_team_lead(self, context: Dict[str, Any], entry_id: str) -> Dict[str, Any]:
        """Notify team lead"""
        return {
            "status": "notified",
            "notification_id": f"NOT-{entry_id[:8]}",
            "recipient": "teamlead@company.com",
            "message": "Team lead notified of high priority issue"
        }
    
    async def _standard_response(self, context: Dict[str, Any], entry_id: str) -> Dict[str, Any]:
        """Send standard response"""
        return {
            "status": "response_sent",
            "response_id": f"RSP-{entry_id[:8]}",
            "message": "Standard response sent to customer"
        }
    
    async def _log_and_track(self, context: Dict[str, Any], entry_id: str) -> Dict[str, Any]:
        """Log and track issue"""
        return {
            "status": "logged",
            "tracking_id": f"TRK-{entry_id[:8]}",
            "message": "Issue logged and being tracked"
        }
    
    # JSON Action Handlers
    async def _log_schema_violation(self, context: Dict[str, Any], entry_id: str) -> Dict[str, Any]:
        """Log schema validation violation"""
        return {
            "status": "logged",
            "violation_id": f"SCH-{entry_id[:8]}",
            "message": "Schema violation logged for review"
        }
    
    async def _notify_integration_team(self, context: Dict[str, Any], entry_id: str) -> Dict[str, Any]:
        """Notify integration team of issues"""
        return {
            "status": "notified",
            "notification_id": f"INT-{entry_id[:8]}",
            "recipient": "integration@company.com",
            "message": "Integration team notified of data issues"
        }
    
    async def _flag_financial_review(self, context: Dict[str, Any], entry_id: str) -> Dict[str, Any]:
        """Flag for financial review"""
        payload = {
            "type": "financial_review",
            "entry_id": entry_id,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        
        response = await self._call_external_api("risk", "/financial_review", payload)
        
        return {
            "status": "flagged",
            "review_id": response.get("review_id", f"FIN-{entry_id[:8]}"),
            "message": "Flagged for financial review"
        }
    
    async def _log_data_quality_issue(self, context: Dict[str, Any], entry_id: str) -> Dict[str, Any]:
        """Log data quality issue"""
        return {
            "status": "logged",
            "issue_id": f"DQ-{entry_id[:8]}",
            "message": "Data quality issue logged"
        }
    
    async def _quarantine_for_review(self, context: Dict[str, Any], entry_id: str) -> Dict[str, Any]:
        """Quarantine data for manual review"""
        return {
            "status": "quarantined",
            "quarantine_id": f"QUA-{entry_id[:8]}",
            "message": "Data quarantined for manual review"
        }
    
    # PDF Action Handlers
    async def _require_manager_approval(self, context: Dict[str, Any], entry_id: str) -> Dict[str, Any]:
        """Require manager approval"""
        return {
            "status": "pending_approval",
            "approval_id": f"APP-{entry_id[:8]}",
            "approver": "manager@company.com",
            "message": "Awaiting manager approval"
        }
    
    async def _route_to_compliance_team(self, context: Dict[str, Any], entry_id: str) -> Dict[str, Any]:
        """Route to compliance team"""
        return {
            "status": "routed",
            "routing_id": f"COM-{entry_id[:8]}",
            "recipient": "compliance@company.com",
            "message": "Routed to compliance team"
        }
    
    async def _notify_data_protection_officer(self, context: Dict[str, Any], entry_id: str) -> Dict[str, Any]:
        """Notify data protection officer"""
        return {
            "status": "notified",
            "notification_id": f"DPO-{entry_id[:8]}",
            "recipient": "dpo@company.com",
            "message": "Data protection officer notified"
        }
    
    async def _route_to_regulatory_affairs(self, context: Dict[str, Any], entry_id: str) -> Dict[str, Any]:
        """Route to regulatory affairs"""
        return {
            "status": "routed",
            "routing_id": f"REG-{entry_id[:8]}",
            "recipient": "regulatory@company.com",
            "message": "Routed to regulatory affairs"
        }
    
    async def _encrypt_and_secure(self, context: Dict[str, Any], entry_id: str) -> Dict[str, Any]:
        """Encrypt and secure sensitive document"""
        return {
            "status": "secured",
            "security_id": f"SEC-{entry_id[:8]}",
            "message": "Document encrypted and secured"
        }
    
    async def _prioritize_processing(self, context: Dict[str, Any], entry_id: str) -> Dict[str, Any]:
        """Prioritize document processing"""
        return {
            "status": "prioritized",
            "priority_id": f"PRI-{entry_id[:8]}",
            "message": "Document processing prioritized"
        }
    
    # General Action Handlers
    async def _log_error(self, context: Dict[str, Any], entry_id: str) -> Dict[str, Any]:
        """Log error"""
        return {
            "status": "logged",
            "error_id": f"ERR-{entry_id[:8]}",
            "message": "Error logged for investigation"
        }
    
    async def _alert_admin(self, context: Dict[str, Any], entry_id: str) -> Dict[str, Any]:
        """Alert administrator"""
        return {
            "status": "alerted",
            "alert_id": f"ADM-{entry_id[:8]}",
            "recipient": "admin@company.com",
            "message": "Administrator alerted"
        }
    
    async def _process_normally(self, context: Dict[str, Any], entry_id: str) -> Dict[str, Any]:
        """Process normally"""
        return {
            "status": "processing",
            "process_id": f"NOR-{entry_id[:8]}",
            "message": "Processing normally"
        }
    
    async def _standard_processing(self, context: Dict[str, Any], entry_id: str) -> Dict[str, Any]:
        """Standard processing"""
        return await self._process_normally(context, entry_id)
    
    # Helper Methods
    async def _call_external_api(self, service: str, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate external API calls"""
        # In a real implementation, this would make actual HTTP requests
        # For simulation, we'll return mock responses
        
        if service == "crm":
            return {
                "ticket_id": f"TKT-{payload['entry_id'][:8]}",
                "status": "created",
                "timestamp": datetime.now().isoformat()
            }
        elif service == "risk":
            return {
                "review_id": f"REV-{payload['entry_id'][:8]}",
                "status": "flagged",
                "timestamp": datetime.now().isoformat()
            }
        
        return {"status": "simulated", "message": f"Simulated call to {service}{endpoint}"}

# Global action router instance
action_router = ActionRouter()