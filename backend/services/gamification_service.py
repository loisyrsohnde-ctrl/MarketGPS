"""
MarketGPS - Gamification Service
Manages points, levels, badges, streaks, and objectives for user engagement.
"""

import uuid
import json
import random
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple, Any
from core.config import get_logger
from storage.sqlite_store import SQLiteStore
from models.gamification import (
    Badge, UserLevel, UserProgress, Objective, UserAction, GamificationStats,
    BadgeCategory, ObjectiveType, GamificationConfig
)
from config.gamification_config import (
    LEVELS, BADGES, WEEKLY_OBJECTIVES_POOL, DAILY_OBJECTIVES_POOL,
    LEADERBOARD_CONFIG, ENGAGEMENT_SETTINGS
)

logger = get_logger(__name__)


class GamificationService:
    """Service for managing all gamification features"""

    def __init__(self, db: Optional[SQLiteStore] = None):
        """Initialize gamification service with database connection"""
        self.db = db or SQLiteStore()
        self.badges_map = {badge["id"]: badge for badge in BADGES}
        self.levels_map = {level["level"]: level for level in LEVELS}

    # ═══════════════════════════════════════════════════════════════════════════
    # INITIALIZATION & SETUP
    # ═══════════════════════════════════════════════════════════════════════════

    def initialize_user(self, user_id: str) -> UserProgress:
        """
        Initialize gamification for a new user.
        Creates initial progress record and generates weekly objectives.
        """
        try:
            # Check if already exists
            existing = self.get_user_progress(user_id)
            if existing and existing.total_points > 0:
                logger.info(f"User {user_id} already initialized for gamification")
                return existing

            # Create initial progress
            progress = UserProgress(user_id=user_id)
            progress_dict = progress.to_dict()

            with self.db._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO user_gamification
                    (user_id, total_points, current_level, current_streak, longest_streak,
                     last_activity_date, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, 0, 1, 0, 0, None,
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat()
                ))
                conn.commit()

            # Generate initial weekly objectives
            self.generate_weekly_objectives(user_id)

            logger.info(f"Initialized gamification for user {user_id}")
            return progress

        except Exception as e:
            logger.error(f"Error initializing user {user_id}: {e}")
            raise

    # ═══════════════════════════════════════════════════════════════════════════
    # PROGRESS TRACKING
    # ═══════════════════════════════════════════════════════════════════════════

    def get_user_progress(self, user_id: str) -> Optional[UserProgress]:
        """Retrieve complete gamification progress for a user"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT user_id, total_points, current_level, current_streak,
                           longest_streak, last_activity_date, created_at, updated_at
                    FROM user_gamification
                    WHERE user_id = ?
                """, (user_id,))
                row = cursor.fetchone()

                if not row:
                    return None

                # Get earned badges
                cursor = conn.execute("""
                    SELECT badge_id FROM user_badges WHERE user_id = ?
                """, (user_id,))
                badge_ids = [row[0] for row in cursor.fetchall()]

                progress = UserProgress(
                    user_id=row[0],
                    total_points=row[1],
                    current_level=row[2],
                    current_streak=row[3],
                    longest_streak=row[4],
                    last_activity_date=row[5],
                    created_at=row[6],
                    updated_at=row[7],
                    badges_earned=badge_ids
                )
                return progress

        except Exception as e:
            logger.error(f"Error getting progress for {user_id}: {e}")
            return None

    # ═══════════════════════════════════════════════════════════════════════════
    # POINTS & LEVELS
    # ═══════════════════════════════════════════════════════════════════════════

    def award_points(self, user_id: str, points: int, reason: str = "") -> Dict[str, Any]:
        """
        Award points to user and handle level ups.

        Returns:
            Dict with:
            - points_awarded: int
            - new_total: int
            - new_level: int
            - level_up: bool
            - rewards: List of new badges earned
        """
        try:
            # Initialize user if needed
            progress = self.get_user_progress(user_id)
            if not progress:
                self.initialize_user(user_id)
                progress = self.get_user_progress(user_id)

            # Apply streak bonus
            streak_multiplier = self._get_streak_bonus(progress.current_streak)
            points_awarded = int(points * streak_multiplier)

            # Apply daily cap
            today_points = self._get_today_points(user_id)
            if today_points + points_awarded > GamificationConfig.MAX_DAILY_POINTS:
                points_awarded = GamificationConfig.MAX_DAILY_POINTS - today_points

            if points_awarded <= 0:
                return {
                    "points_awarded": 0,
                    "new_total": progress.total_points,
                    "new_level": progress.current_level,
                    "level_up": False,
                    "rewards": []
                }

            new_total = progress.total_points + points_awarded
            new_level = self._calculate_level(new_total)
            level_up = new_level > progress.current_level

            with self.db._get_connection() as conn:
                conn.execute("""
                    UPDATE user_gamification
                    SET total_points = ?, current_level = ?, updated_at = ?
                    WHERE user_id = ?
                """, (new_total, new_level, datetime.utcnow().isoformat(), user_id))
                conn.commit()

            # Record action
            self.record_action(user_id, "earn_points", {
                "amount": points_awarded,
                "reason": reason,
                "streak_bonus": streak_multiplier - 1.0
            })

            # Check for new badges
            new_badges = self.check_badges(user_id) if level_up else []

            logger.info(f"Awarded {points_awarded} points to {user_id} (reason: {reason})")

            return {
                "points_awarded": points_awarded,
                "new_total": new_total,
                "new_level": new_level,
                "level_up": level_up,
                "rewards": new_badges
            }

        except Exception as e:
            logger.error(f"Error awarding points to {user_id}: {e}")
            raise

    def record_action(self, user_id: str, action: str, metadata: Dict[str, Any] = None):
        """
        Record a user action for tracking and gamification.
        Triggers badge checks and objective updates.
        """
        try:
            metadata = metadata or {}
            action_id = str(uuid.uuid4())

            # Get points for this action if configured
            points = GamificationConfig.POINTS_PER_ACTION.get(action, 0)

            with self.db._get_connection() as conn:
                conn.execute("""
                    INSERT INTO user_actions (id, user_id, action, metadata_json, points_earned, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    action_id, user_id, action, json.dumps(metadata), points,
                    datetime.utcnow().isoformat()
                ))
                conn.commit()

            # Award points if any
            if points > 0:
                self.award_points(user_id, points, f"Action: {action}")

            # Update streak
            self.update_streak(user_id)

            # Check objectives
            self.update_objective_progress(user_id, action)

            # Check badges
            self.check_badges(user_id)

            logger.debug(f"Recorded action '{action}' for user {user_id}")

        except Exception as e:
            logger.error(f"Error recording action for {user_id}: {e}")

    def _get_today_points(self, user_id: str) -> int:
        """Get total points earned today by user"""
        try:
            today = datetime.utcnow().date().isoformat()
            with self.db._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT COALESCE(SUM(points_earned), 0)
                    FROM user_actions
                    WHERE user_id = ? AND DATE(created_at) = ?
                """, (user_id, today))
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting today's points: {e}")
            return 0

    def _calculate_level(self, total_points: int) -> int:
        """Calculate user level based on total points"""
        for level_config in sorted(LEVELS, key=lambda x: x["min_points"], reverse=True):
            if total_points >= level_config["min_points"]:
                return level_config["level"]
        return 1

    def _get_streak_bonus(self, streak: int) -> float:
        """Get point multiplier based on streak"""
        for required_days in sorted(GamificationConfig.STREAK_BONUS_MULTIPLIER.keys(), reverse=True):
            if streak >= required_days:
                return GamificationConfig.STREAK_BONUS_MULTIPLIER[required_days]
        return 1.0

    # ═══════════════════════════════════════════════════════════════════════════
    # STREAKS
    # ═══════════════════════════════════════════════════════════════════════════

    def update_streak(self, user_id: str) -> int:
        """
        Update user's engagement streak.
        Increments if user acted today, resets if they missed a day.

        Returns:
            Current streak count
        """
        try:
            progress = self.get_user_progress(user_id)
            if not progress:
                self.initialize_user(user_id)
                progress = self.get_user_progress(user_id)

            last_activity = progress.last_activity_date
            today = datetime.utcnow().date()

            if last_activity:
                last_date = datetime.fromisoformat(last_activity).date()
                days_since = (today - last_date).days

                if days_since == 0:
                    # Already actioned today, don't change streak
                    return progress.current_streak

                elif days_since == 1:
                    # Consecutive day, increment streak
                    new_streak = progress.current_streak + 1
                    longest = max(progress.longest_streak, new_streak)
                else:
                    # Streak broken
                    new_streak = 1
                    longest = progress.longest_streak
            else:
                # First action
                new_streak = 1
                longest = 1

            # Update database
            with self.db._get_connection() as conn:
                conn.execute("""
                    UPDATE user_gamification
                    SET current_streak = ?, longest_streak = ?, last_activity_date = ?, updated_at = ?
                    WHERE user_id = ?
                """, (
                    new_streak, longest, datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat(), user_id
                ))
                conn.commit()

            logger.debug(f"Updated streak for {user_id}: {new_streak} days")
            return new_streak

        except Exception as e:
            logger.error(f"Error updating streak for {user_id}: {e}")
            return 0

    # ═══════════════════════════════════════════════════════════════════════════
    # BADGES
    # ═══════════════════════════════════════════════════════════════════════════

    def check_badges(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Check and award any new badges user qualifies for.

        Returns:
            List of newly earned badges
        """
        try:
            progress = self.get_user_progress(user_id)
            if not progress:
                return []

            new_badges = []

            for badge_config in BADGES:
                badge_id = badge_config["id"]

                # Skip if already earned
                if badge_id in progress.badges_earned:
                    continue

                # Check if conditions are met
                if self._check_badge_condition(user_id, badge_config, progress):
                    new_badges.append(badge_config)
                    self._award_badge(user_id, badge_id, badge_config["points_reward"])

            return new_badges

        except Exception as e:
            logger.error(f"Error checking badges for {user_id}: {e}")
            return []

    def _check_badge_condition(self, user_id: str, badge_config: Dict[str, Any],
                               progress: UserProgress) -> bool:
        """Check if user meets badge unlock condition"""
        condition = badge_config["condition"]
        action = condition.get("action")

        try:
            if action == "login":
                # Simple login count
                count = self._get_action_count(user_id, "login")
                return count >= condition.get("count", 1)

            elif action == "view_asset":
                count = self._get_action_count(user_id, "view_asset")
                return count >= condition.get("count", 1)

            elif action == "analyze":
                count = self._get_action_count(user_id, "analyze")
                return count >= condition.get("count", 1)

            elif action == "create_alert":
                count = self._get_action_count(user_id, "create_alert")
                return count >= condition.get("count", 1)

            elif action == "add_watchlist":
                count = self._get_action_count(user_id, "add_watchlist")
                return count >= condition.get("count", 1)

            elif action == "read_news":
                count = self._get_action_count(user_id, "read_news")
                return count >= condition.get("count", 1)

            elif action == "run_backtest":
                count = self._get_action_count(user_id, "run_backtest")
                return count >= condition.get("count", 1)

            elif action == "share_analysis":
                count = self._get_action_count(user_id, "share_analysis")
                return count >= condition.get("count", 1)

            elif action == "streak":
                return progress.current_streak >= condition.get("count", 1)

            elif action == "level_up":
                return progress.current_level >= condition.get("target_level", 1)

            elif action == "subscribe_pro":
                # Check subscription status (would need subscription service)
                return condition.get("count", 1) <= 1  # Simplified

            elif action == "watchlist_sectors":
                sector_count = self._get_watchlist_sector_count(user_id)
                return sector_count >= condition.get("count", 1)

            elif action == "total_points":
                return progress.total_points >= condition.get("count", 1)

            return False

        except Exception as e:
            logger.error(f"Error checking badge condition: {e}")
            return False

    def _award_badge(self, user_id: str, badge_id: str, points: int):
        """Award a badge to user and grant points"""
        try:
            with self.db._get_connection() as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO user_badges (id, user_id, badge_id, earned_at)
                    VALUES (?, ?, ?, ?)
                """, (str(uuid.uuid4()), user_id, badge_id, datetime.utcnow().isoformat()))
                conn.commit()

            # Award points for badge
            if points > 0:
                self.award_points(user_id, points, f"Badge: {badge_id}")

            logger.info(f"Awarded badge '{badge_id}' to user {user_id}")

        except Exception as e:
            logger.error(f"Error awarding badge: {e}")

    def _get_action_count(self, user_id: str, action: str) -> int:
        """Get count of specific action for user"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM user_actions
                    WHERE user_id = ? AND action = ?
                """, (user_id, action))
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting action count: {e}")
            return 0

    def _get_watchlist_sector_count(self, user_id: str) -> int:
        """Get count of different sectors in user's watchlist"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT COUNT(DISTINCT metadata_json)
                    FROM user_actions
                    WHERE user_id = ? AND action = 'add_watchlist'
                """, (user_id,))
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting watchlist sector count: {e}")
            return 0

    def get_badges(self, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all badges with earned status.

        Returns:
            Dict with:
            - earned: List of earned badges with timestamps
            - available: List of available badges with progress
        """
        try:
            progress = self.get_user_progress(user_id)
            if not progress:
                return {"earned": [], "available": []}

            earned_badges = []
            available_badges = []

            with self.db._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT badge_id, earned_at FROM user_badges WHERE user_id = ?
                """, (user_id,))
                earned_ids = {row[0]: row[1] for row in cursor.fetchall()}

            for badge_config in BADGES:
                badge_id = badge_config["id"]
                badge_copy = dict(badge_config)

                if badge_id in earned_ids:
                    badge_copy["earned_at"] = earned_ids[badge_id]
                    earned_badges.append(badge_copy)
                else:
                    # Add progress info
                    progress_info = self._get_badge_progress(user_id, badge_config, progress)
                    badge_copy["progress"] = progress_info
                    available_badges.append(badge_copy)

            return {
                "earned": earned_badges,
                "available": available_badges
            }

        except Exception as e:
            logger.error(f"Error getting badges: {e}")
            return {"earned": [], "available": []}

    def _get_badge_progress(self, user_id: str, badge_config: Dict[str, Any],
                           progress: UserProgress) -> Dict[str, Any]:
        """Get progress towards earning a badge"""
        condition = badge_config["condition"]
        action = condition.get("action")
        target = condition.get("count", 1)

        try:
            if action in ["login", "view_asset", "analyze", "create_alert", "add_watchlist",
                         "read_news", "run_backtest", "share_analysis"]:
                current = self._get_action_count(user_id, action)
                return {"current": current, "target": target, "percentage": int(current / target * 100) if target else 0}

            elif action == "streak":
                current = progress.current_streak
                return {"current": current, "target": target, "percentage": int(current / target * 100) if target else 0}

            elif action == "level_up":
                current = progress.current_level
                target_level = condition.get("target_level", 1)
                return {"current": current, "target": target_level, "percentage": int(current / target_level * 100)}

            elif action == "total_points":
                current = progress.total_points
                return {"current": current, "target": target, "percentage": int(current / target * 100) if target else 0}

            return {"current": 0, "target": target, "percentage": 0}

        except Exception as e:
            logger.error(f"Error getting badge progress: {e}")
            return {"current": 0, "target": target, "percentage": 0}

    # ═══════════════════════════════════════════════════════════════════════════
    # OBJECTIVES
    # ═══════════════════════════════════════════════════════════════════════════

    def generate_weekly_objectives(self, user_id: str, num_objectives: int = 5) -> List[Objective]:
        """Generate weekly objectives for a user"""
        try:
            # Clear old weekly objectives
            with self.db._get_connection() as conn:
                conn.execute("""
                    DELETE FROM user_objectives
                    WHERE user_id = ? AND objective_type = 'weekly' AND completed_at IS NULL
                """, (user_id,))
                conn.commit()

            # Select random objectives from pool
            selected = random.sample(WEEKLY_OBJECTIVES_POOL, min(num_objectives, len(WEEKLY_OBJECTIVES_POOL)))

            objectives = []
            expires_at = datetime.utcnow() + timedelta(days=7)

            for obj_config in selected:
                objective = Objective(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    title=obj_config["title"],
                    description=obj_config.get("description", ""),
                    action=obj_config["action"],
                    target=obj_config["target"],
                    current=0,
                    points_reward=obj_config["points_reward"],
                    objective_type="weekly",
                    expires_at=expires_at.isoformat()
                )

                with self.db._get_connection() as conn:
                    conn.execute("""
                        INSERT INTO user_objectives
                        (id, user_id, objective_type, title, action, target, current, points_reward, expires_at, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        objective.id, objective.user_id, objective.objective_type, objective.title,
                        objective.action, objective.target, objective.current, objective.points_reward,
                        objective.expires_at, objective.created_at
                    ))
                    conn.commit()

                objectives.append(objective)

            logger.info(f"Generated {len(objectives)} weekly objectives for {user_id}")
            return objectives

        except Exception as e:
            logger.error(f"Error generating weekly objectives: {e}")
            return []

    def generate_daily_objectives(self, user_id: str, num_objectives: int = 3) -> List[Objective]:
        """Generate daily objectives for a user"""
        try:
            # Clear old daily objectives
            with self.db._get_connection() as conn:
                conn.execute("""
                    DELETE FROM user_objectives
                    WHERE user_id = ? AND objective_type = 'daily' AND completed_at IS NULL
                """, (user_id,))
                conn.commit()

            # Select random objectives from pool
            selected = random.sample(DAILY_OBJECTIVES_POOL, min(num_objectives, len(DAILY_OBJECTIVES_POOL)))

            objectives = []
            expires_at = datetime.utcnow() + timedelta(days=1)

            for obj_config in selected:
                objective = Objective(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    title=obj_config["title"],
                    description=obj_config.get("description", ""),
                    action=obj_config["action"],
                    target=obj_config["target"],
                    current=0,
                    points_reward=obj_config["points_reward"],
                    objective_type="daily",
                    expires_at=expires_at.isoformat()
                )

                with self.db._get_connection() as conn:
                    conn.execute("""
                        INSERT INTO user_objectives
                        (id, user_id, objective_type, title, action, target, current, points_reward, expires_at, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        objective.id, objective.user_id, objective.objective_type, objective.title,
                        objective.action, objective.target, objective.current, objective.points_reward,
                        objective.expires_at, objective.created_at
                    ))
                    conn.commit()

                objectives.append(objective)

            logger.info(f"Generated {len(objectives)} daily objectives for {user_id}")
            return objectives

        except Exception as e:
            logger.error(f"Error generating daily objectives: {e}")
            return []

    def update_objective_progress(self, user_id: str, action: str):
        """Update progress on objectives based on action"""
        try:
            with self.db._get_connection() as conn:
                # Get active objectives for this action
                cursor = conn.execute("""
                    SELECT id, current, target, points_reward, objective_type
                    FROM user_objectives
                    WHERE user_id = ? AND action = ? AND completed_at IS NULL
                """, (user_id, action))

                objectives = cursor.fetchall()

                for obj_id, current, target, points_reward, obj_type in objectives:
                    new_current = current + 1

                    if new_current >= target:
                        # Objective completed!
                        now = datetime.utcnow().isoformat()
                        conn.execute("""
                            UPDATE user_objectives
                            SET current = ?, completed_at = ?
                            WHERE id = ?
                        """, (new_current, now, obj_id))
                        conn.commit()

                        # Award points
                        self.award_points(user_id, points_reward, f"Objective completed: {obj_id}")
                    else:
                        conn.execute("""
                            UPDATE user_objectives
                            SET current = ?
                            WHERE id = ?
                        """, (new_current, obj_id))
                        conn.commit()

        except Exception as e:
            logger.error(f"Error updating objective progress: {e}")

    def get_objectives(self, user_id: str, objective_type: str = "all") -> List[Dict[str, Any]]:
        """
        Get active objectives for user.

        Args:
            user_id: User ID
            objective_type: "daily", "weekly", "all" (active only)

        Returns:
            List of active objectives with progress
        """
        try:
            with self.db._get_connection() as conn:
                if objective_type == "all":
                    cursor = conn.execute("""
                        SELECT id, title, description, action, target, current, points_reward,
                               objective_type, expires_at
                        FROM user_objectives
                        WHERE user_id = ? AND completed_at IS NULL
                        ORDER BY objective_type, created_at
                    """, (user_id,))
                else:
                    cursor = conn.execute("""
                        SELECT id, title, description, action, target, current, points_reward,
                               objective_type, expires_at
                        FROM user_objectives
                        WHERE user_id = ? AND objective_type = ? AND completed_at IS NULL
                        ORDER BY created_at
                    """, (user_id, objective_type))

                objectives = []
                for row in cursor.fetchall():
                    obj = {
                        "id": row[0],
                        "title": row[1],
                        "description": row[2],
                        "action": row[3],
                        "target": row[4],
                        "current": row[5],
                        "points_reward": row[6],
                        "objective_type": row[7],
                        "expires_at": row[8],
                        "progress_percentage": int(row[5] / row[4] * 100) if row[4] > 0 else 0,
                        "completed": row[5] >= row[4]
                    }
                    objectives.append(obj)

                return objectives

        except Exception as e:
            logger.error(f"Error getting objectives: {e}")
            return []

    # ═══════════════════════════════════════════════════════════════════════════
    # LEADERBOARDS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_leaderboard(self, period: str = "weekly", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get leaderboard for specified period.

        Args:
            period: "weekly", "monthly", "all-time"
            limit: Number of top users to return

        Returns:
            List of leaderboard entries with rank, user_id, points, level, streak
        """
        try:
            config = LEADERBOARD_CONFIG.get(period.upper(), LEADERBOARD_CONFIG["WEEKLY"])
            limit = min(limit, config["top_users"])

            cutoff_date = None
            if config["period_days"]:
                cutoff_date = datetime.utcnow() - timedelta(days=config["period_days"])

            with self.db._get_connection() as conn:
                # Build query based on period
                if cutoff_date:
                    date_str = cutoff_date.isoformat()
                    cursor = conn.execute(f"""
                        SELECT user_id, SUM(points_earned) as total_points
                        FROM user_actions
                        WHERE created_at >= ?
                        GROUP BY user_id
                        HAVING COUNT(*) >= ?
                        ORDER BY total_points DESC
                        LIMIT ?
                    """, (date_str, config["min_actions"], limit))
                else:
                    cursor = conn.execute(f"""
                        SELECT user_id, SUM(COALESCE(points_earned, 0)) as total_points
                        FROM user_actions
                        GROUP BY user_id
                        HAVING COUNT(*) >= ?
                        ORDER BY total_points DESC
                        LIMIT ?
                    """, (config["min_actions"], limit))

                leaderboard = []
                for rank, (user_id, total_points) in enumerate(cursor.fetchall(), 1):
                    # Get additional user stats
                    progress = self.get_user_progress(user_id)
                    if progress:
                        entry = {
                            "rank": rank,
                            "user_id": user_id,
                            "total_points": total_points or 0,
                            "current_level": progress.current_level,
                            "current_streak": progress.current_streak,
                            "badges_count": len(progress.badges_earned),
                            "level_name": self.levels_map.get(progress.current_level, {}).get("name", "Unknown")
                        }
                        leaderboard.append(entry)

                return leaderboard

        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            return []

    def get_user_rank(self, user_id: str, period: str = "weekly") -> Dict[str, Any]:
        """Get user's rank and percentile in leaderboard"""
        try:
            leaderboard = self.get_leaderboard(period, limit=10000)

            for entry in leaderboard:
                if entry["user_id"] == user_id:
                    total_users = len(leaderboard)
                    percentile = ((total_users - entry["rank"]) / total_users * 100) if total_users > 0 else 0
                    return {
                        "rank": entry["rank"],
                        "percentile": percentile,
                        "points": entry["total_points"],
                        "level": entry["current_level"],
                        "period": period
                    }

            return {
                "rank": None,
                "percentile": 0,
                "points": 0,
                "level": 1,
                "period": period
            }

        except Exception as e:
            logger.error(f"Error getting user rank: {e}")
            return {}

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_gamification_stats(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive gamification statistics for user"""
        try:
            progress = self.get_user_progress(user_id)
            if not progress:
                return {}

            # Get points from different periods
            now = datetime.utcnow()
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)

            with self.db._get_connection() as conn:
                # Last 7 days
                cursor = conn.execute("""
                    SELECT COALESCE(SUM(points_earned), 0)
                    FROM user_actions
                    WHERE user_id = ? AND created_at >= ?
                """, (user_id, week_ago.isoformat()))
                points_7d = cursor.fetchone()[0]

                # Last 30 days
                cursor = conn.execute("""
                    SELECT COALESCE(SUM(points_earned), 0)
                    FROM user_actions
                    WHERE user_id = ? AND created_at >= ?
                """, (user_id, month_ago.isoformat()))
                points_30d = cursor.fetchone()[0]

                # Completed objectives
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM user_objectives
                    WHERE user_id = ? AND completed_at IS NOT NULL
                """, (user_id,))
                completed_objectives = cursor.fetchone()[0]

            # Calculate daily average
            account_age_days = max((now - datetime.fromisoformat(progress.created_at)).days, 1)
            avg_daily = progress.total_points / account_age_days

            # Get rank
            rank_info = self.get_user_rank(user_id, "all-time")

            return {
                "total_points": progress.total_points,
                "current_level": progress.current_level,
                "level_name": self.levels_map.get(progress.current_level, {}).get("name", "Unknown"),
                "current_streak": progress.current_streak,
                "longest_streak": progress.longest_streak,
                "badges_earned": len(progress.badges_earned),
                "objectives_completed": completed_objectives,
                "points_7_days": points_7d,
                "points_30_days": points_30d,
                "avg_daily_points": round(avg_daily, 1),
                "rank": rank_info.get("rank"),
                "rank_percentile": round(rank_info.get("percentile", 0), 1),
                "account_age_days": account_age_days
            }

        except Exception as e:
            logger.error(f"Error getting gamification stats: {e}")
            return {}
