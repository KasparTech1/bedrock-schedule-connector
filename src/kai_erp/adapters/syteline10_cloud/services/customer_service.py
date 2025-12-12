"""Customer search service."""
from typing import Optional
from datetime import datetime, timezone

import structlog

from ..mongoose_client import MongooseClient, MongooseConfig
from ..models.customers import Customer, CustomerSearchResult
from ..utils import clean_str

logger = structlog.get_logger(__name__)


class CustomerService:
    """Service for customer search and management."""
    
    def __init__(self, config: MongooseConfig):
        self.config = config
    
    async def search_customers(
        self,
        search_term: Optional[str] = None,
        customer_number: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> CustomerSearchResult:
        """
        Search for Bedrock customers.
        
        Args:
            search_term: Search in name or customer number
            customer_number: Exact customer number match
            city: Filter by city
            state: Filter by state
            status: Filter by status (A=Active, I=Inactive)
            limit: Max customers to return
            
        Returns:
            CustomerSearchResult with matching customers
        """
        async with MongooseClient(self.config) as client:
            # Build filter
            filters = []
            
            if customer_number:
                filters.append(f"CustNum='{customer_number}'")
            
            if city:
                filters.append(f"City LIKE '%{city}%'")
            
            if state:
                filters.append(f"State='{state}'")
            
            if status:
                filters.append(f"Stat='{status}'")
            
            filter_str = " AND ".join(filters) if filters else None
            
            # Fetch customers
            # Note: Using SyteLine standard property names
            raw_customers = await client.query_ido(
                "SLCustomers",
                [
                    "CustNum", "Name", "Addr_1", "Addr_2", "City", "State",
                    "Zip", "Country", "TelexNum", "Contact_1", "CreditHold", "CustType", "Stat"
                ],
                filter_str,
                limit * 2  # Fetch extra for client-side search filter
            )
            
            # Build customer objects
            customers = []
            for cust_data in raw_customers:
                cust_num = clean_str(cust_data.get("CustNum"))
                name = clean_str(cust_data.get("Name"))
                
                # Apply search_term filter (client-side since LIKE may not work well)
                if search_term:
                    search_lower = search_term.lower()
                    if (search_lower not in cust_num.lower() and 
                        search_lower not in name.lower()):
                        continue
                
                customers.append(Customer(
                    cust_num=cust_num,
                    name=name,
                    addr1=clean_str(cust_data.get("Addr_1")) or None,
                    addr2=clean_str(cust_data.get("Addr_2")) or None,
                    city=clean_str(cust_data.get("City")) or None,
                    state=clean_str(cust_data.get("State")) or None,
                    zip_code=clean_str(cust_data.get("Zip")) or None,
                    country=clean_str(cust_data.get("Country")) or None,
                    phone=clean_str(cust_data.get("TelexNum")) or None,  # Phone field
                    contact=clean_str(cust_data.get("Contact_1")) or None,
                    email=None,  # Email may need different property
                    cust_type=clean_str(cust_data.get("CustType")) or None,
                    status=clean_str(cust_data.get("Stat")) or "A",
                ))
            
            # Apply limit
            customers = customers[:limit]
            
            return CustomerSearchResult(
                total_count=len(customers),
                customers=customers,
                fetched_at=datetime.now(timezone.utc),
            )
    
    async def get_customer(self, customer_number: str) -> Optional[Customer]:
        """
        Get a specific customer by number.
        
        Args:
            customer_number: The customer number
            
        Returns:
            Customer if found, None otherwise
        """
        result = await self.search_customers(customer_number=customer_number, limit=1)
        return result.customers[0] if result.customers else None

