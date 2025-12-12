"""Utility functions for Bedrock Scheduler."""
from typing import Any
from datetime import date, datetime


def clean_str(value: Any) -> str:
    """Clean string value - strip whitespace."""
    if value is None:
        return ""
    return str(value).strip()


def parse_float(value: Any) -> float:
    """Parse float value safely."""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def parse_syteline_date(date_str: str) -> date | None:
    """
    Parse SyteLine date format.
    
    SyteLine dates can be in various formats:
    - "20251022 0" (YYYYMMDD with suffix)
    - "2025-10-22"
    - "2025-10-22T00:00:00"
    - "10/22/2025"
    """
    if not date_str:
        return None
    
    date_str = date_str.strip()
    
    # Handle "YYYYMMDD 0" format (SyteLine standard)
    if " " in date_str and len(date_str.split()[0]) == 8:
        try:
            return datetime.strptime(date_str.split()[0], "%Y%m%d").date()
        except ValueError:
            pass
    
    # Try various formats
    for fmt in ["%Y%m%d", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y"]:
        try:
            return datetime.strptime(date_str[:10], fmt).date()
        except ValueError:
            continue
    
    return None


def format_date(date_str: str) -> str | None:
    """Format a SyteLine date string to ISO format."""
    parsed = parse_syteline_date(date_str)
    return parsed.isoformat() if parsed else None


def parse_bed_length(drawing: str) -> int:
    """Parse bed length from drawing number (first 1-2 digits)."""
    if not drawing:
        return 0
    
    # Try to extract leading digits
    digits = ""
    for char in drawing:
        if char.isdigit():
            digits += char
        else:
            break
    
    if digits and len(digits) <= 2:
        try:
            return int(digits)
        except ValueError:
            pass
    
    return 0


def parse_bed_type(model: str) -> str:
    """
    Parse bed type from model/drawing number or item code.
    
    Examples:
    - "14G-7" -> Granite (ends with G before dash)
    - "23D" -> Diamond (ends with D)
    - "14GP-7" or "6GP" -> Granite+ (contains GP)
    - "8M-9" -> Marble (ends with M before dash)
    - "14D-7" -> Diamond
    """
    if not model:
        return "Other"
    
    model_upper = model.upper().strip()
    
    # Check for Granite+ first (GP patterns - must check before G)
    if "GP" in model_upper:
        return "Granite+"
    
    # Get the prefix before first dash (e.g., "14G" from "14G-7")
    prefix = model_upper.split("-")[0] if "-" in model_upper else model_upper
    
    # Remove any trailing numbers from prefix for items like "23D"
    # But keep the letter suffix
    stripped_prefix = prefix.rstrip("0123456789")
    if not stripped_prefix:
        stripped_prefix = prefix
    
    # Check last character of prefix
    last_char = stripped_prefix[-1] if stripped_prefix else ""
    
    if last_char == "D":
        return "Diamond"
    elif last_char == "G":
        return "Granite"
    elif last_char == "M":
        return "Marble"
    elif last_char == "L":
        return "Limestone"
    elif last_char == "P":
        return "Platform"
    elif last_char == "O":
        return "Onyx"
    elif last_char == "S":
        return "Slate"
    elif "QU" in model_upper or (prefix.startswith("Q") and len(prefix) > 1):
        return "Quad"
    
    return "Other"

