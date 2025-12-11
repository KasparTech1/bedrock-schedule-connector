"""
Connector Metrics Tracking
==========================

Tracks execution metrics for connectors including:
- API call counts and timing
- Records fetched per IDO
- Total execution time
- Historical run statistics
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from collections import deque
import threading

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class IDOCallMetrics:
    """Metrics for a single IDO API call."""
    ido_name: str
    properties_count: int
    filter_expression: Optional[str]
    record_cap: int
    records_returned: int
    duration_ms: float
    started_at: datetime
    success: bool
    error_message: Optional[str] = None


@dataclass
class ConnectorRunMetrics:
    """Metrics for a single connector execution."""
    connector_name: str
    run_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    # API call details
    ido_calls: list[IDOCallMetrics] = field(default_factory=list)
    total_api_calls: int = 0
    parallel_batches: int = 0
    max_concurrent: int = 5
    
    # Data processing
    total_records_fetched: int = 0
    output_records: int = 0
    
    # Timing
    api_time_ms: float = 0
    processing_time_ms: float = 0
    total_time_ms: float = 0
    
    # Filters applied
    filters: dict[str, Any] = field(default_factory=dict)
    
    # Status
    success: bool = True
    error_message: Optional[str] = None
    
    def add_ido_call(self, call: IDOCallMetrics):
        """Add an IDO call metric."""
        self.ido_calls.append(call)
        self.total_api_calls += 1
        self.total_records_fetched += call.records_returned
        self.api_time_ms += call.duration_ms
    
    def finalize(self, output_records: int):
        """Finalize the run metrics."""
        self.completed_at = datetime.now(timezone.utc)
        self.output_records = output_records
        self.total_time_ms = (self.completed_at - self.started_at).total_seconds() * 1000
        self.processing_time_ms = self.total_time_ms - self.api_time_ms
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "connector_name": self.connector_name,
            "run_id": self.run_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "ido_calls": [
                {
                    "ido_name": call.ido_name,
                    "properties_count": call.properties_count,
                    "filter_expression": call.filter_expression,
                    "record_cap": call.record_cap,
                    "records_returned": call.records_returned,
                    "duration_ms": round(call.duration_ms, 1),
                    "success": call.success,
                    "error": call.error_message,
                }
                for call in self.ido_calls
            ],
            "summary": {
                "total_api_calls": self.total_api_calls,
                "parallel_batches": self.parallel_batches,
                "max_concurrent": self.max_concurrent,
                "total_records_fetched": self.total_records_fetched,
                "output_records": self.output_records,
                "api_time_ms": round(self.api_time_ms, 1),
                "processing_time_ms": round(self.processing_time_ms, 1),
                "total_time_ms": round(self.total_time_ms, 1),
            },
            "filters": self.filters,
            "success": self.success,
            "error": self.error_message,
        }


@dataclass
class ConnectorAnatomy:
    """
    Static anatomy of a connector - its structure and configuration.
    """
    name: str
    description: str
    
    # IDO configuration
    idos: list[dict[str, Any]]  # List of IDO specs
    
    # Join/processing logic
    join_description: str
    processing_steps: list[str]
    
    # Expected volumes
    typical_record_counts: dict[str, int]
    
    # Allocation logic (for order availability)
    allocation_logic: Optional[list[str]] = None
    
    # Business day calendar (if applicable)
    calendar_config: Optional[dict[str, Any]] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "name": self.name,
            "description": self.description,
            "data_sources": {
                "idos": self.idos,
                "total_ido_count": len(self.idos),
            },
            "processing": {
                "join_description": self.join_description,
                "steps": self.processing_steps,
            },
            "expected_volumes": self.typical_record_counts,
            "allocation_logic": self.allocation_logic,
            "calendar_config": self.calendar_config,
        }


class MetricsStore:
    """
    Thread-safe store for connector execution metrics.
    
    Keeps last N runs for each connector for historical analysis.
    """
    
    MAX_HISTORY = 20
    
    def __init__(self):
        self._runs: dict[str, deque[ConnectorRunMetrics]] = {}
        self._lock = threading.Lock()
        self._current_run: dict[str, ConnectorRunMetrics] = {}
    
    def start_run(self, connector_name: str, filters: dict[str, Any] = None) -> ConnectorRunMetrics:
        """Start tracking a new connector run."""
        import uuid
        
        run = ConnectorRunMetrics(
            connector_name=connector_name,
            run_id=str(uuid.uuid4())[:8],
            started_at=datetime.now(timezone.utc),
            filters=filters or {},
        )
        
        with self._lock:
            self._current_run[connector_name] = run
        
        return run
    
    def complete_run(self, connector_name: str, output_records: int, error: str = None):
        """Complete and store a connector run."""
        with self._lock:
            if connector_name in self._current_run:
                run = self._current_run.pop(connector_name)
                run.finalize(output_records)
                
                if error:
                    run.success = False
                    run.error_message = error
                
                if connector_name not in self._runs:
                    self._runs[connector_name] = deque(maxlen=self.MAX_HISTORY)
                
                self._runs[connector_name].append(run)
                
                logger.info(
                    "Connector run completed",
                    connector=connector_name,
                    run_id=run.run_id,
                    total_ms=round(run.total_time_ms, 1),
                    api_calls=run.total_api_calls,
                    records=run.output_records,
                )
                
                return run
        return None
    
    def get_current_run(self, connector_name: str) -> Optional[ConnectorRunMetrics]:
        """Get the current in-progress run."""
        with self._lock:
            return self._current_run.get(connector_name)
    
    def get_run_history(self, connector_name: str) -> list[ConnectorRunMetrics]:
        """Get historical runs for a connector."""
        with self._lock:
            if connector_name in self._runs:
                return list(self._runs[connector_name])
            return []
    
    def get_aggregate_stats(self, connector_name: str) -> dict[str, Any]:
        """Get aggregate statistics across historical runs."""
        runs = self.get_run_history(connector_name)
        
        if not runs:
            return {
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
            }
        
        successful = [r for r in runs if r.success]
        
        if not successful:
            return {
                "total_runs": len(runs),
                "successful_runs": 0,
                "failed_runs": len(runs),
            }
        
        avg_total_time = sum(r.total_time_ms for r in successful) / len(successful)
        avg_api_time = sum(r.api_time_ms for r in successful) / len(successful)
        avg_records = sum(r.output_records for r in successful) / len(successful)
        avg_api_calls = sum(r.total_api_calls for r in successful) / len(successful)
        
        min_time = min(r.total_time_ms for r in successful)
        max_time = max(r.total_time_ms for r in successful)
        
        # Per-IDO stats
        ido_stats = {}
        for run in successful:
            for call in run.ido_calls:
                if call.ido_name not in ido_stats:
                    ido_stats[call.ido_name] = {
                        "call_count": 0,
                        "total_records": 0,
                        "total_duration_ms": 0,
                    }
                ido_stats[call.ido_name]["call_count"] += 1
                ido_stats[call.ido_name]["total_records"] += call.records_returned
                ido_stats[call.ido_name]["total_duration_ms"] += call.duration_ms
        
        # Calculate averages
        for ido_name, stats in ido_stats.items():
            if stats["call_count"] > 0:
                stats["avg_records"] = round(stats["total_records"] / stats["call_count"], 1)
                stats["avg_duration_ms"] = round(stats["total_duration_ms"] / stats["call_count"], 1)
        
        return {
            "total_runs": len(runs),
            "successful_runs": len(successful),
            "failed_runs": len(runs) - len(successful),
            "timing": {
                "avg_total_ms": round(avg_total_time, 1),
                "avg_api_ms": round(avg_api_time, 1),
                "min_total_ms": round(min_time, 1),
                "max_total_ms": round(max_time, 1),
            },
            "records": {
                "avg_output": round(avg_records, 1),
                "avg_api_calls": round(avg_api_calls, 1),
            },
            "ido_stats": ido_stats,
            "last_run": runs[-1].to_dict() if runs else None,
        }


# Global metrics store instance
_metrics_store: Optional[MetricsStore] = None


def get_metrics_store() -> MetricsStore:
    """Get the global metrics store instance."""
    global _metrics_store
    if _metrics_store is None:
        _metrics_store = MetricsStore()
    return _metrics_store


# Connector Anatomy Definitions
ORDER_AVAILABILITY_ANATOMY = ConnectorAnatomy(
    name="Order Availability",
    description="""
