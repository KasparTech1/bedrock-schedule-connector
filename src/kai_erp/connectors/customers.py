"""
Customer Search Connector
=========================

Customer lookup and information.

Source IDOs:
- SLCustomers: Customer master
- SLCustaddrs: Customer addresses
"""

from typing import Any, Optional

from kai_erp.connectors.base import BaseConnector
from kai_erp.core.types import IDOSpec, RestQuerySpec
from kai_erp.models.customers import Customer, CustomerAddress


class CustomerSearch(BaseConnector[Customer]):
    """
    Customer search connector for looking up customer information.
    
    Supports searching by name, number, city, or state.
    
    Example:
        async with RestEngine(config) as engine:
            search = CustomerSearch(engine)
            result = await search.execute(
                filters={"query": "Acme", "active_only": True}
            )
    """
    
    def get_rest_spec(self, filters: Optional[dict[str, Any]] = None) -> RestQuerySpec:
        """Define REST API access pattern for customer search."""
        
        # Build customer filter
        customer_filter_parts = []
        
        if filters:
            if filters.get("active_only", True):
                customer_filter_parts.append("Stat='A'")
            
            if filters.get("query"):
                query = filters["query"]
                # Search multiple fields
                customer_filter_parts.append(
                    f"(Name like '%{query}%' or CustNum like '%{query}%' "
                    f"or City like '%{query}%' or State like '%{query}%')"
                )
        
        customer_filter = " and ".join(customer_filter_parts) if customer_filter_parts else None
        
        return RestQuerySpec(
            idos=[
                IDOSpec(
                    name="SLCustomers",
                    properties=[
                        "CustNum", "Name", "ContactName", "Phone", "Email",
                        "Addr1", "Addr2", "City", "State", "Zip", "Country",
                        "Stat", "CreditHold", "TermsCode", "CreditLimit"
                    ],
                    filter=customer_filter
                ),
                IDOSpec(
                    name="SLCustaddrs",
                    properties=[
                        "CustNum", "CustSeq", "Name", "Addr1", "Addr2",
                        "City", "State", "Zip", "Country"
                    ]
                )
            ],
            join_sql=self._build_join_sql(filters)
        )
    
    def _build_join_sql(self, filters: Optional[dict[str, Any]] = None) -> str:
        """Build the DuckDB join SQL."""
        sql = """
            SELECT 
                c.CustNum as CustomerNum,
                c.Name,
                c.ContactName,
                c.Phone,
                c.Email,
                c.Addr1 as Address1,
                c.Addr2 as Address2,
                c.City,
                c.State,
                c.Zip as ZipCode,
                c.Country,
                c.Stat as Status,
                c.CreditHold,
                c.TermsCode as PaymentTerms,
                c.CreditLimit,
                a.CustSeq as AddressId,
                a.Name as AddrName,
                a.Addr1 as AddrAddress1,
                a.Addr2 as AddrAddress2,
                a.City as AddrCity,
                a.State as AddrState,
                a.Zip as AddrZip,
                a.Country as AddrCountry
                
            FROM SLCustomers c
            LEFT JOIN SLCustaddrs a ON c.CustNum = a.CustNum
        """
        
        where_parts = []
        if filters:
            if filters.get("active_only", True):
                where_parts.append("c.Stat = 'A'")
            if filters.get("query"):
                query = filters["query"]
                where_parts.append(
                    f"(c.Name LIKE '%{query}%' OR c.CustNum LIKE '%{query}%' "
                    f"OR c.City LIKE '%{query}%' OR c.State LIKE '%{query}%')"
                )
        
        if where_parts:
            sql += " WHERE " + " AND ".join(where_parts)
        
        sql += " ORDER BY c.Name"
        
        return sql
    
    def get_lake_query(self, filters: Optional[dict[str, Any]] = None) -> str:
        """Define Data Lake SQL query."""
        return """
            SELECT 
                c.cust_num as CustomerNum,
                c.name as Name,
                c.contact_name as ContactName,
                c.phone as Phone,
                c.city as City,
                c.state as State
                
            FROM SYTELINE.customer c
            WHERE c.stat = 'A'
            ORDER BY c.name
        """
    
    async def estimate_volume(self, filters: Optional[dict[str, Any]] = None) -> int:
        """Estimate result count."""
        if filters and filters.get("query"):
            return 20  # Search typically returns few matches
        return 100  # Active customers subset
    
    def transform_result(self, row: dict[str, Any]) -> Customer:
        """Transform query result to Customer model."""
        # Build addresses list if address data present
        addresses = []
        if row.get("AddressId"):
            addresses.append(CustomerAddress(
                address_id=str(row.get("AddressId", "")),
                name=str(row.get("AddrName", "")),
                address_1=str(row.get("AddrAddress1", "")),
                address_2=str(row.get("AddrAddress2", "")),
                city=str(row.get("AddrCity", "")),
                state=str(row.get("AddrState", "")),
                zip_code=str(row.get("AddrZip", "")),
                country=str(row.get("AddrCountry", "US"))
            ))
        
        return Customer(
            customer_num=str(row.get("CustomerNum", "")),
            name=str(row.get("Name", "")),
            contact_name=str(row.get("ContactName", "")),
            phone=str(row.get("Phone", "")),
            email=str(row.get("Email", "")),
            address_1=str(row.get("Address1", "")),
            address_2=str(row.get("Address2", "")),
            city=str(row.get("City", "")),
            state=str(row.get("State", "")),
            zip_code=str(row.get("ZipCode", "")),
            country=str(row.get("Country", "US")),
            active=row.get("Status") == "A",
            credit_hold=bool(row.get("CreditHold")),
            payment_terms=str(row.get("PaymentTerms", "")),
            credit_limit=float(row.get("CreditLimit")) if row.get("CreditLimit") else None,
            addresses=addresses
        )
