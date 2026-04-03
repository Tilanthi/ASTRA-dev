import json
import time
from pathlib import Path
from typing import Dict, Any, List

class AuditLogger:
    def __init__(self, log_dir: str = "/shared/ASTRA/logs/audit"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        # One file per day to prevent massive logs
        self.current_date = time.strftime("%Y-%m-%d")
        self.log_file = self.log_dir / f"audit_{self.current_date}.jsonl"

    def log_event(self, module: str, action: str, details: Dict[str, Any], actor: str = "System"):
        """Log a structured audit event."""
        # Check if day rolled over
        today = time.strftime("%Y-%m-%d")
        if today != self.current_date:
            self.current_date = today
            self.log_file = self.log_dir / f"audit_{self.current_date}.jsonl"

        event = {
            "timestamp": time.time(),
            "time_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "module": module,
            "action": action,
            "actor": actor,
            "details": details
        }

        with open(self.log_file, "a") as f:
            f.write(json.dumps(event) + "\n")
            
        return event

    def get_recent(self, limit: int = 50) -> List[Dict]:
        """Get recent audit events."""
        events = []
        if not self.log_file.exists():
            return events
            
        # Very simple tail (reads whole file, inefficient for huge files but okay for phase 2)
        try:
            with open(self.log_file, "r") as f:
                lines = f.readlines()
                for line in reversed(lines[-limit:]):
                    events.append(json.loads(line.strip()))
        except Exception:
            pass
            
        return events
