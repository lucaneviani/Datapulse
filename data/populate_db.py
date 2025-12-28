#!/usr/bin/env python3
"""
Database Population Script

Imports demo data from superstore_orders.csv into the SQLite database.
Handles duplicate records gracefully by checking existing data.

Usage:
    python data/populate_db.py

Copyright (c) 2024 Luca Neviani
Licensed under the MIT License
"""

import pandas as pd
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from sqlalchemy.orm import sessionmaker
from sqlalchemy import inspect
from backend.models import create_database, Customer, Product, Order, OrderItem
from datetime import datetime


def get_existing_ids(session, model):
    """Fetch existing primary keys from a table."""
    return {row[0] for row in session.query(model.id).all()}


def main():
    """Main population logic with duplicate handling."""
    engine = create_database()
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Check if data already exists
    inspector = inspect(engine)
    if 'customers' in inspector.get_table_names():
        existing_customers = get_existing_ids(session, Customer)
        existing_products = get_existing_ids(session, Product)
        existing_orders = get_existing_ids(session, Order)
        
        if existing_customers:
            print(f"Database already contains {len(existing_customers)} customers.")
            print("Skipping population to avoid duplicates.")
            print("To repopulate, delete data/database.db first.")
            session.close()
            return
    else:
        existing_customers = set()
        existing_products = set()
        existing_orders = set()
    
    csv_path = os.path.join(script_dir, 'superstore_orders.csv')
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found")
        sys.exit(1)
    
    print("Loading CSV data...")
    df = pd.read_csv(csv_path)
    
    customers = {}
    products = {}
    orders = {}

    print(f"Processing {len(df)} records...")
    
    for idx, row in df.iterrows():
        cust_id = row['Customer ID']
        if cust_id not in customers:
            customer = Customer(
                id=cust_id,
                name=row['Customer Name'],
                segment=row['Segment'],
                country=row['Country'],
                city=row['City'],
                state=row['State'],
                postal_code=str(row['Postal Code']),
                region=row['Region']
            )
            session.add(customer)
            customers[cust_id] = customer

        prod_id = row['Product ID']
        if prod_id not in products:
            product = Product(
                id=prod_id,
                name=row['Product Name'],
                category=row['Category'],
                sub_category=row['Sub-Category']
            )
            session.add(product)
            products[prod_id] = product

        order_id = row['Order ID']
        if order_id not in orders:
            order = Order(
                id=order_id,
                customer_id=cust_id,
                order_date=datetime.strptime(row['Order Date'], '%m/%d/%Y'),
                ship_date=datetime.strptime(row['Ship Date'], '%m/%d/%Y'),
                ship_mode=row['Ship Mode'],
                total=0.0
            )
            session.add(order)
            orders[order_id] = order

        item = OrderItem(
            order_id=order_id,
            product_id=prod_id,
            quantity=int(row['Quantity']),
            sales=float(row['Sales']),
            discount=float(row['Discount']),
            profit=float(row['Profit'])
        )
        session.add(item)

        # Aggiorna total ordine
        orders[order_id].total += float(row['Sales'])
    
    session.commit()
    session.close()
    
    print(f"Database populated successfully!")
    print(f"  - Customers: {len(customers)}")
    print(f"  - Products: {len(products)}")
    print(f"  - Orders: {len(orders)}")


if __name__ == "__main__":
    main()