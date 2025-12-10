"""
KAI ERP Connector
=================

A three-layer system for accessing SyteLine 10 CloudSuite data:

- Layer 1: Data Sources (REST APIs + Data Lake)
- Layer 2: Connectors (Business logic)
- Layer 3: MCP Server (AI interface)

Usage:
    from kai_erp.connectors import BedrockOpsScheduler
    from kai_erp.core import RestEngine
    
    async with RestEngine(config) as engine:
        connector = BedrockOpsScheduler(engine)
        result = await connector.execute(filters={"work_center": "WELD-01"})
"""

__version__ = "3.0.0"
__author__ = "Kaspar Companies IT"

# Re-exports will be added as modules are implemented
