"""
Test script for Demo MCP Server.

Run this to test MCP tool calls against the live demo environment.
"""

import asyncio
import json
from kai_erp.mcp.demo_server import DemoMcpServer


async def test_mcp_server():
    """Test the demo MCP server with various tool calls."""
    
    print("=" * 60)
    print("🚀 Testing Demo MCP Server")
    print("=" * 60)
    
    async with DemoMcpServer() as server:
        # Test 1: Initialize
        print("\n📡 Test 1: Initialize")
        print("-" * 40)
        response = await server.handle_message({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        })
        print(f"Server: {response['result']['name']} v{response['result']['version']}")
        print(f"Capabilities: {response['result']['capabilities']}")
        
        # Test 2: List Tools
        print("\n🔧 Test 2: List Tools")
        print("-" * 40)
        response = await server.handle_message({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        })
        tools = response['result']['tools']
        print(f"Available tools ({len(tools)}):")
        for tool in tools:
            print(f"  • {tool['name']}")
        
        # Test 3: Get Items (no filter)
        print("\n📦 Test 3: get_syteline_items (no filter)")
        print("-" * 40)
        response = await server.handle_message({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_syteline_items",
                "arguments": {"limit": 5}
            }
        })
        result = response['result']
        if result.get('success'):
            print(f"✅ Success! Retrieved {result['data']['count']} items")
            print(f"   Source: {result['data']['source']}")
            for item in result['data']['items'][:3]:
                print(f"   • {item.get('Item')}: {item.get('Description', 'N/A')[:40]}...")
        else:
            print(f"❌ Error: {result.get('error', {}).get('message')}")
        
        # Test 4: Get Items (with filter)
        print("\n📦 Test 4: get_syteline_items (item='30')")
        print("-" * 40)
        response = await server.handle_message({
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "get_syteline_items",
                "arguments": {"item": "30", "limit": 5}
            }
        })
        result = response['result']
        if result.get('success'):
            print(f"✅ Success! Retrieved {result['data']['count']} items matching '30'")
            for item in result['data']['items']:
                print(f"   • {item.get('Item')}: {item.get('Description', 'N/A')[:40]}...")
        else:
            print(f"❌ Error: {result.get('error', {}).get('message')}")
        
        # Test 5: Get Customers
        print("\n👥 Test 5: get_syteline_customers")
        print("-" * 40)
        response = await server.handle_message({
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "get_syteline_customers",
                "arguments": {"limit": 5}
            }
        })
        result = response['result']
        if result.get('success'):
            print(f"✅ Success! Retrieved {result['data']['count']} customers")
            for cust in result['data']['customers'][:3]:
                print(f"   • {cust.get('CustNum')}: {cust.get('Name', 'N/A')}")
        else:
            print(f"❌ Error: {result.get('error', {}).get('message')}")
        
        # Test 6: Query IDO (advanced)
        print("\n🔍 Test 6: query_syteline_ido (SLJobs)")
        print("-" * 40)
        response = await server.handle_message({
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "query_syteline_ido",
                "arguments": {
                    "ido_name": "SLJobs",
                    "properties": ["Job", "Item", "JobQty", "Stat"],
                    "limit": 5
                }
            }
        })
        result = response['result']
        if result.get('success'):
            print(f"✅ Success! Retrieved {result['data']['count']} jobs")
            for job in result['data']['records'][:3]:
                print(f"   • Job {job.get('Job')}: {job.get('Item')} (Qty: {job.get('JobQty')})")
        else:
            print(f"❌ Error: {result.get('error', {}).get('message')}")
        
        print("\n" + "=" * 60)
        print("✅ All MCP tests completed!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_mcp_server())
