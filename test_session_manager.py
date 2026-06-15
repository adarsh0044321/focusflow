"""
FocusFlow SessionManager Tests
==============================
Verifies the calculations and logging behavior of the SessionManager database module.
"""

import os
import shutil
import tempfile
import unittest
from datetime import datetime, date, timedelta
from pathlib import Path

from session_manager import SessionManager

class TestSessionManager(unittest.TestCase):

    def setUp(self) -> None:
        # Create a temporary directory for test files
        self.test_dir = Path(tempfile.mkdtemp())
        self.session_mgr = SessionManager(self.test_dir)

    def tearDown(self) -> None:
        # Remove the temporary directory after test
        shutil.rmtree(self.test_dir)

    def test_goals_checklist(self) -> None:
        # 1. Add Goals
        goal1 = self.session_mgr.add_daily_goal("Revise Physics Formula")
        goal2 = self.session_mgr.add_daily_goal("Solve 10 Maths Integrals")
        
        self.assertEqual(len(self.session_mgr.get_daily_goals()), 2)
        self.assertEqual(goal1["text"], "Revise Physics Formula")
        self.assertFalse(goal1["completed"])

        # 2. Toggle Goals
        success = self.session_mgr.toggle_daily_goal(goal1["id"])
        self.assertTrue(success)
        goals = self.session_mgr.get_daily_goals()
        # Find goal1
        g1 = next(g for g in goals if g["id"] == goal1["id"])
        self.assertTrue(g1["completed"])

        # 3. Delete Goals
        success_del = self.session_mgr.delete_daily_goal(goal2["id"])
        self.assertTrue(success_del)
        self.assertEqual(len(self.session_mgr.get_daily_goals()), 1)

    def test_focus_score_formula(self) -> None:
        # Test full completion
        session1 = self.session_mgr.add_session(
            goal="Completed Goal",
            subject="Maths",
            duration_mins=60,
            target_duration_mins=60,
            mode="strict",
            status="completed"
        )
        self.assertEqual(session1["focus_score"], 100)

        # Test partial completion (duration matched, status partial = 0.6)
        session2 = self.session_mgr.add_session(
            goal="Partial Goal",
            subject="Physics",
            duration_mins=30,
            target_duration_mins=30,
            mode="moderate",
            status="partially_completed"
        )
        self.assertEqual(session2["focus_score"], 60)

        # Test interrupted session (score - 30)
        session3 = self.session_mgr.add_session(
            goal="Interrupted Goal",
            subject="Chemistry",
            duration_mins=10,
            target_duration_mins=60,
            mode="very_strict",
            status="interrupted",
            is_interrupted=True
        )
        # Ratio = 10/60 = 0.16. Status weight = 0.0.
        # Ratio * Weight = 0. Interrupted penalty: max(0, 0 - 30) = 0.
        self.assertEqual(session3["focus_score"], 0)

        # Test half duration completed
        session4 = self.session_mgr.add_session(
            goal="Half Completed Goal",
            subject="Physics",
            duration_mins=30,
            target_duration_mins=60,
            mode="strict",
            status="completed"
        )
        # Ratio = 0.5. Status weight = 1.0. Score = 0.5 * 1.0 * 100 = 50.
        self.assertEqual(session4["focus_score"], 50)

    def test_streaks_calculation(self) -> None:
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)

        # Mock sessions chronologically
        s1 = {
            "id": "1",
            "timestamp": two_days_ago.strftime("%Y-%m-%d 10:00:00"),
            "goal": "Revise organic chemistry",
            "subject": "Chemistry",
            "duration_mins": 30,
            "target_duration_mins": 30,
            "mode": "light",
            "status": "completed",
            "focus_score": 90,
            "is_interrupted": False
        }
        s2 = {
            "id": "2",
            "timestamp": yesterday.strftime("%Y-%m-%d 15:00:00"),
            "goal": "Read mechanics",
            "subject": "Physics",
            "duration_mins": 45,
            "target_duration_mins": 45,
            "mode": "strict",
            "status": "completed",
            "focus_score": 95,
            "is_interrupted": False
        }
        
        self.session_mgr.sessions = [s1, s2]
        self.assertEqual(self.session_mgr._calculate_streak(), 2)

        # Add study session today
        s3 = {
            "id": "3",
            "timestamp": today.strftime("%Y-%m-%d 09:00:00"),
            "goal": "Revise maths",
            "subject": "Maths",
            "duration_mins": 10,
            "target_duration_mins": 10,
            "mode": "moderate",
            "status": "partially_completed",
            "focus_score": 50,
            "is_interrupted": False
        }
        self.session_mgr.sessions.append(s3)
        self.assertEqual(self.session_mgr._calculate_streak(), 3)

    def test_achievements_unlocks(self) -> None:
        # First session unlocks "first_step"
        self.session_mgr.add_session(
            goal="Intro Session",
            subject="Physics",
            duration_mins=20,
            target_duration_mins=20,
            mode="light",
            status="completed"
        )
        achievements = self.session_mgr.check_achievements()
        self.assertIn("first_step", achievements)

        # 60+ min Strict mode unlocks "deep_diver"
        self.session_mgr.add_session(
            goal="Deep Study Block",
            subject="Maths",
            duration_mins=60,
            target_duration_mins=60,
            mode="strict",
            status="completed"
        )
        achievements = self.session_mgr.check_achievements()
        self.assertIn("deep_diver", achievements)

if __name__ == "__main__":
    unittest.main()
