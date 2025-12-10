"""
Customer Models
===============

Models for the Customer Search connector.
"""

from typing import Optional

from pydantic import BaseModel, Field


class CustomerAddress(BaseModel):
    """
    A customer address (shipping or billing).
    """
    
    address_id: str = Field(description="Address identifier")
    name: str = Field(default="", description="Address name/attention")
    address_1: str = Field(default="", description="Address line 1")
    address_2: str = Field(default="", description="Address line 2")
    city: str = Field(default="", description="City")
    state: str = Field(default="", description="State/province")
    zip_code: str = Field(default="", description="ZIP/postal code")
    country: str = Field(default="US", description="Country code")
    is_default: bool = Field(default=False, description="Is default address")


class Customer(BaseModel):
    """
    A customer record.
    
    Represents a customer with contact information and addresses.
    
    Example:
        {
            "customer_num": "C-100",
            "name": "Acme Corporation",
            "city": "Dallas",
            "state": "TX",
            "active": true
        }
    """
    
    # Identification
    customer_num: str = Field(description="Customer number")
    name: str = Field(description="Customer name")
    
    # Contact
    contact_name: str = Field(default="", description="Primary contact name")
    phone: str = Field(default="", description="Phone number")
    email: str = Field(default="", description="Email address")
    
    # Primary address
    address_1: str = Field(default="", description="Address line 1")
    address_2: str = Field(default="", description="Address line 2")
    city: str = Field(default="", description="City")
    state: str = Field(default="", description="State/province")
    zip_code: str = Field(default="", description="ZIP/postal code")
    country: str = Field(default="US", description="Country code")
    
    # Status
    active: bool = Field(default=True, description="Is customer active")
    credit_hold: bool = Field(default=False, description="Is customer on credit hold")
    
    # Terms
    payment_terms: str = Field(default="", description="Payment terms code")
    credit_limit: Optional[float] = Field(default=None, description="Credit limit")
    
    # Additional addresses
    addresses: list[CustomerAddress] = Field(
        default_factory=list,
        description="Additional shipping/billing addresses"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "customer_num": "C-100",
                "name": "Acme Corporation",
                "contact_name": "John Smith",
                "phone": "555-123-4567",
                "email": "john@acme.com",
                "city": "Dallas",
                "state": "TX",
                "zip_code": "75201",
                "active": True,
                "credit_hold": False
            }
        }
    }
