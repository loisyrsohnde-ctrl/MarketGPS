"""
Test suite for Gamification Service
Tests all gamification features: points, levels, badges, streaks, objectives
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from services.gamification_service import GamificationService
from models.gamification import UserProgress, Badge, Objective
from config.gamification_config import LEVELS, BADGES


class TestGamificationService:
    """Test suite for GamificationService"""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database"""
        db = MagicMock()
        db._get_connection = MagicMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create a gamification service with mock DB"""
        service = GamificationService(mock_db)
        return service

    # ─────────────────────────────────────────────────────────────────────
    # INITIALIZATION TESTS
    # ─────────────────────────────────────────────────────────────────────

    def test_initialize_user_creates_progress(self, service, mock_db):
        """Test that initializing user creates a UserProgress record"""
        # Mock the connection
        conn_mock = MagicMock()
        mock_db._get_connection.return_value.__enter__ = MagicMock(return_value=conn_mock)
        mock_db._get_connection.return_value.__exit__ = MagicMock(return_value=False)

        # Mock get_user_progress to return None first time
        with patch.object(service, 'get_user_progress', return_value=None):
            with patch.object(service, 'generate_weekly_objectives'):
                result = service.initialize_user("test_user")

        assert result is not None
        conn_mock.execute.assert_called()

    def test_initialize_user_idempotent(self, service):
        """Test that initializing an existing user doesn't reset progress"""
        existing_progress = UserProgress(
            user_id="test_user",
            total_points=500,
            current_level=5
        )

        with patch.object(service, 'get_user_progress', return_value=existing_progress):
            result = service.initialize_user("test_user")

        # Should return existing progress without changes
        assert result.total_points == 500
        assert result.current_level == 5

    # ─────────────────────────────────────────────────────────────────────
    # PROGRESS TRACKING TESTS
    # ─────────────────────────────────────────────────────────────────────

    def test_get_user_progress_retrieves_data(self, service, mock_db):
        """Test retrieving user progress from database"""
        conn_mock = MagicMock()
        cursor_mock = MagicMock()

        # Mock database responses
        cursor_mock.fetchone.side_effect = [
            ("test_user", 500, 5, 10, 15, "2025-01-01T00:00:00", "2025-01-01T00:00:00"),  # Progress row
            None  # Badges query returns empty
        ]
        cursor_mock.fetchall.return_value = [("badge1",), ("badge2",)]

        conn_mock.execute.return_value = cursor_mock
        mock_db._get_connection.return_value.__enter__ = MagicMock(return_value=conn_mock)
        mock_db._get_connection.return_value.__exit__ = MagicMock(return_value=False)

        result = service.get_user_progress("test_user")

        assert result is not None
        assert result.user_id == "test_user"
        assert result.total_points == 500
        assert result.current_level == 5

    # ─────────────────────────────────────────────────────────────────────
    # POINTS & LEVELS TESTS
    # ─────────────────────────────────────────────────────────────────────

    def test_award_points_increases_total(self, service):
        """Test that awarding points increases user's total"""
        progress = UserProgress(user_id="test_user", total_points=100, current_level=1)

        with patch.object(service, 'get_user_progress', return_value=progress):
            with patch.object(service, '_get_today_points', return_value=0):
                with patch.object(service, 'record_action'):
                    with patch.object(service, 'check_badges', return_value=[]):
                        with patch.object(service, '_get_streak_bonus', return_value=1.0):
                            with patch.object(service, '_calculate_level', return_value=1):
                                with patch.object(service.db, '_get_connection'):
                                    result = service.award_points("test_user", 50, "test")

        assert result["points_awarded"] == 50
        assert result["new_total"] == 150
        assert result["level_up"] is False

    def test_award_points_triggers_level_up(self, service):
        """Test that reaching next level triggers level_up flag"""
        progress = UserProgress(user_id="test_user", total_points=90, current_level=1)

        with patch.object(service, 'get_user_progress', return_value=progress):
            with patch.object(service, '_get_today_points', return_value=0):
                with patch.object(service, 'record_action'):
                    with patch.object(service, 'check_badges', return_value=[]):
                        with patch.object(service, '_get_streak_bonus', return_value=1.0):
                            with patch.object(service, '_calculate_level', side_effect=[1, 2]):
                                with patch.object(service.db, '_get_connection'):
                                    result = service.award_points("test_user", 20, "test")

        assert result["level_up"] is True
        assert result["new_level"] == 2

    def test_calculate_level_returns_correct_level(self, service):
        """Test level calculation based on points"""
        assert service._calculate_level(0) == 1
        assert service._calculate_level(99) == 1
        assert service._calculate_level(100) == 2
        assert service._calculate_level(300) == 3
        assert service._calculate_level(1000) == 5
        assert service._calculate_level(10000) == 10

    def test_streak_bonus_applies_correctly(self, service):
        """Test that streak bonus multipliers are applied"""
        assert service._get_streak_bonus(0) == 1.0
        assert service._get_streak_bonus(3) == 1.1
        assert service._get_streak_bonus(7) == 1.25
        assert service._get_streak_bonus(14) == 1.5
        assert service._get_streak_bonus(30) == 2.0

    # ─────────────────────────────────────────────────────────────────────
    # STREAK TESTS
    # ─────────────────────────────────────────────────────────────────────

    def test_update_streak_increments_on_consecutive_days(self, service):
        """Test streak increments when user acts on consecutive days"""
        yesterday = datetime.utcnow() - timedelta(days=1)
        progress = UserProgress(
            user_id="test_user",
            current_streak=5,
            longest_streak=5,
            last_activity_date=yesterday.isoformat()
        )

        with patch.object(service, 'get_user_progress', return_value=progress):
            with patch.object(service.db, '_get_connection'):
                streak = service.update_streak("test_user")

        assert streak == 6

    def test_update_streak_resets_on_missed_day(self, service):
        """Test streak resets when user misses a day"""
        two_days_ago = datetime.utcnow() - timedelta(days=2)
        progress = UserProgress(
            user_id="test_user",
            current_streak=10,
            longest_streak=10,
            last_activity_date=two_days_ago.isoformat()
        )

        with patch.object(service, 'get_user_progress', return_value=progress):
            with patch.object(service.db, '_get_connection'):
                streak = service.update_streak("test_user")

        assert streak == 1

    def test_update_streak_starts_at_one(self, service):
        """Test streak starts at 1 for first action"""
        progress = UserProgress(
            user_id="test_user",
            current_streak=0,
            longest_streak=0,
            last_activity_date=None
        )

        with patch.object(service, 'get_user_progress', return_value=progress):
            with patch.object(service.db, '_get_connection'):
                streak = service.update_streak("test_user")

        assert streak == 1

    # ─────────────────────────────────────────────────────────────────────
    # BADGE TESTS
    # ─────────────────────────────────────────────────────────────────────

    def test_check_badge_condition_login(self, service):
        """Test checking login badge condition"""
        progress = UserProgress(user_id="test_user")
        badge_config = {
            "condition": {"action": "login", "count": 1}
        }

        with patch.object(service, '_get_action_count', return_value=1):
            result = service._check_badge_condition("test_user", badge_config, progress)

        assert result is True

    def test_check_badge_condition_streak(self, service):
        """Test checking streak badge condition"""
        progress = UserProgress(user_id="test_user", current_streak=7)
        badge_config = {
            "condition": {"action": "streak", "count": 7}
        }

        result = service._check_badge_condition("test_user", badge_config, progress)

        assert result is True

    def test_check_badge_condition_level(self, service):
        """Test checking level badge condition"""
        progress = UserProgress(user_id="test_user", current_level=5)
        badge_config = {
            "condition": {"action": "level_up", "target_level": 5}
        }

        result = service._check_badge_condition("test_user", badge_config, progress)

        assert result is True

    def test_get_badges_separates_earned_and_available(self, service):
        """Test that get_badges correctly separates earned and available badges"""
        progress = UserProgress(
            user_id="test_user",
            badges_earned=["first_login"]
        )

        with patch.object(service, 'get_user_progress', return_value=progress):
            with patch.object(service.db, '_get_connection'):
                with patch.object(service, '_get_badge_progress', return_value={"current": 0, "target": 10}):
                    result = service.get_badges("test_user")

        assert "earned" in result
        assert "available" in result
        assert len(result["earned"]) > 0
        assert len(result["available"]) > 0

    # ─────────────────────────────────────────────────────────────────────
    # OBJECTIVE TESTS
    # ─────────────────────────────────────────────────────────────────────

    def test_generate_weekly_objectives_creates_objectives(self, service):
        """Test that generating weekly objectives creates them"""
        with patch.object(service.db, '_get_connection'):
            objectives = service.generate_weekly_objectives("test_user", 5)

        assert len(objectives) > 0
        assert all(obj.objective_type == "weekly" for obj in objectives)
        assert all(obj.user_id == "test_user" for obj in objectives)

    def test_generate_daily_objectives_creates_daily(self, service):
        """Test that generating daily objectives creates them"""
        with patch.object(service.db, '_get_connection'):
            objectives = service.generate_daily_objectives("test_user", 3)

        assert len(objectives) > 0
        assert all(obj.objective_type == "daily" for obj in objectives)

    def test_update_objective_progress_increments_current(self, service):
        """Test that objective progress is incremented"""
        conn_mock = MagicMock()
        cursor_mock = MagicMock()
        cursor_mock.fetchall.return_value = [
            ("obj1", 2, 5, 20, "weekly")  # id, current, target, points, type
        ]
        conn_mock.execute.return_value = cursor_mock

        service.db._get_connection.return_value.__enter__ = MagicMock(return_value=conn_mock)
        service.db._get_connection.return_value.__exit__ = MagicMock(return_value=False)

        with patch.object(service, 'award_points'):
            service.update_objective_progress("test_user", "analyze")

        # Should have updated the objective
        assert conn_mock.execute.called

    def test_get_objectives_returns_active(self, service):
        """Test getting active objectives"""
        conn_mock = MagicMock()
        cursor_mock = MagicMock()
        cursor_mock.fetchall.return_value = [
            ("obj1", "Title", "Desc", "action", 5, 2, 20, "weekly", "2025-12-31T23:59:59")
        ]
        conn_mock.execute.return_value = cursor_mock

        service.db._get_connection.return_value.__enter__ = MagicMock(return_value=conn_mock)
        service.db._get_connection.return_value.__exit__ = MagicMock(return_value=False)

        objectives = service.get_objectives("test_user", "weekly")

        assert len(objectives) > 0
        assert objectives[0]["title"] == "Title"

    # ─────────────────────────────────────────────────────────────────────
    # LEADERBOARD TESTS
    # ─────────────────────────────────────────────────────────────────────

    def test_get_leaderboard_returns_ranked_users(self, service):
        """Test that leaderboard returns users sorted by points"""
        conn_mock = MagicMock()
        cursor_mock = MagicMock()
        cursor_mock.fetchall.side_effect = [
            [("user1", 500), ("user2", 300)],  # First query
            None  # For get_user_progress
        ]

        service.db._get_connection.return_value.__enter__ = MagicMock(return_value=conn_mock)
        service.db._get_connection.return_value.__exit__ = MagicMock(return_value=False)

        with patch.object(service, 'get_user_progress') as mock_progress:
            mock_progress.return_value = UserProgress(user_id="user1", total_points=500, current_level=5)
            leaderboard = service.get_leaderboard("weekly", 10)

        # Should have at least processed the data
        assert service.db._get_connection.called

    def test_get_user_rank_finds_position(self, service):
        """Test getting user's rank in leaderboard"""
        mock_leaderboard = [
            {"rank": 1, "user_id": "user1", "total_points": 500},
            {"rank": 2, "user_id": "test_user", "total_points": 400},
            {"rank": 3, "user_id": "user3", "total_points": 300},
        ]

        with patch.object(service, 'get_leaderboard', return_value=mock_leaderboard):
            rank_info = service.get_user_rank("test_user", "weekly")

        assert rank_info["rank"] == 2
        assert rank_info["points"] == 400

    # ─────────────────────────────────────────────────────────────────────
    # STATISTICS TESTS
    # ─────────────────────────────────────────────────────────────────────

    def test_get_gamification_stats_returns_complete_stats(self, service):
        """Test that gamification stats include all expected fields"""
        progress = UserProgress(
            user_id="test_user",
            total_points=500,
            current_level=5,
            current_streak=7,
            longest_streak=10,
            created_at=datetime.utcnow().isoformat(),
            badges_earned=["badge1", "badge2"]
        )

        conn_mock = MagicMock()
        cursor_mock = MagicMock()
        cursor_mock.fetchone.side_effect = [
            (300,),  # points_7d
            (400,),  # points_30d
            (10,),   # completed_objectives
        ]
        conn_mock.execute.return_value = cursor_mock

        service.db._get_connection.return_value.__enter__ = MagicMock(return_value=conn_mock)
        service.db._get_connection.return_value.__exit__ = MagicMock(return_value=False)

        with patch.object(service, 'get_user_progress', return_value=progress):
            with patch.object(service, 'get_user_rank', return_value={"rank": 5, "percentile": 95.0}):
                stats = service.get_gamification_stats("test_user")

        assert stats["total_points"] == 500
        assert stats["current_level"] == 5
        assert stats["current_streak"] == 7
        assert stats["badges_earned"] == 2
        assert "rank" in stats
        assert "avg_daily_points" in stats


class TestGamificationIntegration:
    """Integration tests for gamification system"""

    def test_full_engagement_cycle(self):
        """Test a complete user engagement cycle"""
        # This would be an integration test with real DB
        # Verify: action -> points -> level -> badges -> objectives
        pass

    def test_streak_maintenance(self):
        """Test maintaining a streak across multiple days"""
        # Simulate user actions across multiple days
        # Verify streak increments correctly
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