Customer order availability with inventory allocation analysis.
Emulates the Syteline 8 TBE_Customer_Order_Availability_Add_Release_Date stored procedure.

Shows open customer orders with how inventory is allocated from different
production stages: On Hand → Paint → Blast → Weld/Fab.
""",
    idos=[
        {
            "name": "SLCos",
            "description": "Customer order headers",
            "properties": ["CoNum", "CustNum", "CustSeq", "OrderDate", "Stat"],
            "filter": "Stat='O'",
            "record_cap": 1000,
        },
        {
            "name": "SLCoitems",
            "description": "Customer order line items",
            "properties": ["CoNum", "CoLine", "CoRelease", "Item", "QtyOrdered", "QtyShipped", "DueDate", "Price", "Stat"],
            "filter": "Stat='O'",
            "record_cap": 5000,
        },
        {
            "name": "SLCustaddrs",
            "description": "Customer addresses (for names)",
            "properties": ["CustNum", "CustSeq", "Name"],
            "filter": None,
            "record_cap": 5000,
        },
        {
            "name": "SLItems",
            "description": "Item master data",
            "properties": ["Item", "Description", "DrawingNbr", "DerDrawingNbr"],
            "filter": None,
            "record_cap": 10000,
        },
        {
            "name": "SLItemwhses",
            "description": "Inventory by warehouse",
            "properties": ["Item", "Whse", "QtyOnHand", "QtyAllocCo", "QtyWip"],
            "filter": "Whse='Main'",
            "record_cap": 10000,
        },
        {
            "name": "SLJobs",
            "description": "Manufacturing jobs",
            "properties": ["Job", "Suffix", "Item", "QtyReleased", "Stat", "JobDate"],
            "filter": "Type='J'",
            "record_cap": 5000,
        },
        {
            "name": "SLJobRoutes",
            "description": "Job operations/routing",
            "properties": ["Job", "Suffix", "Wc", "QtyReceived", "QtyComplete"],
            "filter": None,
            "record_cap": 20000,
        },
    ],
    join_description="""
