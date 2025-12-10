"""Seed test data for the test database."""

import logging
from datetime import datetime, timedelta
import random

from .engine import TestDatabaseEngine

logger = logging.getLogger(__name__)

# Sample data generators
WORK_CENTERS = [
    ("WELD-01", "Welding Station 1"),
    ("WELD-02", "Welding Station 2"),
    ("CUT-01", "Cutting Station"),
    ("PAINT-01", "Paint Booth 1"),
    ("ASSY-01", "Assembly Line 1"),
    ("ASSY-02", "Assembly Line 2"),
    ("QC-01", "Quality Control"),
    ("SHIP-01", "Shipping"),
]

ITEMS = [
    ("BED-STD-8", "Standard 8ft Truck Bed"),
    ("BED-STD-6", "Standard 6ft Truck Bed"),
    ("BED-HD-8", "Heavy Duty 8ft Truck Bed"),
    ("BED-HD-6", "Heavy Duty 6ft Truck Bed"),
    ("LINER-STD", "Standard Bed Liner"),
    ("LINER-HD", "Heavy Duty Bed Liner"),
    ("RAIL-STD", "Standard Side Rails"),
    ("RAIL-HD", "Heavy Duty Side Rails"),
    ("TG-STD", "Standard Tailgate"),
    ("TG-HD", "Heavy Duty Tailgate"),
]

CUSTOMERS = [
    ("C001", "ABC Trucking Co", "123 Main St", "Dallas", "TX", "75201", "214-555-0101", "John Smith", "john@abctrucking.com"),
    ("C002", "Smith Farms LLC", "456 Country Rd", "Austin", "TX", "78701", "512-555-0102", "Bob Smith", "bob@smithfarms.com"),
    ("C003", "Johnson Construction", "789 Builder Ave", "Houston", "TX", "77001", "713-555-0103", "Mike Johnson", "mike@johnsonconstruction.com"),
    ("C004", "Texas Auto Parts", "321 Commerce Blvd", "San Antonio", "TX", "78201", "210-555-0104", "Lisa Chen", "lisa@texasautoparts.com"),
    ("C005", "Mountain Equipment", "555 Highland Dr", "Denver", "CO", "80201", "303-555-0105", "Sarah Davis", "sarah@mountainequipment.com"),
    ("C006", "Midwest Fleet Services", "888 Industrial Way", "Chicago", "IL", "60601", "312-555-0106", "Tom Wilson", "tom@midwestfleet.com"),
    ("C007", "Pacific Northwest Motors", "999 Harbor Blvd", "Seattle", "WA", "98101", "206-555-0107", "Amy Lee", "amy@pnwmotors.com"),
    ("C008", "Southern States Supply", "111 Supply Dr", "Atlanta", "GA", "30301", "404-555-0108", "James Brown", "james@southernstates.com"),
]


