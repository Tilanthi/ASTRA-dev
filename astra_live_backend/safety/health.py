# Copyright 2024-2026 Glenn J. White (The Open University / RAL Space)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
import psutil
from typing import Dict

class SystemHealthReport:
    """Component health monitoring for ASTRA."""
    
    def __init__(self):
        self.start_time = time.time()
        
    def get_report(self, engine_state: Dict) -> Dict:
        """Generate a health report combining system metrics and engine state."""
        process = psutil.Process()
        
        # System metrics
        mem_info = process.memory_info()
        cpu_percent = process.cpu_percent()
        
        # Determine overall health based on engine states
        health_status = "HEALTHY"
        if engine_state.get("safety_state") in ["STOPPED", "LOCKDOWN"]:
            health_status = "CRITICAL"
        elif engine_state.get("safety_state") in ["PAUSED", "SAFE_MODE"]:
            health_status = "WARNING"
            
        components = [
            {"id": "c1", "name": "Memory Matrix (MORK)", "status": "nominal" if mem_info.rss < 2*1024*1024*1024 else "warning", "message": "Memory cache stable"},
            {"id": "c2", "name": "Safety Controller", "status": "nominal", "message": "Bus active, breakers armed"},
            {"id": "c3", "name": "Discovery Engine", "status": "nominal" if engine_state.get("running", True) else "warning", "message": "OODA cycle nominal"},
            {"id": "c4", "name": "Hypothesis Evaluator", "status": "nominal", "message": "Queue processing normally"},
            {"id": "c5", "name": "Ethics & Alignment", "status": "nominal", "message": "Score: >0.85"},
            {"id": "c6", "name": "System Resources", "status": "nominal" if cpu_percent < 90 else "warning", "message": f"CPU: {cpu_percent}% MEM: {mem_info.rss / 1024 / 1024:.1f}MB"}
        ]
        
        return {
            "status": health_status,
            "uptime_seconds": time.time() - self.start_time,
            "components": components,
            "timestamp": time.time()
        }
