import json
import redis
from typing import Dict, List, Optional, Any
from datetime import datetime
from models.schemas import MemoryEntry, ClassificationResult
from config.settings import settings
import uuid

class SharedMemoryStore:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        
    def generate_id(self) -> str:
        """Generate unique ID for memory entries"""
        return str(uuid.uuid4())
    
    def store_entry(self, entry: MemoryEntry) -> str:
        """Store a memory entry"""
        try:
            entry_dict = entry.model_dump(mode='json')
            # Convert datetime to string for JSON serialization
            if isinstance(entry_dict.get('timestamp'), datetime):
                entry_dict['timestamp'] = entry_dict['timestamp'].isoformat()
            
            self.redis_client.hset(
                f"memory:{entry.id}",
                mapping={
                    "data": json.dumps(entry_dict),
                    "created_at": datetime.now().isoformat(),
                    "status": entry.status
                }
            )
            
            # Add to processing queue
            self.redis_client.lpush("processing_queue", entry.id)
            
            return entry.id
        except Exception as e:
            print(f"Error storing memory entry: {e}")
            raise
    
    def get_entry(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry"""
        try:
            data = self.redis_client.hget(f"memory:{entry_id}", "data")
            if data:
                entry_dict = json.loads(data)
                # Convert string timestamp back to datetime
                if 'timestamp' in entry_dict:
                    entry_dict['timestamp'] = datetime.fromisoformat(entry_dict['timestamp'])
                return MemoryEntry(**entry_dict)
            return None
        except Exception as e:
            print(f"Error retrieving memory entry: {e}")
            return None
    
    def update_entry(self, entry_id: str, updates: Dict[str, Any]) -> bool:
        """Update specific fields of a memory entry"""
        try:
            entry = self.get_entry(entry_id)
            if not entry:
                return False
            
            # Update the entry
            entry_dict = entry.model_dump()
            entry_dict.update(updates)
            
            updated_entry = MemoryEntry(**entry_dict)
            self.store_entry(updated_entry)
            return True
        except Exception as e:
            print(f"Error updating memory entry: {e}")
            return False
    
    def add_agent_output(self, entry_id: str, agent_name: str, output: Dict[str, Any]) -> bool:
        """Add agent output to memory entry"""
        entry = self.get_entry(entry_id)
        if entry:
            entry.agent_outputs[agent_name] = output
            entry.decision_trace.append(f"{agent_name}: {datetime.now().isoformat()}")
            return self.update_entry(entry_id, {
                "agent_outputs": entry.agent_outputs,
                "decision_trace": entry.decision_trace
            })
        return False
    
    def add_action_triggered(self, entry_id: str, action: str) -> bool:
        """Add triggered action to memory entry"""
        entry = self.get_entry(entry_id)
        if entry:
            entry.actions_triggered.append(action)
            return self.update_entry(entry_id, {
                "actions_triggered": entry.actions_triggered
            })
        return False
    
    def get_processing_queue(self) -> List[str]:
        """Get list of entries in processing queue"""
        return self.redis_client.lrange("processing_queue", 0, -1)
    
    def remove_from_queue(self, entry_id: str) -> bool:
        """Remove entry from processing queue"""
        return self.redis_client.lrem("processing_queue", 1, entry_id) > 0
    
    def get_all_entries(self) -> List[MemoryEntry]:
        """Get all memory entries"""
        keys = self.redis_client.keys("memory:*")
        entries = []
        for key in keys:
            entry_id = key.split(":")[1]
            entry = self.get_entry(entry_id)
            if entry:
                entries.append(entry)
        return entries
    
    def clear_all(self) -> bool:
        """Clear all memory entries (for testing)"""
        try:
            keys = self.redis_client.keys("memory:*")
            if keys:
                self.redis_client.delete(*keys)
            self.redis_client.delete("processing_queue")
            return True
        except Exception as e:
            print(f"Error clearing memory: {e}")
            return False

# Global memory instance
memory_store = SharedMemoryStore()