1. Join SLCos (orders) with SLCoitems (line items) on CoNum
2. Join with SLCustaddrs on CustNum+CustSeq for customer names
3. Join with SLItems on Item for descriptions
4. Join with SLItemwhses on Item for inventory levels
5. Cross-reference SLJobs and SLJobRoutes to calculate WIP at each work center
""",
    processing_steps=[
        "1. Fetch all 7 IDOs in parallel (max 5 concurrent)",
        "2. Build lookup tables for customers, items, inventory",
        "3. Calculate WIP quantities at each work center (PAINT, BLAST) from job routes",
        "4. Calculate ReleasedWeldFab = QtyWIP - QtyInPaint - QtyInBlast",
        "5. Build jobs-by-item mapping with release dates",
        "6. Filter to open order lines with remaining quantity > 0",
        "7. Sort by due date for allocation priority",
        "8. Apply allocation algorithm (cursor emulation):",
        "   - For each order line in due date order:",
        "   - Allocate from On Hand first",
        "   - Then from Paint queue",
        "   - Then from Blast queue",
        "   - Then from Released Weld/Fab",
        "9. Calculate completion dates based on business day calendar",
        "10. Return final result with coverage analysis",
    ],
    typical_record_counts={
        "SLCos": 200,
        "SLCoitems": 500,
        "SLCustaddrs": 1000,
        "SLItems": 3000,
        "SLItemwhses": 3000,
        "SLJobs": 500,
        "SLJobRoutes": 5000,
    },
    allocation_logic=[
        "Priority 1: On Hand inventory - immediately available",
        "Priority 2: Paint queue - nearly complete (7+ days from release)",
        "Priority 3: Blast queue - in process (4-7 days from release)",
        "Priority 4: Released Weld/Fab - early production (0-4 days from release)",
        "",
        "Allocation is done in due date order, so earlier orders get first pick",
        "Once inventory is allocated to an order, it's no longer available for later orders",
    ],
    calendar_config={
        "business_days": "Monday-Thursday only",
        "friday": "Not a business day (per original stored procedure)",
        "weekend": "Not business days",
        "holidays_2025": [
            "2025-01-01 (New Year's Day)",
            "2025-05-26 (Memorial Day)",
            "2025-07-03 (Independence Day)",
            "2025-09-01 (Labor Day)",
            "2025-11-27 (Thanksgiving)",
            "2025-12-24 (Christmas Eve)",
            "2025-12-25 (Christmas Day)",
        ],
        "completion_estimates": {
            "weld_fab": "4 business days from release",
            "blast": "7 business days from release",
            "paint_assembly": "10 business days from release",
        },
    },
)


FLOW_OPTIMIZER_ANATOMY = ConnectorAnatomy(
    name="Flow Optimizer (Open Orders)",
    description="""
