"""
FocusFlow Session Manager
=========================
Manages focus session logging, daily goals, study streaks, and achievement
milestones with JSON persistence.

Files:
    data/sessions.json     — lists all recorded focus sessions
    data/daily_goals.json  — lists daily checklist goals
"""

import json
import logging
import os
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("focusflow.session_manager")

class SessionManager:
    """Manages focus session history, goals, streaks, and gamification metrics."""

    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.sessions_path = self.base_dir / "data" / "sessions.json"
        self.goals_path = self.base_dir / "data" / "daily_goals.json"
        
        # Ensure directories exist
        self.sessions_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.sessions: List[Dict[str, Any]] = []
        self.goals: List[Dict[str, Any]] = []
        
        self._load_sessions()
        self._load_goals()

    def _load_sessions(self) -> None:
        if self.sessions_path.exists():
            try:
                with open(self.sessions_path, "r", encoding="utf-8") as f:
                    self.sessions = json.load(f)
                logger.info(f"Loaded {len(self.sessions)} focus sessions.")
            except Exception as e:
                logger.error(f"Error loading sessions: {e}")
                self.sessions = []
        else:
            self.sessions = []
            self._save_sessions()

    def _save_sessions(self) -> None:
        try:
            with open(self.sessions_path, "w", encoding="utf-8") as f:
                json.dump(self.sessions, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving sessions: {e}")

    def _load_goals(self) -> None:
        if self.goals_path.exists():
            try:
                with open(self.goals_path, "r", encoding="utf-8") as f:
                    self.goals = json.load(f)
                logger.info(f"Loaded {len(self.goals)} daily goals.")
            except Exception as e:
                logger.error(f"Error loading goals: {e}")
                self.goals = []
        else:
            self.goals = []
            self._save_goals()

    def _save_goals(self) -> None:
        try:
            with open(self.goals_path, "w", encoding="utf-8") as f:
                json.dump(self.goals, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving goals: {e}")

    def add_session(self, 
                    goal: str, 
                    subject: str, 
                    duration_mins: int, 
                    target_duration_mins: int, 
                    mode: str, 
                    status: str, 
                    is_interrupted: bool = False) -> Dict[str, Any]:
        """Log a new study session and calculate its Focus Score."""
        
        # Calculate Focus Score
        # Formula: (Actual Duration / Target Duration) * ModeWeight * 100
        # Weights: completed: 1.0, partially_completed: 0.6, not_completed: 0.2, interrupted: 0.0
        # If interrupted, subtract 30.
        duration_ratio = min(1.0, duration_mins / max(1, target_duration_mins))
        
        status_weights = {
            "completed": 1.0,
            "partially_completed": 0.6,
            "not_completed": 0.2,
            "interrupted": 0.0
        }
        weight = status_weights.get(status, 0.5)
        
        score = int(duration_ratio * weight * 100)
        if is_interrupted or status == "interrupted":
            score = max(0, score - 30)
            
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        new_session = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "timestamp": timestamp,
            "goal": goal,
            "subject": subject or "General Study",
            "duration_mins": duration_mins,
            "target_duration_mins": target_duration_mins,
            "mode": mode,
            "status": status,
            "focus_score": score,
            "is_interrupted": is_interrupted
        }
        
        self.sessions.append(new_session)
        self._save_sessions()
        
        # Unlocked achievements check
        unlocked = self.check_achievements()
        new_session["unlocked_achievements"] = unlocked
        
        logger.info(f"Log session added: {new_session['id']} with score {score}")
        return new_session

    def get_stats(self) -> Dict[str, Any]:
        """Compile and return statistics for the dashboard."""
        total_sessions = len(self.sessions)
        if total_sessions == 0:
            return {
                "total_hours": 0.0,
                "streak": 0,
                "avg_focus_score": 0,
                "sessions_count": 0,
                "weekly_data": [0] * 7,
                "subject_distribution": {},
                "hourly_productivity": [0] * 24,
                "achievements": self.get_achievements_list(),
                "recent_sessions": []
            }
            
        total_mins = sum(s["duration_mins"] for s in self.sessions)
        total_hours = round(total_mins / 60.0, 1)
        
        # Average Focus Score
        avg_score = int(sum(s["focus_score"] for s in self.sessions) / total_sessions)
        
        # Streak calculation
        streak = self._calculate_streak()
        
        # Weekly Graph data (Last 7 days, ending today)
        weekly_data = self._calculate_weekly_data()
        
        # Subject-wise study time
        subj_dist: Dict[str, int] = {}
        for s in self.sessions:
            subj = s.get("subject", "General Study") or "General Study"
            subj_dist[subj] = subj_dist.get(subj, 0) + s["duration_mins"]
            
        # Convert subject distribution to minutes (sorted)
        sorted_subjects = dict(sorted(subj_dist.items(), key=lambda item: item[1], reverse=True))
        
        # Hourly productivity
        hourly_prod = [0] * 24
        for s in self.sessions:
            try:
                dt = datetime.strptime(s["timestamp"], "%Y-%m-%d %H:%M:%S")
                hourly_prod[dt.hour] += s["duration_mins"]
            except Exception:
                pass
                
        # Recent sessions
        recent = sorted(self.sessions, key=lambda s: s["timestamp"], reverse=True)[:5]
        
        return {
            "total_hours": total_hours,
            "streak": streak,
            "avg_focus_score": avg_score,
            "sessions_count": total_sessions,
            "weekly_data": weekly_data,
            "subject_distribution": sorted_subjects,
            "hourly_productivity": hourly_prod,
            "achievements": self.get_achievements_list(),
            "recent_sessions": recent
        }

    def _calculate_streak(self) -> int:
        """Calculate active consecutive study days streak."""
        study_dates = set()
        for s in self.sessions:
            if s["status"] in ("completed", "partially_completed") and s["duration_mins"] > 0:
                try:
                    dt = datetime.strptime(s["timestamp"], "%Y-%m-%d %H:%M:%S").date()
                    study_dates.add(dt)
                except Exception:
                    pass
                    
        if not study_dates:
            return 0
            
        sorted_dates = sorted(list(study_dates), reverse=True)
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # If the user hasn't studied today or yesterday, streak is broken (0)
        if sorted_dates[0] not in (today, yesterday):
            return 0
            
        streak = 1
        current_date = sorted_dates[0]
        
        for next_date in sorted_dates[1:]:
            if current_date - next_date == timedelta(days=1):
                streak += 1
                current_date = next_date
            elif current_date - next_date == timedelta(days=0):
                # Same day, skip
                continue
            else:
                # Gap found, streak ends
                break
                
        return streak

    def _calculate_weekly_data(self) -> List[float]:
        """Returns study hours for the last 7 days (including today)."""
        today = date.today()
        day_sums = {today - timedelta(days=i): 0.0 for i in range(7)}
        
        for s in self.sessions:
            try:
                dt = datetime.strptime(s["timestamp"], "%Y-%m-%d %H:%M:%S").date()
                if dt in day_sums:
                    day_sums[dt] += s["duration_mins"] / 60.0
            except Exception:
                pass
                
        # Return in chronological order (oldest first, ending with today)
        return [round(day_sums[today - timedelta(days=i)], 1) for i in reversed(range(7))]

    def get_achievements_list(self) -> List[Dict[str, Any]]:
        """List all achievements and their unlock status."""
        achievements_defs = [
            {
                "id": "first_step",
                "title": "First Step",
                "description": "Complete your first focus session",
                "icon": "Zap"
            },
            {
                "id": "deep_diver",
                "title": "Deep Diver",
                "description": "Complete a 60+ minute session in Strict or Very Strict mode",
                "icon": "Shield"
            },
            {
                "id": "unstoppable",
                "title": "Unstoppable",
                "description": "Reach a 3-day focus streak",
                "icon": "Flame"
            },
            {
                "id": "academic_weapon",
                "title": "Academic Weapon",
                "description": "Study for 10+ hours in total",
                "icon": "BookOpen"
            },
            {
                "id": "early_bird",
                "title": "Early Bird",
                "description": "Complete a session starting before 8:00 AM",
                "icon": "Clock"
            },
            {
                "id": "night_owl",
                "title": "Night Owl",
                "description": "Complete a session starting after 10:00 PM",
                "icon": "Moon"
            }
        ]
        
        unlocked_ids = self.check_achievements()
        
        for a in achievements_defs:
            a["unlocked"] = a["id"] in unlocked_ids
            
        return achievements_defs

    def check_achievements(self) -> List[str]:
        """Check all sessions and return unlocked achievement IDs."""
        unlocked = []
        
        # 1. First Step
        has_completed_session = any(s["status"] in ("completed", "partially_completed") for s in self.sessions)
        if has_completed_session:
            unlocked.append("first_step")
            
        # 2. Deep Diver
        has_deep_dive = any(
            s["status"] == "completed" and 
            s["mode"] in ("strict", "very_strict") and 
            s["duration_mins"] >= 60 
            for s in self.sessions
        )
        if has_deep_dive:
            unlocked.append("deep_diver")
            
        # 3. Unstoppable
        streak = self._calculate_streak()
        if streak >= 3:
            unlocked.append("unstoppable")
            
        # 4. Academic Weapon
        total_mins = sum(s["duration_mins"] for s in self.sessions)
        if total_mins >= 600: # 10 hours
            unlocked.append("academic_weapon")
            
        # 5. Early Bird & Night Owl
        for s in self.sessions:
            if s["status"] in ("completed", "partially_completed"):
                try:
                    dt = datetime.strptime(s["timestamp"], "%Y-%m-%d %H:%M:%S")
                    if dt.hour < 8:
                        unlocked.append("early_bird")
                    if dt.hour >= 22:
                        unlocked.append("night_owl")
                except Exception:
                    pass
                    
        return list(set(unlocked))

    # --- Daily Goals checklist ---
    def get_daily_goals(self) -> List[Dict[str, Any]]:
        today_str = date.today().strftime("%Y-%m-%d")
        today_goals = [g for g in self.goals if g.get("date") == today_str]
        return today_goals

    def add_daily_goal(self, text: str) -> Dict[str, Any]:
        today_str = date.today().strftime("%Y-%m-%d")
        new_goal = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "text": text,
            "completed": False,
            "date": today_str
        }
        self.goals.append(new_goal)
        self._save_goals()
        return new_goal

    def toggle_daily_goal(self, goal_id: str) -> bool:
        for g in self.goals:
            if g["id"] == goal_id:
                g["completed"] = not g["completed"]
                self._save_goals()
                return True
        return False

    def delete_daily_goal(self, goal_id: str) -> bool:
        for i, g in enumerate(self.goals):
            if g["id"] == goal_id:
                self.goals.pop(i)
                self._save_goals()
                return True
        return False
