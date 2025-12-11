"""
Bedrock Ops Scheduler Connector
===============================

Production schedule visibility for Bedrock Truck Beds.
This is the flagship connector that demonstrates the full pattern.

Source IDOs:
- SLJobs: Job headers (item, qty, status)
- SLJobroutes: Operations (work center, sequence, progress)
- SLJrtSchs: Schedule (start/finish dates)
- SLItems: Item descriptions
- SLItemwhses: Inventory levels
- SLWcs: Work center descriptions
"""

from datetime import datetime
from typing import Any, Optional

from kai_erp.connectors.base import BaseConnector
from kai_erp.core.security import ODataSanitizer, validate_filter_value
from kai_erp.core.types import IDOSpec, RestQuerySpec
from kai_erp.models.operations import OperationStatus, ScheduledOperation


class BedrockOpsScheduler(BaseConnector[ScheduledOperation]):
    """
    Production schedule connector for Bedrock operations.
    
    Provides real-time visibility into what's being manufactured,
    where, and progress status.
    
    Example:
        async with RestEngine(config) as engine:
            scheduler = BedrockOpsScheduler(engine)
            result = await scheduler.execute(
                filters={"work_center": "WELD-01"}
            )
            for op in result.data:
                print(f"{op['job']}: {op['pct_complete']}% complete")
    """
    
    # Typical volume estimates
    TYPICAL_ACTIVE_JOBS = 200
    TYPICAL_OPS_PER_JOB = 4
    
    def get_rest_spec(self, filters: Optional[dict[str, Any]] = None) -> RestQuerySpec:
        """
        Define REST API access pattern for production schedule.
        
        Fetches 6 IDOs and joins them to create complete operation view.
        Uses parameterized queries to prevent SQL injection.
        """
        # Build job filter - OData filters for API calls (with sanitization)
        job_filter_parts = ["Stat='R'"]  # Released jobs only
        if filters:
            if filters.get("job"):
                safe_job = validate_filter_value(filters["job"])
                job_filter_parts.append(ODataSanitizer.build_equals_filter("Job", safe_job))
        job_filter = ODataSanitizer.build_and_filter(job_filter_parts)
        
        # Build jobroute filter for API call (with sanitization)
        jobroute_filter = None
        if filters and filters.get("work_center"):
            safe_wc = validate_filter_value(filters["work_center"])
            jobroute_filter = ODataSanitizer.build_equals_filter("Wc", safe_wc)
        
        # Build parameterized join SQL
        join_sql, join_params = self._build_join_sql(filters)
        
        return RestQuerySpec(
            idos=[
                IDOSpec(
                    name="SLJobs",
                    properties=[
                        "Job", "Suffix", "Item", "QtyReleased",
                        "QtyComplete", "Stat", "Whse"
                    ],
                    filter=job_filter
                ),
                IDOSpec(
                    name="SLJobroutes",
                    properties=[
                        "Job", "Suffix", "OperNum", "Wc",
                        "QtyComplete", "QtyScrapped"
                    ],
                    filter=jobroute_filter
                ),
                IDOSpec(
                    name="SLJrtSchs",
                    properties=[
                        "Job", "Suffix", "OperNum",
                        "SchedStart", "SchedFinish"
                    ]
                ),
                IDOSpec(
                    name="SLItems",
                    properties=["Item", "Description"]
                ),
                IDOSpec(
                    name="SLItemwhses",
                    properties=["Item", "Whse", "QtyOnHand"]
                ),
                IDOSpec(
                    name="SLWcs",
                    properties=["Wc", "Description"]
                )
            ],
            join_sql=join_sql,
            join_params=join_params
        )
    
    def _build_join_sql(self, filters: Optional[dict[str, Any]] = None) -> tuple[str, list[Any]]:
        """
        Build the DuckDB join SQL with optional filters.
        
        Returns:
            Tuple of (sql_query, parameters) for parameterized execution.
            This prevents SQL injection attacks.
        """
        params: list[Any] = []
        
        base_sql = """
            SELECT 
                j.Job,
                j.Suffix,
                j.Item,
                j.QtyReleased,
                j.QtyComplete as JobQtyComplete,
                jr.OperNum,
                jr.Wc,
                jr.QtyComplete as OperQtyComplete,
                jr.QtyScrapped,
                js.SchedStart,
                js.SchedFinish,
                i.Description as ItemDescription,
                iw.QtyOnHand,
                wc.Description as WcDescription,
                
                -- Calculated: percent complete
                CASE 
                    WHEN j.QtyReleased > 0 
                    THEN ROUND((COALESCE(jr.QtyComplete, 0) / j.QtyReleased) * 100, 1)
                    ELSE 0 
                END as PctComplete,
                
                -- Calculated: status
                CASE
                    WHEN COALESCE(jr.QtyComplete, 0) >= j.QtyReleased THEN 'complete'
                    WHEN js.SchedFinish < CURRENT_TIMESTAMP THEN 'behind'
                    ELSE 'on_track'
                END as Status
                
            FROM SLJobs j
            JOIN SLJobroutes jr 
                ON j.Job = jr.Job AND j.Suffix = jr.Suffix
            LEFT JOIN SLJrtSchs js 
                ON jr.Job = js.Job 
                AND jr.Suffix = js.Suffix 
                AND jr.OperNum = js.OperNum
            LEFT JOIN SLItems i 
                ON j.Item = i.Item
            LEFT JOIN SLItemwhses iw 
                ON j.Item = iw.Item AND j.Whse = iw.Whse
            LEFT JOIN SLWcs wc 
                ON jr.Wc = wc.Wc
        """
        
        # Add WHERE clauses based on filters using parameterized queries
        where_clauses = []
        
        if filters:
            if not filters.get("include_completed", False):
                where_clauses.append("COALESCE(jr.QtyComplete, 0) < j.QtyReleased")
            
            if filters.get("work_center"):
                where_clauses.append("jr.Wc = ?")
                params.append(filters["work_center"])
            
            if filters.get("job"):
                where_clauses.append("j.Job = ?")
                params.append(filters["job"])
        else:
            # Default: exclude completed
            where_clauses.append("COALESCE(jr.QtyComplete, 0) < j.QtyReleased")
        
        if where_clauses:
            base_sql += " WHERE " + " AND ".join(where_clauses)
        
        base_sql += " ORDER BY js.SchedStart, j.Job, jr.OperNum"
        
        return base_sql, params
    
    def get_lake_query(self, filters: Optional[dict[str, Any]] = None) -> str:
        """
        Define Data Lake SQL query for bulk/historical access.
        
        Uses Compass SQL syntax against replicated tables.
        """
        base_query = """
            SELECT 
                j.job as Job,
                j.suffix as Suffix,
                j.item as Item,
                j.qty_released as QtyReleased,
                j.qty_complete as JobQtyComplete,
                jr.oper_num as OperNum,
                jr.wc as Wc,
                jr.qty_complete as OperQtyComplete,
                js.sched_start as SchedStart,
                js.sched_finish as SchedFinish,
                i.description as ItemDescription,
                iw.qty_on_hand as QtyOnHand,
                wc.description as WcDescription
                
            FROM SYTELINE.job j
            JOIN SYTELINE.jobroute jr 
                ON j.job = jr.job AND j.suffix = jr.suffix
            LEFT JOIN SYTELINE.jrt_sch js 
                ON jr.job = js.job 
                AND jr.suffix = js.suffix 
                AND jr.oper_num = js.oper_num
            LEFT JOIN SYTELINE.item i 
                ON j.item = i.item
            LEFT JOIN SYTELINE.itemwhse iw 
                ON j.item = iw.item AND j.whse = iw.whse
            LEFT JOIN SYTELINE.wc wc 
                ON jr.wc = wc.wc
                
            WHERE j.stat = 'R'
        """
        
        # Apply filters with sanitization to prevent SQL injection
        if filters:
            if filters.get("work_center"):
                safe_wc = ODataSanitizer.escape_string(
                    validate_filter_value(filters["work_center"])
                )
                base_query += f" AND jr.wc = '{safe_wc}'"
            if filters.get("job"):
                safe_job = ODataSanitizer.escape_string(
                    validate_filter_value(filters["job"])
                )
                base_query += f" AND j.job = '{safe_job}'"
        
        base_query += " ORDER BY js.sched_start, j.job, jr.oper_num"
        
        return base_query
    
    async def estimate_volume(self, filters: Optional[dict[str, Any]] = None) -> int:
        """
        Estimate result count based on typical volumes and filters.
        
        Typical Bedrock production:
        - 100-300 active jobs
        - 3-8 operations per job
        - ~800 total operations (typical)
        - ~2000 operations (peak season)
        """
        base = self.TYPICAL_ACTIVE_JOBS * self.TYPICAL_OPS_PER_JOB  # ~800
        
        if not filters:
            return base
        
        # Filters reduce volume significantly
        if filters.get("job"):
            return self.TYPICAL_OPS_PER_JOB  # ~4 ops for single job
        
        if filters.get("work_center"):
            # Roughly 10 work centers, so 1/10 of total
            return base // 10  # ~80 ops
        
        return base
    
    def transform_result(self, row: dict[str, Any]) -> ScheduledOperation:
        """
        Transform query result row to ScheduledOperation model.
        
        Handles data type conversions and status mapping.
        """
        # Parse status string to enum
        status_str = row.get("Status", "unknown")
        try:
            status = OperationStatus(status_str)
        except ValueError:
            status = OperationStatus.UNKNOWN
        
        # Parse datetime fields
        sched_start = self._parse_datetime(row.get("SchedStart"))
        sched_finish = self._parse_datetime(row.get("SchedFinish"))
        
        return ScheduledOperation(
            job=str(row.get("Job", "")),
            suffix=int(row.get("Suffix", 0)),
            item=str(row.get("Item", "")),
            item_description=str(row.get("ItemDescription", "")),
            operation_num=int(row.get("OperNum", 0)),
            work_center=str(row.get("Wc", "")),
            work_center_description=str(row.get("WcDescription", "")),
            qty_released=float(row.get("QtyReleased", 0)),
            qty_complete=float(row.get("OperQtyComplete", 0)),
            pct_complete=float(row.get("PctComplete", 0)),
            sched_start=sched_start,
            sched_finish=sched_finish,
            status=status,
            qty_on_hand=float(row.get("QtyOnHand", 0)) if row.get("QtyOnHand") else None
        )
    
    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """Parse datetime from various formats."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None
