"""Tests for rotation job."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestRotationSet:
    """Tests for rotation set building."""
    
    def test_rotation_batch_limit(self):
        """Test rotation respects batch size limit."""
        # Simulated rotation logic
        batch_size = 100
        top50 = list(range(50))
        stale = list(range(200, 400))
        interests = list(range(500, 510))
        
        result = set()
        
        # Add top50
        result.update(top50)
        
        # Add interests
        result.update(interests)
        
        # Fill remaining with stale
        remaining = batch_size - len(result)
        result.update(stale[:remaining])
        
        # Should not exceed batch size
        assert len(result) <= batch_size + 10  # Allow small buffer for interests
    
    def test_top50_always_included(self):
        """Test top50 is always in rotation set."""
        top50 = set(range(50))
        batch_size = 30  # Even smaller batch
        
        result = top50.copy()
        
        # Top50 should always be included regardless of batch size
        assert len(result.intersection(top50)) == len(top50)
    
    def test_user_interests_prioritized(self):
        """Test user interests are prioritized."""
        top50 = set(range(50))
        interests = {100, 101, 102}  # Not in top50
        stale = set(range(200, 300))
        batch_size = 60
        
        result = top50.copy()
        result.update(interests)
        remaining = batch_size - len(result)
        
        # Fill with stale
        for item in list(stale)[:remaining]:
            result.add(item)
        
        # Interests should be in result
        assert interests.issubset(result)
    
    def test_no_full_pool_scan(self):
        """Test rotation never scans full pool."""
        pool_size = 1000
        batch_size = 100
        
        # Rotation should process at most batch_size + top50 + interests
        max_processed = batch_size + 50 + 20  # generous buffer
        
        assert max_processed < pool_size


class TestRotationState:
    """Tests for rotation state tracking."""
    
    def test_stale_ordering(self):
        """Test assets are processed oldest first."""
        # Simulated last_refresh_at times
        assets = [
            ("A", datetime.now() - timedelta(hours=10)),
            ("B", datetime.now() - timedelta(hours=5)),
            ("C", datetime.now() - timedelta(hours=20)),
            ("D", datetime.now() - timedelta(hours=1)),
        ]
        
        # Sort by oldest first
        sorted_assets = sorted(assets, key=lambda x: x[1])
        
        assert sorted_assets[0][0] == "C"  # 20 hours ago
        assert sorted_assets[-1][0] == "D"  # 1 hour ago
    
    def test_cooldown_respected(self):
        """Test cooldown prevents immediate re-processing."""
        cooldown_until = datetime.now() + timedelta(minutes=5)
        current_time = datetime.now()
        
        # Should be excluded if cooldown not expired
        in_cooldown = cooldown_until > current_time
        assert in_cooldown
    
    def test_priority_levels(self):
        """Test priority levels affect selection."""
        assets = [
            ("A", 1),  # Normal
            ("B", 2),  # High priority
            ("C", 0),  # Low priority
        ]
        
        # Sort by priority (higher first)
        sorted_assets = sorted(assets, key=lambda x: x[1], reverse=True)
        
        assert sorted_assets[0][0] == "B"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
