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

"""
ASTRA V9.0 — Expertise Tracker
Tracks agent specializations, performance, and learning across tasks.
"""

import time
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from .agent_factory import ScientificAgent, AgentRole


class ExpertiseLevel(Enum):
    """Levels of expertise."""
    NOVICE = "novice"
    DEVELOPING = "developing"
    COMPETENT = "competent"
    EXPERT = "expert"
    MASTER = "master"


@dataclass
class TaskPerformance:
    """Record of agent performance on a specific task."""
    task_id: str
    agent_id: str
    agent_role: AgentRole
    domain: str
    method: str
    success: bool
    confidence: float
    time_taken: float
    timestamp: float = field(default_factory=time.time)
    feedback: Optional[str] = None


@dataclass
class SpecializationProfile:
    """Profile of agent's specialized expertise."""
    agent_id: str
    agent_role: AgentRole
    primary_domains: List[str]
    secondary_domains: List[str]
    preferred_methods: List[str]
    expertise_by_domain: Dict[str, float]  # domain -> confidence (0-1)
    performance_by_method: Dict[str, float]  # method -> success rate
    total_tasks: int = 0
    successful_tasks: int = 0
    overall_success_rate: float = 0.0


class ExpertiseTracker:
    """
    Tracks and analyzes agent expertise and performance over time.

    Maintains records of:
    - Domain specializations
    - Method preferences and performance
    - Learning progress
    - Collaborative patterns
    """

    def __init__(self, db_path: str = "astra_agent_expertise.db"):
        self.db_path = db_path
        self.agent_profiles: Dict[str, SpecializationProfile] = {}
        self.task_history: List[TaskPerformance] = []
        self.collaboration_matrix: Dict[Tuple[str, str], int] = defaultdict(int)

        # Initialize database
        self._init_db()

    def _init_db(self):
        """Initialize database for tracking expertise."""
        import sqlite3
        import os

        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")

        # Create task performance table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS task_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                agent_role TEXT NOT NULL,
                domain TEXT NOT NULL,
                method TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                confidence REAL NOT NULL,
                time_taken REAL NOT NULL,
                timestamp REAL NOT NULL,
                feedback TEXT
            )
        """)

        # Create agent profile table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_profiles (
                agent_id TEXT PRIMARY KEY,
                agent_role TEXT NOT NULL,
                primary_domains TEXT NOT NULL,
                secondary_domains TEXT,
                preferred_methods TEXT,
                expertise_by_domain TEXT NOT NULL,
                performance_by_method TEXT NOT NULL,
                total_tasks INTEGER DEFAULT 0,
                successful_tasks INTEGER DEFAULT 0,
                overall_success_rate REAL DEFAULT 0.0,
                last_updated REAL NOT NULL
            )
        """)

        # Create collaboration table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_collaborations (
                agent_id_1 TEXT NOT NULL,
                agent_id_2 TEXT NOT NULL,
                collaboration_count INTEGER DEFAULT 1,
                last_collaboration REAL NOT NULL,
                success_rate REAL DEFAULT 0.0,
                PRIMARY KEY (agent_id_1, agent_id_2)
            )
        """)

        conn.commit()
        conn.close()

    def register_agent(self, agent: ScientificAgent) -> SpecializationProfile:
        """Register an agent and create initial profile."""
        profile = SpecializationProfile(
            agent_id=agent.id,
            agent_role=agent.role,
            primary_domains=agent.expertise.domains[:3],  # Top 3 domains
            secondary_domains=agent.expertise.domains[3:] if len(agent.expertise.domains) > 3 else [],
            preferred_methods=agent.expertise.methods,
            expertise_by_domain=agent.expertise.confidence_by_domain.copy(),
            performance_by_method={method: 0.5 for method in agent.expertise.methods}
        )

        self.agent_profiles[agent.id] = profile

        # Persist to database
        self._save_profile(profile)

        return profile

    def record_performance(self, performance: TaskPerformance) -> None:
        """Record agent performance on a task."""
        # Add to history
        self.task_history.append(performance)

        # Update agent profile
        if performance.agent_id in self.agent_profiles:
            profile = self.agent_profiles[performance.agent_id]

            profile.total_tasks += 1
            if performance.success:
                profile.successful_tasks += 1

            profile.overall_success_rate = (
                profile.successful_tasks / profile.total_tasks
            )

            # Update method performance
            if performance.method not in profile.performance_by_method:
                profile.performance_by_method[performance.method] = 0.5

            # Update method success rate with exponential moving average
            old_rate = profile.performance_by_method[performance.method]
            alpha = 0.3  # Learning rate
            new_rate = alpha * (1.0 if performance.success else 0.0) + (1 - alpha) * old_rate
            profile.performance_by_method[performance.method] = new_rate

            # Update domain expertise
            if performance.domain in profile.expertise_by_domain:
                old_expertise = profile.expertise_by_domain[performance.domain]
                # Adjust expertise based on performance
                adjustment = 0.05 if performance.success else -0.03
                new_expertise = max(0.1, min(0.95, old_expertise + adjustment))
                profile.expertise_by_domain[performance.domain] = new_expertise

            # Save updated profile
            self._save_profile(profile)

        # Persist to database
        self._save_performance(performance)

    def record_collaboration(self, agent_id_1: str, agent_id_2: str,
                            success: bool) -> None:
        """Record collaboration between two agents."""
        key = tuple(sorted([agent_id_1, agent_id_2]))
        self.collaboration_matrix[key] += 1

        # Persist to database
        self._save_collaboration(agent_id_1, agent_id_2, success)

    def get_agent_profile(self, agent_id: str) -> Optional[SpecializationProfile]:
        """Get agent's specialization profile."""
        return self.agent_profiles.get(agent_id)

    def get_expertise_level(self, agent_id: str,
                           domain: str) -> ExpertiseLevel:
        """Get agent's expertise level in a specific domain."""
        profile = self.agent_profiles.get(agent_id)
        if not profile:
            return ExpertiseLevel.NOVICE

        expertise = profile.expertise_by_domain.get(domain, 0.0)

        if expertise >= 0.9:
            return ExpertiseLevel.MASTER
        elif expertise >= 0.75:
            return ExpertiseLevel.EXPERT
        elif expertise >= 0.5:
            return ExpertiseLevel.COMPETENT
        elif expertise >= 0.3:
            return ExpertiseLevel.DEVELOPING
        else:
            return ExpertiseLevel.NOVICE

    def recommend_agent_for_task(self, task_domain: str,
                                task_type: str,
                                exclude_agents: Optional[List[str]] = None) -> Optional[str]:
        """Recommend best agent for a specific task."""
        exclude = set(exclude_agents or [])

        candidates = []

        for agent_id, profile in self.agent_profiles.items.items():
            if agent_id in exclude:
                continue

            # Check domain expertise
            domain_expertise = profile.expertise_by_domain.get(task_domain, 0.0)

            # Check method performance
            method_performance = profile.performance_by_method.get(task_type, 0.5)

            # Combined score
            score = 0.6 * domain_expertise + 0.4 * method_performance

            candidates.append((agent_id, score))

        if not candidates:
            return None

        # Sort by score and return top candidate
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    def get_collaborative_teams(self, task_domains: List[str],
                             team_size: int = 3) -> List[List[str]]:
        """Recommend teams of agents with complementary expertise."""
        # For each domain, get top agents
        domain_agents = {}

        for domain in task_domains:
            domain_agents[domain] = []
            for agent_id, profile in self.agent_profiles.items():
                if domain in profile.expertise_by_domain:
                    expertise = profile.expertise_by_domain[domain]
                    domain_agents[domain].append((agent_id, expertise))

            # Sort by expertise
            domain_agents[domain].sort(key=lambda x: x[1], reverse=True)

        # Build teams with complementary expertise
        teams = []

        # Greedy team formation
        used_agents = set()

        while len(used_agents) < len(self.agent_profiles) and team_size > 0:
            team = []

            for domain in task_domains:
                # Get top available agent for this domain
                for agent_id, expertise in domain_agents.get(domain, []):
                    if agent_id not in used_agents and agent_id not in team:
                        team.append(agent_id)
                        break

                if len(team) >= team_size:
                    break

            if team:
                teams.append(team)
                used_agents.update(team)

        return teams

    def get_performance_summary(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get performance summary for an agent."""
        profile = self.agent_profiles.get(agent_id)
        if not profile:
            return None

        # Get recent tasks
        recent_tasks = [t for t in self.task_history if t.agent_id == agent_id][-20:]

        return {
            "agent_id": agent_id,
            "role": profile.agent_role.value,
            "total_tasks": profile.total_tasks,
            "successful_tasks": profile.successful_tasks,
            "overall_success_rate": profile.overall_success_rate,
            "primary_domains": profile.primary_domains,
            "expertise_levels": {
                domain: self.get_expertise_level(agent_id, domain).value
                for domain in profile.expertise_by_domain.keys()
            },
            "method_performance": profile.performance_by_method,
            "recent_performance": {
                "tasks": len(recent_tasks),
                "success_rate": sum(1 for t in recent_tasks if t.success) / len(recent_tasks) if recent_tasks else 0
            }
        }

    def get_collaboration_network(self) -> Dict[str, Any]:
        """Get collaboration network between agents."""
        nodes = []
        edges = []

        # Get all agents
        for agent_id, profile in self.agent_profiles.items():
            nodes.append({
                "id": agent_id,
                "role": profile.agent_role.value,
                "success_rate": profile.overall_success_rate,
                "total_tasks": profile.total_tasks
            })

        # Get collaboration edges
        edge_set = set()
        for (agent_1, agent_2), count in self.collaboration_matrix.items():
            if count > 0:
                edge_key = tuple(sorted([agent_1, agent_2]))
                if edge_key not in edge_set:
                    edge_set.add(edge_key)
                    edges.append({
                        "source": agent_1,
                        "target": agent_2,
                        "collaborations": count
                    })

        return {
            "nodes": nodes,
            "edges": edges,
            "total_collaborations": sum(self.collaboration_matrix.values())
        }

    def _save_profile(self, profile: SpecializationProfile) -> None:
        """Save agent profile to database."""
        import sqlite3

        conn = sqlite3.connect(self.db_path)

        conn.execute("""
            INSERT OR REPLACE INTO agent_profiles
            (agent_id, agent_role, primary_domains, secondary_domains,
             preferred_methods, expertise_by_domain, performance_by_method,
             total_tasks, successful_tasks, overall_success_rate, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            profile.agent_id,
            profile.agent_role.value,
            json.dumps(profile.primary_domains),
            json.dumps(profile.secondary_domains),
            json.dumps(profile.preferred_methods),
            json.dumps(profile.expertise_by_domain),
            json.dumps(profile.performance_by_method),
            profile.total_tasks,
            profile.successful_tasks,
            profile.overall_success_rate,
            time.time()
        ))

        conn.commit()
        conn.close()

    def _save_performance(self, performance: TaskPerformance) -> None:
        """Save task performance to database."""
        import sqlite3

        conn = sqlite3.connect(self.db_path)

        conn.execute("""
            INSERT INTO task_performance
            (task_id, agent_id, agent_role, domain, method, success,
             confidence, time_taken, timestamp, feedback)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            performance.task_id,
            performance.agent_id,
            performance.agent_role.value,
            performance.domain,
            performance.method,
            performance.success,
            performance.confidence,
            performance.time_taken,
            performance.timestamp,
            performance.feedback
        ))

        conn.commit()
        conn.close()

    def _save_collaboration(self, agent_id_1: str, agent_id_2: str,
                          success: bool) -> None:
        """Save collaboration record to database."""
        import sqlite3

        conn = sqlite3.connect(self.db_path)

        # Check if exists
        existing = conn.execute(
            "SELECT collaboration_count, success_rate FROM agent_collaborations "
            "WHERE agent_id_1 = ? AND agent_id_2 = ?",
            (min(agent_id_1, agent_id_2), max(agent_id_1, agent_id_2))
        ).fetchone()

        if existing:
            # Update
            count, old_rate = existing
            new_count = count + 1
            # Update success rate
            new_rate = (old_rate * count + (1.0 if success else 0.0)) / new_count

            conn.execute("""
                UPDATE agent_collaborations
                SET collaboration_count = ?, success_rate = ?, last_collaboration = ?
                WHERE agent_id_1 = ? AND agent_id_2 = ?
            """, (new_count, new_rate, time.time(),
                  min(agent_id_1, agent_id_2), max(agent_id_1, agent_id_2)))
        else:
            # Insert
            conn.execute("""
                INSERT INTO agent_collaborations
                (agent_id_1, agent_id_2, collaboration_count, last_collaboration, success_rate)
                VALUES (?, ?, ?, ?, ?)
            """, (min(agent_id_1, agent_id_2), max(agent_id_1, agent_id_2),
                  1, time.time(), 1.0 if success else 0.0))

        conn.commit()
        conn.close()

    def load_from_db(self) -> None:
        """Load agent profiles and history from database."""
        import sqlite3

        conn = sqlite3.connect(self.db_path)

        # Load profiles
        profiles = conn.execute("SELECT * FROM agent_profiles").fetchall()

        for row in profiles:
            (agent_id, agent_role, primary_domains_json, secondary_domains_json,
             preferred_methods_json, expertise_by_domain_json, performance_by_method_json,
             total_tasks, successful_tasks, overall_success_rate, last_updated) = row

            profile = SpecializationProfile(
                agent_id=agent_id,
                agent_role=AgentRole(agent_role),
                primary_domains=json.loads(primary_domains_json),
                secondary_domains=json.loads(secondary_domains_json),
                preferred_methods=json.loads(preferred_methods_json),
                expertise_by_domain=json.loads(expertise_by_domain_json),
                performance_by_method=json.loads(performance_by_method_json),
                total_tasks=total_tasks,
                successful_tasks=successful_tasks,
                overall_success_rate=overall_success_rate
            )

            self.agent_profiles[agent_id] = profile

        # Load task history (recent 1000)
        tasks = conn.execute("""
            SELECT * FROM task_performance
            ORDER BY timestamp DESC
            LIMIT 1000
        """).fetchall()

        for row in tasks:
            (task_id, agent_id, agent_role, domain, method, success,
             confidence, time_taken, timestamp, feedback) = row

            perf = TaskPerformance(
                task_id=task_id,
                agent_id=agent_id,
                agent_role=AgentRole(agent_role),
                domain=domain,
                method=method,
                success=bool(success),
                confidence=confidence,
                time_taken=time_taken,
                timestamp=timestamp,
                feedback=feedback
            )

            self.task_history.append(perf)

        conn.close()

    def get_system_summary(self) -> Dict[str, Any]:
        """Get summary of expertise tracking system."""
        total_agents = len(self.agent_profiles)
        total_tasks = sum(p.total_tasks for p in self.agent_profiles.values())

        # Calculate system-wide success rate
        if total_tasks > 0:
            successful_tasks = sum(p.successful_tasks for p in self.agent_profiles.values())
            system_success_rate = successful_tasks / total_tasks
        else:
            system_success_rate = 0.0

        # Count by role
        role_counts = {}
        for profile in self.agent_profiles.values():
            role = profile.agent_role.value
            role_counts[role] = role_counts.get(role, 0) + 1

        return {
            "total_agents": total_agents,
            "total_tasks_recorded": total_tasks,
            "system_success_rate": system_success_rate,
            "agents_by_role": role_counts,
            "total_collaborations": sum(self.collaboration_matrix.values()),
            "tracking_db_path": self.db_path
        }


# Utility functions
def create_expertise_tracker(db_path: str = "astra_agent_expertise.db") -> ExpertiseTracker:
    """Create expertise tracker with database."""
    tracker = ExpertiseTracker(db_path)
    return tracker


def compare_agent_performance(agent_id_1: str, agent_id_2: str,
                             tracker: ExpertiseTracker) -> Optional[Dict[str, Any]]:
    """Compare performance between two agents."""
    profile_1 = tracker.get_agent_profile(agent_id_1)
    profile_2 = tracker.get_agent_profile(agent_id_2)

    if not profile_1 or not profile_2:
        return None

    # Compare domains
    common_domains = set(profile_1.expertise_by_domain.keys()) & \
                      set(profile_2.expertise_by_domain.keys())

    domain_comparison = {}
    for domain in common_domains:
        expertise_1 = profile_1.expertise_by_domain[domain]
        expertise_2 = profile_2.expertise_by_domain[domain]
        domain_comparison[domain] = {
            agent_id_1: expertise_1,
            agent_id_2: expertise_2,
            "better": agent_id_1 if expertise_1 > expertise_2 else agent_id_2
        }

    return {
        "agents": [agent_id_1, agent_id_2],
        "roles": [profile_1.agent_role.value, profile_2.agent_role.value],
        "overall_success_rates": {
            agent_id_1: profile_1.overall_success_rate,
            agent_id_2: profile_2.overall_success_rate
        },
        "domain_comparison": domain_comparison,
        "total_tasks": {
            agent_id_1: profile_1.total_tasks,
            agent_id_2: profile_2.total_tasks
        }
    }