def seed_test_data(engine: TestDatabaseEngine, num_jobs: int = 20, num_orders: int = 15) -> None:
    """Seed the test database with sample data.

    Args:
        engine: TestDatabaseEngine instance (must be connected).
        num_jobs: Number of jobs to create.
        num_orders: Number of sales orders to create.
    """
    logger.info("Seeding test database...")

    # Create tables first
    engine.create_tables()
    engine.clear_all_data()

    # Seed Items
    for item_id, description in ITEMS:
        engine.execute(
            "INSERT INTO Items (Item, Description, UM, ProductCode, Stat) VALUES (?, ?, ?, ?, ?)",
            (item_id, description, "EA", item_id.split("-")[0], "A"),
        )

    # Seed Customers
    for cust in CUSTOMERS:
        engine.execute(
            """INSERT INTO Customers 
               (CustNum, Name, Addr1, City, State, Zip, Phone, Contact, Email, CustType, Stat)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (*cust, "DIST", "A"),
        )

    # Seed Jobs with Job Routes
    today = datetime.now()
    for i in range(1, num_jobs + 1):
        job_num = f"J-{2024000 + i}"
        item = random.choice(ITEMS)
        customer = random.choice(CUSTOMERS)
        qty = random.randint(5, 50)
        qty_complete = random.randint(0, qty) if random.random() > 0.3 else 0
        status = "C" if qty_complete >= qty else ("S" if qty_complete > 0 else "R")
        start_date = today + timedelta(days=random.randint(-5, 10))
        due_date = start_date + timedelta(days=random.randint(3, 14))

        engine.execute(
            """INSERT INTO Jobs 
               (Job, Suffix, Item, Description, QtyReleased, QtyComplete, CustNum, CustName, Status, OrderDate, DueDate)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (job_num, 0, item[0], item[1], qty, qty_complete, customer[0], customer[1],
             status, start_date.strftime("%Y-%m-%d"), due_date.strftime("%Y-%m-%d")),
        )

        # Add 3-5 operations per job
        num_ops = random.randint(3, 5)
        selected_wcs = random.sample(WORK_CENTERS, num_ops)
        op_date = start_date

        for op_num, (wc_code, wc_desc) in enumerate(selected_wcs, start=10):
            op_status = "C" if random.random() > 0.6 else ("S" if random.random() > 0.5 else "R")
            op_end = op_date + timedelta(days=random.randint(1, 3))

            engine.execute(
                """INSERT INTO JobRoutes 
                   (Job, Suffix, OperNum, Wc, WcDescription, StartDate, EndDate, Status, RunHrsRemaining)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (job_num, 0, op_num * 10, wc_code, wc_desc,
                 op_date.strftime("%Y-%m-%d"), op_end.strftime("%Y-%m-%d"),
                 op_status, random.uniform(0, 8) if op_status != "C" else 0),
            )
            op_date = op_end

    # Seed Sales Orders
    for i in range(1, num_orders + 1):
        co_num = f"SO-{2024000 + i}"
        customer = random.choice(CUSTOMERS)
        order_date = today - timedelta(days=random.randint(1, 30))

        engine.execute(
            "INSERT INTO Cos (CoNum, CustNum, CustName, OrderDate, Stat) VALUES (?, ?, ?, ?, ?)",
            (co_num, customer[0], customer[1], order_date.strftime("%Y-%m-%d"), "O"),
        )

        # Add 1-4 line items per order
        num_lines = random.randint(1, 4)
        selected_items = random.sample(ITEMS, min(num_lines, len(ITEMS)))

        for line_num, (item_id, item_desc) in enumerate(selected_items, start=1):
            qty_ordered = random.randint(2, 20)
            qty_shipped = random.randint(0, qty_ordered) if random.random() > 0.4 else 0
            due_date = order_date + timedelta(days=random.randint(7, 30))

            engine.execute(
                """INSERT INTO CoItems 
                   (CoNum, CoLine, Item, Description, QtyOrdered, QtyShipped, DueDate, Stat)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (co_num, line_num, item_id, item_desc, qty_ordered, qty_shipped,
                 due_date.strftime("%Y-%m-%d"), "O" if qty_shipped < qty_ordered else "C"),
            )

    # Seed Inventory
    warehouses = ["MAIN", "DIST", "WIP"]
    locations = ["A1", "A2", "B1", "B2", "C1"]

    for item_id, _ in ITEMS:
        for whse in warehouses:
            loc = random.choice(locations)
            qty_on_hand = random.randint(0, 100)
            qty_reserved = random.randint(0, min(qty_on_hand, 30))
            safety_stock = random.randint(5, 20)

            engine.execute(
                """INSERT INTO ItemLocs 
                   (Item, Whse, Loc, QtyOnHand, QtyRsvd, SafetyStockQty)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (item_id, whse, loc, qty_on_hand, qty_reserved, safety_stock),
            )

    engine.commit()
    logger.info(f"Seeded {num_jobs} jobs, {num_orders} orders, {len(ITEMS)} items, {len(CUSTOMERS)} customers")
