"""Schedule-related data models."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class JobOperation:
    """A single operation within a job."""
    job: str
    suffix: int
    operation_num: int
    work_center: str
    qty_complete: float
    qty_scrapped: float
    # Future: sched_start, sched_finish when SLJrtSchs available


@dataclass
class Job:
    """A manufacturing job with its operations."""
    job: str
    suffix: int
    item: str
    item_description: str
    qty_released: float
    qty_complete: float
    status: str
    customer_num: Optional[str]
    customer_name: Optional[str]
    operations: list[JobOperation]
    
    @property
    def pct_complete(self) -> float:
        """Calculate percent complete."""
        if self.qty_released <= 0:
            return 0.0
        return round((self.qty_complete / self.qty_released) * 100, 1)
    
    @property
    def is_complete(self) -> bool:
        """Check if job is fully complete."""
        return self.qty_complete >= self.qty_released


@dataclass  
class ScheduleOverview:
    """Overview of production schedule."""
    total_jobs: int
    active_jobs: int
    jobs_by_status: dict[str, int]
    work_centers: list[str]
    jobs: list[Job]
    fetched_at: datetime

