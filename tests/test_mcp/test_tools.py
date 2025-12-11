"""
Tests for MCP Tools
===================
"""

import pytest

from kai_erp.mcp.tools import (
    ALL_TOOLS,
    PRODUCTION_SCHEDULE_TOOL,
    OPEN_ORDERS_TOOL,
    CUSTOMER_SEARCH_TOOL,
    INVENTORY_STATUS_TOOL,
    ORDER_AVAILABILITY_TOOL,
    get_tool_by_name,
    get_tool_schemas,
)


class TestToolDefinitions:
    """Tests for tool definitions."""
    
    def test_all_tools_defined(self):
        """All expected tools should be defined."""
        assert len(ALL_TOOLS) == 5
        
        tool_names = [t.name for t in ALL_TOOLS]
        assert "get_production_schedule" in tool_names
        assert "get_open_orders" in tool_names
        assert "search_customers" in tool_names
        assert "get_inventory_status" in tool_names
        assert "get_order_availability" in tool_names
    
    def test_production_schedule_tool(self):
        """Test production schedule tool definition."""
        tool = PRODUCTION_SCHEDULE_TOOL
        
        assert tool.name == "get_production_schedule"
        assert "production" in tool.description.lower()
        
        param_names = [p.name for p in tool.parameters]
        assert "work_center" in param_names
        assert "job" in param_names
        assert "include_completed" in param_names
        
        # work_center should be optional
        wc_param = next(p for p in tool.parameters if p.name == "work_center")
        assert wc_param.required is False
    
    def test_open_orders_tool(self):
        """Test open orders tool definition."""
        tool = OPEN_ORDERS_TOOL
        
        assert tool.name == "get_open_orders"
        
        param_names = [p.name for p in tool.parameters]
        assert "customer" in param_names
        assert "days_out" in param_names
    
    def test_customer_search_tool(self):
        """Test customer search tool definition."""
        tool = CUSTOMER_SEARCH_TOOL
        
        assert tool.name == "search_customers"
        
        # query should be required
        query_param = next(p for p in tool.parameters if p.name == "query")
        assert query_param.required is True
    
    def test_inventory_status_tool(self):
        """Test inventory status tool definition."""
        tool = INVENTORY_STATUS_TOOL
        
        assert tool.name == "get_inventory_status"
        
        param_names = [p.name for p in tool.parameters]
        assert "item" in param_names
        assert "warehouse" in param_names
        assert "low_stock_only" in param_names

    def test_order_availability_tool(self):
        """Test order availability tool definition."""
        tool = ORDER_AVAILABILITY_TOOL
        assert tool.name == "get_order_availability"


class TestToolLookup:
    """Tests for tool lookup functions."""
    
    def test_get_tool_by_name_exists(self):
        """Test getting existing tool by name."""
        tool = get_tool_by_name("get_production_schedule")
        
        assert tool is not None
        assert tool.name == "get_production_schedule"
    
    def test_get_tool_by_name_not_found(self):
        """Test getting non-existent tool."""
        tool = get_tool_by_name("nonexistent_tool")
        
        assert tool is None


class TestToolSchemas:
    """Tests for MCP tool schema generation."""
    
    def test_get_tool_schemas_format(self):
        """Test schema format matches MCP spec."""
        schemas = get_tool_schemas()
        
        assert len(schemas) == 5
        
        for schema in schemas:
            # Required fields
            assert "name" in schema
            assert "description" in schema
            assert "inputSchema" in schema
            
            # Input schema structure
            input_schema = schema["inputSchema"]
            assert input_schema["type"] == "object"
            assert "properties" in input_schema
            assert "required" in input_schema
    
    def test_production_schedule_schema(self):
        """Test production schedule tool schema."""
        schemas = get_tool_schemas()
        
        schema = next(s for s in schemas if s["name"] == "get_production_schedule")
        
        props = schema["inputSchema"]["properties"]
        
        # Check work_center property
        assert "work_center" in props
        assert props["work_center"]["type"] == "string"
        
        # Check include_completed default
        assert "include_completed" in props
        assert props["include_completed"]["default"] is False
    
    def test_required_parameters(self):
        """Test required parameters are correctly marked."""
        schemas = get_tool_schemas()
        
        # search_customers has required query param
        customer_schema = next(s for s in schemas if s["name"] == "search_customers")
        assert "query" in customer_schema["inputSchema"]["required"]
        
        # get_production_schedule has no required params
        prod_schema = next(s for s in schemas if s["name"] == "get_production_schedule")
        assert prod_schema["inputSchema"]["required"] == []
