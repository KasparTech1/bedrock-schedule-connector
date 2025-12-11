#!/usr/bin/env python3
"""
Test Bedrock Connectivity
=========================

Quick script to validate Mongoose REST API connectivity with the KAI Labs
credentials. Run this to confirm we can access Bedrock data before
requesting additional permissions.

Usage:
    python scripts/test_bedrock_connectivity.py
    
    # Or with uv
    uv run python scripts/test_bedrock_connectivity.py
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kai_erp.connectors.bedrock_jobs_test import (
    BedrockJobsTestConnector,
    create_config_from_credentials
)


async def main():
    print("=" * 60)
    print("BEDROCK MONGOOSE REST API CONNECTIVITY TEST")
    print("=" * 60)
    print()
    
    # Create connector with credentials
    config = create_config_from_credentials()
    connector = BedrockJobsTestConnector(config)
    
    print(f"Tenant ID: {config.tenant_id}")
    print(f"ION API URL: {config.ion_api_url}")
    print(f"Token URL: {config.token_url}")
    print()
    
    # Debug: Try different header variations
    print("-" * 60)
    print("STEP 0: Testing Different Header Combinations")
    print("-" * 60)
    print()
    
    try:
        await connector.debug_header_variations("SLItems", ["Item", "Description"])
    except Exception as e:
        print(f"Header variation test failed: {e}")
    
    print("-" * 60)
    print("STEP 0b: Raw Response with Best Headers")
    print("-" * 60)
    print()
    
    try:
        debug_result = await connector.debug_raw_query("SLItems", ["Item", "Description"])
        print(f"Status: {debug_result['status_code']}")
        print(f"URL: {debug_result['url']}")
        print(f"Raw Response:")
        print(debug_result['raw_text'][:1000])
        print()
        
        # Check for permission error
        if debug_result['parsed']:
            if not debug_result['parsed'].get('Success', True):
                msg = debug_result['parsed'].get('Message', '')
                if 'privilege' in msg.lower():
                    print("⚠️  PERMISSION ISSUE DETECTED!")
                    print("   The SERVICE ACCOUNT needs IDO permissions.")
                    print("   (User account kai_conference@kasparcompanies.com has them,")
                    print("   but the service account in the ionapi file does not)")
                    print()
    except Exception as e:
        print(f"Debug query failed: {e}")
    
    # Run connectivity test
    print("-" * 60)
    print("STEP 1: Testing OAuth2 Token & IDO Access")
    print("-" * 60)
    print()
    
    results = await connector.test_connectivity()
    
    print()
    print("-" * 60)
    print("STEP 2: Testing Active Jobs Query")
    print("-" * 60)
    print()
    
    try:
        jobs = await connector.get_active_jobs(limit=5)
        print(f"Found {len(jobs)} active jobs:")
        print()
        
        for job in jobs[:5]:
            job_num = job.get("Job", "?")
            item = job.get("Item", "?")
            desc = job.get("ItemDescription", "")[:30]
            pct = job.get("PctComplete", 0)
            print(f"  Job {job_num}: {item} - {desc}... ({pct}% complete)")
        
        print()
        print("✅ Active jobs query successful!")
        
    except Exception as e:
        print(f"❌ Active jobs query failed: {e}")
    
    print()
    print("-" * 60)
    print("SUMMARY")
    print("-" * 60)
    print()
    
    if results["token_acquired"]:
        print("✅ OAuth2 Authentication: WORKING")
    else:
        print("❌ OAuth2 Authentication: FAILED")
    
    # Count successful IDOs
    successful = sum(1 for v in results["idos_tested"].values() if v.get("success"))
    total = len(results["idos_tested"])
    print(f"✅ IDO Access: {successful}/{total} IDOs accessible")
    
    print()
    print("IDO Status:")
    for ido, status in results["idos_tested"].items():
        if status.get("success"):
            print(f"  ✅ {ido}: {status.get('record_count', 0)} records")
        else:
            print(f"  ❌ {ido}: {status.get('error', 'Unknown error')}")
    
    print()
    print("=" * 60)
    
    if results["success"] and successful == total:
        print("🎉 ALL TESTS PASSED - Ready to build connectors!")
        print("=" * 60)
        return 0
    else:
        print("⚠️  Some tests failed - check errors above")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

