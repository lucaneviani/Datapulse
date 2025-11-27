import pandas as pd
import sys
sys.path.append('..')
from sqlalchemy.orm import sessionmaker
from backend.models import create_database, Customer, Product, Order, OrderItem
from datetime import datetime

# Crea DB
engine = create_database()
Session = sessionmaker(bind=engine)
session = Session()

# Carica CSV
df = pd.read_csv('../data/superstore_orders.csv')

# Dizionari per evitare duplicati
customers = {}
products = {}
orders = {}

for _, row in df.iterrows():
    # Crea Customer se non esiste
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

    # Crea Product se non esiste
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

    # Crea Order se non esiste (raggruppa per Order ID)
    order_id = row['Order ID']
    if order_id not in orders:
        order = Order(
            id=order_id,
            customer_id=cust_id,
            order_date=datetime.strptime(row['Order Date'], '%m/%d/%Y'),
            ship_date=datetime.strptime(row['Ship Date'], '%m/%d/%Y'),
            ship_mode=row['Ship Mode'],
            total=0.0  # Calcolato dopo
        )
        session.add(order)
        orders[order_id] = order

    # Aggiungi OrderItem
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
print("DB popolato con successo!")