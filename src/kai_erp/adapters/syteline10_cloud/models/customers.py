"""Customer-related data models."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Customer:
    """A Bedrock customer record."""
    cust_num: str
    name: str
    addr1: Optional[str]
    addr2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    country: Optional[str]
    phone: Optional[str]
    contact: Optional[str]
    email: Optional[str]
    cust_type: Optional[str]
    status: str  # A=Active, I=Inactive


@dataclass
class CustomerSearchResult:
    """Result of a customer search."""
    total_count: int
    customers: list[Customer]
    fetched_at: datetime

