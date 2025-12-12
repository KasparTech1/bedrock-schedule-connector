"""Schedule management service."""
from typing import Any, Optional
from datetime import datetime, timezone

import structlog

from ..mongoose_client import MongooseClient, MongooseConfig
from ..models.schedule import JobOperation, Job, ScheduleOverview
from ..utils import clean_str, parse_float

logger = structlog.get_logger(__name__)


class ScheduleService:
    """Service for managing production schedules."""
    
    def __init__(self, config: MongooseConfig):
        self.config = config
    
    async def get_schedule_overview(
        self,
        include_complete: bool = False,
        limit: int = 100
    ) -> ScheduleOverview:
        """
        Get overview of current production schedule.
        
        Args:
            include_complete: Include completed jobs
            limit: Max jobs to return
            
        Returns:
            ScheduleOverview with jobs and statistics
        """
        async with MongooseClient(self.config) as client:
            # Determine job filter
            job_filter = None if include_complete else "Stat='R'"
            
            # Fetch all data in parallel
            data = await client.parallel_fetch([
                ("SLJobs", ["Job", "Suffix", "Item", "QtyReleased", "QtyComplete", "Stat", "CustNum"], job_filter, limit),
                ("SLJobRoutes", ["Job", "Suffix", "OperNum", "Wc", "QtyComplete", "QtyScrapped"], None, limit * 10),
                ("SLItems", ["Item", "Description"], None, 5000),
                ("SLCustomers", ["CustNum", "Name"], None, 5000),
            ])
            
            # Build lookup tables
            items_lookup = {
                clean_str(i.get("Item")): i.get("Description", "")
                for i in data.get("SLItems", [])
            }
            
            customers_lookup = {
                clean_str(c.get("CustNum")): c.get("Name", "")
                for c in data.get("SLCustomers", [])
            }
            
            # Group operations by job
            ops_by_job: dict[str, list[dict]] = {}
            for op in data.get("SLJobRoutes", []):
                job_key = f"{clean_str(op.get('Job'))}_{op.get('Suffix', '0')}"
                if job_key not in ops_by_job:
                    ops_by_job[job_key] = []
                ops_by_job[job_key].append(op)
            
            # Build job objects
            jobs = []
            jobs_by_status: dict[str, int] = {}
            work_centers_set: set[str] = set()
            
            for job_data in data.get("SLJobs", []):
                job_num = clean_str(job_data.get("Job"))
                suffix = int(job_data.get("Suffix", 0) or 0)
                job_key = f"{job_num}_{suffix}"
                
                item = clean_str(job_data.get("Item"))
                cust_num = clean_str(job_data.get("CustNum"))
                status = clean_str(job_data.get("Stat"))
                
                # Build operations
                operations = []
                for op_data in ops_by_job.get(job_key, []):
                    wc = clean_str(op_data.get("Wc"))
                    work_centers_set.add(wc)
                    
                    operations.append(JobOperation(
                        job=job_num,
                        suffix=suffix,
                        operation_num=int(op_data.get("OperNum", 0) or 0),
                        work_center=wc,
                        qty_complete=parse_float(op_data.get("QtyComplete")),
                        qty_scrapped=parse_float(op_data.get("QtyScrapped")),
                    ))
                
                # Sort operations by operation number
                operations.sort(key=lambda x: x.operation_num)
                
                job = Job(
                    job=job_num,
                    suffix=suffix,
                    item=item,
                    item_description=items_lookup.get(item, ""),
                    qty_released=parse_float(job_data.get("QtyReleased")),
                    qty_complete=parse_float(job_data.get("QtyComplete")),
                    status=status,
                    customer_num=cust_num if cust_num else None,
                    customer_name=customers_lookup.get(cust_num) if cust_num else None,
                    operations=operations,
                )
                
                jobs.append(job)
                
                # Track status counts
                jobs_by_status[status] = jobs_by_status.get(status, 0) + 1
            
            # Sort jobs by job number
            jobs.sort(key=lambda x: (x.job, x.suffix))
            
            return ScheduleOverview(
                total_jobs=len(jobs),
                active_jobs=sum(1 for j in jobs if not j.is_complete),
                jobs_by_status=jobs_by_status,
                work_centers=sorted(work_centers_set),
                jobs=jobs,
                fetched_at=datetime.now(timezone.utc),
            )
    
    async def get_jobs_at_work_center(
        self,
        work_center: str,
        include_complete: bool = False,
        limit: int = 50
    ) -> list[Job]:
        """
        Get jobs with operations at a specific work center.
        
        Args:
            work_center: Work center code (e.g., "HF-CUT")
            include_complete: Include completed jobs
            limit: Max jobs to return
            
        Returns:
            List of jobs with operations at the work center
        """
        overview = await self.get_schedule_overview(
            include_complete=include_complete,
            limit=limit * 2  # Fetch more since we'll filter
        )
        
        # Filter to jobs with operations at this work center
        filtered_jobs = [
            job for job in overview.jobs
            if any(op.work_center == work_center for op in job.operations)
        ]
        
        return filtered_jobs[:limit]
    
    async def get_job_details(
        self,
        job_number: str,
        suffix: int = 0
    ) -> Optional[Job]:
        """
        Get detailed information for a specific job.
        
        Args:
            job_number: Job number
            suffix: Job suffix (default 0)
            
        Returns:
            Job details or None if not found
        """
        async with MongooseClient(self.config) as client:
            # Pad job number if needed (SyteLine uses right-padded strings)
            job_filter = f"Job='{job_number}' AND Suffix={suffix}"
            
            # Fetch job and its operations
            data = await client.parallel_fetch([
                ("SLJobs", ["Job", "Suffix", "Item", "QtyReleased", "QtyComplete", "Stat", "CustNum"], job_filter, 1),
                ("SLJobRoutes", ["Job", "Suffix", "OperNum", "Wc", "QtyComplete", "QtyScrapped"], f"Job='{job_number}'", 100),
            ])
            
            jobs = data.get("SLJobs", [])
            if not jobs:
                return None
            
            job_data = jobs[0]
            job_num = clean_str(job_data.get("Job"))
            item = clean_str(job_data.get("Item"))
            cust_num = clean_str(job_data.get("CustNum"))
            
            # Get item description
            items = await client.query_ido("SLItems", ["Item", "Description"], f"Item='{item}'", 1)
            item_desc = items[0].get("Description", "") if items else ""
            
            # Get customer name if applicable
            cust_name = None
            if cust_num:
                customers = await client.query_ido("SLCustomers", ["CustNum", "Name"], f"CustNum='{cust_num}'", 1)
                cust_name = customers[0].get("Name", "") if customers else None
            
            # Build operations
            operations = []
            for op_data in data.get("SLJobRoutes", []):
                operations.append(JobOperation(
                    job=job_num,
                    suffix=suffix,
                    operation_num=int(op_data.get("OperNum", 0) or 0),
                    work_center=clean_str(op_data.get("Wc")),
                    qty_complete=parse_float(op_data.get("QtyComplete")),
                    qty_scrapped=parse_float(op_data.get("QtyScrapped")),
                ))
            
            operations.sort(key=lambda x: x.operation_num)
            
            return Job(
                job=job_num,
                suffix=suffix,
                item=item,
                item_description=item_desc,
                qty_released=parse_float(job_data.get("QtyReleased")),
                qty_complete=parse_float(job_data.get("QtyComplete")),
                status=clean_str(job_data.get("Stat")),
                customer_num=cust_num if cust_num else None,
                customer_name=cust_name,
                operations=operations,
            )
    
    async def get_work_center_queue(
        self,
        work_center: str,
        limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Get the queue of operations at a work center.
        
        Args:
            work_center: Work center code
            limit: Max operations to return
            
        Returns:
            List of operations with job details
        """
        async with MongooseClient(self.config) as client:
            # Fetch operations at this work center
            ops = await client.query_ido(
                "SLJobRoutes",
                ["Job", "Suffix", "OperNum", "Wc", "QtyComplete", "QtyScrapped"],
                f"Wc='{work_center}'",
                limit
            )
            
            if not ops:
                return []
            
            # Get unique jobs
            job_nums = list(set(clean_str(op.get("Job")) for op in ops))
            
            # Fetch job details (limited batch)
            jobs = await client.query_ido(
                "SLJobs",
                ["Job", "Suffix", "Item", "QtyReleased", "QtyComplete", "Stat"],
                None,  # Would need IN clause - fetch all for now
                1000
            )
            
            # Build job lookup
            jobs_lookup = {
                clean_str(j.get("Job")): j
                for j in jobs
            }
            
            # Build queue with job info
            queue = []
            for op in ops:
                job_num = clean_str(op.get("Job"))
                job_data = jobs_lookup.get(job_num, {})
                
                queue.append({
                    "job": job_num,
                    "suffix": int(op.get("Suffix", 0) or 0),
                    "operation_num": int(op.get("OperNum", 0) or 0),
                    "work_center": clean_str(op.get("Wc")),
                    "item": clean_str(job_data.get("Item")),
                    "qty_released": parse_float(job_data.get("QtyReleased")),
                    "qty_complete": parse_float(op.get("QtyComplete")),
                    "job_status": clean_str(job_data.get("Stat")),
                })
            
            # Sort by job number and operation
            queue.sort(key=lambda x: (x["job"], x["operation_num"]))
            
            return queue

