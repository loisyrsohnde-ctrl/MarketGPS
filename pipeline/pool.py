"""
MarketGPS Pool Job.
Active candidate pool management.
"""
from typing import List, Dict
from datetime import datetime

from core.utils import get_logger
from core.models import PoolMember
from core.config import get_config
from storage.sqlite_store import SQLiteStore

logger = get_logger(__name__)


class PoolJob:
    """
    Pool management job.
    
    Responsibilities:
    - Select eligible assets for active pool
    - Compute priority weights
    - Maintain pool size limits
    """
    
    def __init__(self, store: SQLiteStore = None):
        """
        Initialize pool job.
        
        Args:
            store: SQLite store instance
        """
        self.store = store or SQLiteStore()
        self.config = get_config()
    
    def run(self, max_pool_size: int = 500) -> dict:
        """
        Run pool job.
        
        Args:
            max_pool_size: Maximum pool size
            
        Returns:
            Job statistics
        """
        logger.info("Starting Pool job")
        start_time = datetime.now()
        job_id = self.store.start_job_run("pool")
        
        stats = {
            "pool_size": 0,
            "from_gating": 0,
            "user_interests": 0,
        }
        
        try:
            # Get eligible assets from gating
            eligible_ids = self.store.get_eligible_assets()
            stats["from_gating"] = len(eligible_ids)
            
            # Get user interests (priority boost)
            user_interests = set(self.store.get_active_user_interests())
            stats["user_interests"] = len(user_interests)
            
            # Get current top50 (preserve)
            current_top50 = set(self.store.get_top50_assets())
            
            # Compute priority weights
            pool_candidates = []
            
            for asset_id in eligible_ids:
                weight = self._compute_priority_weight(
                    asset_id,
                    is_user_interest=asset_id in user_interests,
                    is_top50=asset_id in current_top50
                )
                pool_candidates.append((asset_id, weight))
            
            # Add user interests not in eligible (lower priority)
            for asset_id in user_interests:
                if asset_id not in eligible_ids:
                    pool_candidates.append((asset_id, 0.5))  # Low but present
            
            # Sort by priority weight
            pool_candidates.sort(key=lambda x: x[1], reverse=True)
            
            # Limit pool size
            pool_candidates = pool_candidates[:max_pool_size]
            
            # Create pool members
            members = []
            for rank, (asset_id, weight) in enumerate(pool_candidates, 1):
                members.append(PoolMember(
                    asset_id=asset_id,
                    pool_rank=rank,
                    priority_weight=weight,
                ))
            
            # Rebuild pool
            self.store.rebuild_pool(members)
            stats["pool_size"] = len(members)
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Pool job completed in {duration:.1f}s: "
                f"{stats['pool_size']} assets in pool"
            )
            
            self.store.finish_job_run(job_id, "success", assets_processed=stats["pool_size"])
            
        except Exception as e:
            logger.error(f"Pool job failed: {e}")
            self.store.finish_job_run(job_id, "failed", error_summary=str(e))
            stats["error"] = str(e)
        
        return stats
    
    def _compute_priority_weight(
        self,
        asset_id: str,
        is_user_interest: bool = False,
        is_top50: bool = False
    ) -> float:
        """
        Compute priority weight for an asset.
        
        Higher weight = processed more frequently.
        """
        weight = 1.0
        
        # Get gating status for ADV
        status = self.store.get_gating(asset_id)
        if status:
            # Higher ADV = higher priority
            if status.adv_usd >= 10_000_000:
                weight *= 1.5
            elif status.adv_usd >= 5_000_000:
                weight *= 1.3
            elif status.adv_usd >= 1_000_000:
                weight *= 1.1
            
            # Higher confidence = higher priority
            weight *= (0.8 + status.data_confidence / 500)
        
        # User interest boost
        if is_user_interest:
            weight *= 2.0
        
        # Top50 preservation boost
        if is_top50:
            weight *= 1.5
        
        return weight
