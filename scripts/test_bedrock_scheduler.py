#!/usr/bin/env python3
"""
Test Bedrock Scheduler
======================

Test the full Bedrock Scheduler connector with real API calls.

Usage:
    uv run python scripts/test_bedrock_scheduler.py
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kai_erp.mongoose import BedrockScheduler, MongooseConfig


async def main():
    print("=" * 70)
    print("BEDROCK SCHEDULER CONNECTOR TEST")
    print("=" * 70)
    print()
    
    # Create scheduler with Bedrock HFA config
    config = MongooseConfig.bedrock_hfa()
    scheduler = BedrockScheduler(config)
    
    # Test 1: Get schedule overview
    print("-" * 70)
    print("TEST 1: Get Schedule Overview")
    print("-" * 70)
    
    try:
        overview = await scheduler.get_schedule_overview(limit=10)
        
        print(f"✅ Total Jobs: {overview.total_jobs}")
        print(f"✅ Active Jobs: {overview.active_jobs}")
        print(f"✅ Jobs by Status: {overview.jobs_by_status}")
        print(f"✅ Work Centers: {overview.work_centers}")
        print()
        
        print("Sample Jobs:")
        for job in overview.jobs[:5]:
            print(f"  - Job {job.job}: {job.item} ({job.item_description[:30]}...)")
            print(f"    Qty: {job.qty_complete}/{job.qty_released} ({job.pct_complete}% complete)")
            print(f"    Operations: {len(job.operations)}")
            for op in job.operations[:3]:
                print(f"      Op {op.operation_num}: {op.work_center}")
            print()
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return 1
    
    # Test 2: Get work centers
    print("-" * 70)
    print("TEST 2: Work Centers")
    print("-" * 70)
    
    print(f"Available work centers: {', '.join(overview.work_centers[:10])}")
    print()
    
    # Test 3: Get queue at a work center (if any exist)
    if overview.work_centers:
        wc = overview.work_centers[0]
        print("-" * 70)
        print(f"TEST 3: Queue at Work Center '{wc}'")
        print("-" * 70)
        
        try:
            queue = await scheduler.get_work_center_queue(wc, limit=5)
            print(f"✅ Operations in queue: {len(queue)}")
            
            for op in queue[:5]:
                print(f"  - Job {op['job']} Op {op['operation_num']}: {op['item']}")
            print()
            
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    # Test 4: Get specific job details (if any jobs exist)
    if overview.jobs:
        job_num = overview.jobs[0].job
        print("-" * 70)
        print(f"TEST 4: Job Details for '{job_num}'")
        print("-" * 70)
        
        try:
            job = await scheduler.get_job_details(job_num)
            
            if job:
                print(f"✅ Job: {job.job}")
                print(f"   Item: {job.item} - {job.item_description}")
                print(f"   Qty: {job.qty_complete}/{job.qty_released} ({job.pct_complete}%)")
                print(f"   Status: {job.status}")
                print(f"   Customer: {job.customer_name or 'N/A'}")
                print(f"   Operations: {len(job.operations)}")
            else:
                print(f"⚠️  Job not found")
            print()
            
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    print("=" * 70)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