Open orders with WIP data for Flow Optimizer import.
Matches the TBE_App OPEN ORDERS V5 query schema.
""",
    idos=[
        {
            "name": "SLCos",
            "description": "Customer order headers",
            "properties": ["CoNum", "CustNum", "OrderDate", "Stat"],
            "filter": "Stat='O'",
            "record_cap": 1000,
        },
        {
            "name": "SLCoitems",
            "description": "Order line items",
            "properties": ["CoNum", "CoLine", "Item", "QtyOrdered", "QtyShipped", "DueDate", "PromiseDate", "Price", "Stat"],
            "filter": "Stat='O'",
            "record_cap": 5000,
        },
        {
            "name": "SLCustomers",
            "description": "Customer names",
            "properties": ["CustNum", "Name"],
            "filter": None,
            "record_cap": 5000,
        },
        {
            "name": "SLItems",
            "description": "Item descriptions",
            "properties": ["Item", "Description", "DerDrawingNbr", "DrawingNbr"],
            "filter": None,
            "record_cap": 10000,
        },
        {
            "name": "SLJobs",
            "description": "Manufacturing jobs",
            "properties": ["Job", "Suffix", "Item", "QtyReleased", "QtyComplete", "Stat", "Type", "JobDate"],
            "filter": "Type='J'",
            "record_cap": 5000,
        },
        {
            "name": "SLJobRoutes",
            "description": "Job routes for WIP",
            "properties": ["Job", "Suffix", "Wc", "QtyReceived", "QtyComplete"],
            "filter": None,
            "record_cap": 20000,
        },
        {
            "name": "SLItemwhses",
            "description": "On-hand inventory",
            "properties": ["Item", "QtyOnHand", "QtyAllocCo", "QtyWip"],
            "filter": None,
            "record_cap": 10000,
        },
    ],
    join_description="""
1. Join orders with line items on CoNum
2. Lookup customer names
3. Lookup item descriptions and drawing numbers
4. Calculate WIP at each work center from job routes
5. Get on-hand inventory per item
""",
    processing_steps=[
        "1. Parallel fetch all 7 IDOs",
        "2. Build lookup tables",
        "3. Calculate WIP at WELD, BLAST, PAINT, ASSY work centers",
        "4. Parse bed type from drawing number (Granite, Diamond, Marble, etc.)",
        "5. Calculate urgency bucket based on days until due",
        "6. Sort by due date, customer, item",
    ],
    typical_record_counts={
        "SLCos": 200,
        "SLCoitems": 500,
        "SLCustomers": 1000,
        "SLItems": 3000,
        "SLJobs": 500,
        "SLJobRoutes": 5000,
        "SLItemwhses": 3000,
    },
)


CUSTOMER_SEARCH_ANATOMY = ConnectorAnatomy(
    name="Customer Search",
    description="Search and lookup Bedrock Truck Beds customers.",
    idos=[
        {
            "name": "SLCustomers",
            "description": "Customer master data",
            "properties": [
                "CustNum", "Name", "Addr_1", "Addr_2", "City", "State",
                "Zip", "Country", "TelexNum", "Contact_1", "CreditHold", "CustType", "Stat"
            ],
            "filter": "Dynamic based on search parameters",
            "record_cap": 100,
        },
    ],
    join_description="Single IDO query with optional filters",
    processing_steps=[
        "1. Build filter expression from search parameters",
        "2. Query SLCustomers IDO",
        "3. Apply client-side search term filter if needed",
        "4. Return matching customers",
    ],
    typical_record_counts={
        "SLCustomers": 50,
    },
)


# Registry of connector anatomies
CONNECTOR_ANATOMIES = {
    "order-availability": ORDER_AVAILABILITY_ANATOMY,
    "flow-optimizer": FLOW_OPTIMIZER_ANATOMY,
    "customer-search": CUSTOMER_SEARCH_ANATOMY,
}


def get_connector_anatomy(connector_id: str) -> Optional[ConnectorAnatomy]:
    """Get the anatomy definition for a connector."""
    return CONNECTOR_ANATOMIES.get(connector_id)
