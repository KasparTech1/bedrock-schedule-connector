"""
Security Utilities
==================

Input validation and sanitization utilities to prevent injection attacks.
"""

import re
from typing import Any


class ODataSanitizer:
    """
    Sanitizer for OData filter expressions.
    
    OData uses single quotes for string literals and has specific escape rules.
    This sanitizer escapes user input to prevent OData injection attacks.
    
    Example:
        sanitizer = ODataSanitizer()
        safe_value = sanitizer.escape_string("O'Malley")  # Returns "O''Malley"
        filter_expr = sanitizer.build_filter("Name", "like", "O'Malley")
    """
    
    # Pattern to detect potentially dangerous OData operators/functions
    DANGEROUS_PATTERNS = re.compile(
        r"(\b(or|and|not|eq|ne|gt|ge|lt|le|add|sub|mul|div|mod|contains|"
        r"startswith|endswith|substringof|tolower|toupper|trim|length|"
        r"indexof|replace|substring)\b|\(|\)|')",
        re.IGNORECASE
    )
    
    @staticmethod
    def escape_string(value: str) -> str:
        """
        Escape a string value for use in OData filter expressions.
        
        In OData, single quotes are escaped by doubling them.
        
        Args:
            value: The string value to escape
            
        Returns:
            Escaped string safe for OData filters
            
        Example:
            >>> ODataSanitizer.escape_string("O'Malley")
            "O''Malley"
        """
        if not isinstance(value, str):
            value = str(value)
        # Escape single quotes by doubling them
        return value.replace("'", "''")
    
    @staticmethod
    def validate_identifier(value: str) -> bool:
        """
        Validate that a value is a safe identifier (column name, etc.).
        
        Args:
            value: The identifier to validate
            
        Returns:
            True if safe, False otherwise
        """
        if not value:
            return False
        # Allow alphanumeric, underscore, hyphen (common in SyteLine IDs)
        return bool(re.match(r'^[\w\-]+$', value))
    
    @classmethod
    def build_equals_filter(cls, field: str, value: str) -> str:
        """
        Build a safe OData equals filter expression.
        
        Args:
            field: Field name (must be a valid identifier)
            value: Value to compare against
            
        Returns:
            Safe OData filter expression
            
        Example:
            >>> ODataSanitizer.build_equals_filter("Job", "J-1234")
            "Job='J-1234'"
        """
        if not cls.validate_identifier(field):
            raise ValueError(f"Invalid field name: {field}")
        safe_value = cls.escape_string(value)
        return f"{field}='{safe_value}'"
    
    @classmethod
    def build_like_filter(cls, field: str, value: str, position: str = "contains") -> str:
        """
        Build a safe OData LIKE filter expression.
        
        Args:
            field: Field name (must be a valid identifier)
            value: Value to search for
            position: 'contains', 'startswith', or 'endswith'
            
        Returns:
            Safe OData filter expression
            
        Example:
            >>> ODataSanitizer.build_like_filter("Name", "Acme", "contains")
            "Name like '%Acme%'"
        """
        if not cls.validate_identifier(field):
            raise ValueError(f"Invalid field name: {field}")
        
        safe_value = cls.escape_string(value)
        
        if position == "contains":
            return f"{field} like '%{safe_value}%'"
        elif position == "startswith":
            return f"{field} like '{safe_value}%'"
        elif position == "endswith":
            return f"{field} like '%{safe_value}'"
        else:
            raise ValueError(f"Invalid position: {position}")
    
    @classmethod
    def build_or_filter(cls, conditions: list[str]) -> str:
        """
        Combine multiple filter conditions with OR.
        
        Args:
            conditions: List of filter conditions
            
        Returns:
            Combined filter expression
        """
        if not conditions:
            return ""
        if len(conditions) == 1:
            return conditions[0]
        return "(" + " or ".join(conditions) + ")"
    
    @classmethod
    def build_and_filter(cls, conditions: list[str]) -> str:
        """
        Combine multiple filter conditions with AND.
        
        Args:
            conditions: List of filter conditions
            
        Returns:
            Combined filter expression
        """
        if not conditions:
            return ""
        if len(conditions) == 1:
            return conditions[0]
        return " and ".join(conditions)


def sanitize_sql_identifier(value: str) -> str:
    """
    Sanitize a value for use as a SQL identifier (table name, column name).
    
    Only allows alphanumeric characters and underscores.
    Raises ValueError for invalid identifiers.
    
    Args:
        value: The identifier to sanitize
        
    Returns:
        The sanitized identifier
        
    Raises:
        ValueError: If the identifier contains invalid characters
    """
    if not value:
        raise ValueError("Identifier cannot be empty")
    if not re.match(r'^[\w]+$', value):
        raise ValueError(f"Invalid SQL identifier: {value}")
    return value


def validate_filter_value(value: Any, max_length: int = 200) -> str:
    """
    Validate and sanitize a filter value.
    
    Args:
        value: The value to validate
        max_length: Maximum allowed length
        
    Returns:
        Validated string value
        
    Raises:
        ValueError: If validation fails
    """
    if value is None:
        raise ValueError("Filter value cannot be None")
    
    str_value = str(value)
    
    if len(str_value) > max_length:
        raise ValueError(f"Filter value too long (max {max_length} characters)")
    
    # Check for null bytes which could cause issues
    if '\x00' in str_value:
        raise ValueError("Filter value contains invalid characters")
    
    return str_value

