from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# Tabella Customers (da Customer ID, Name, etc.)
class Customer(Base):
    __tablename__ = 'customers'
    id = Column(String, primary_key=True)  # Customer ID (stringa unica)
    name = Column(String)  # Customer Name
    segment = Column(String)  # Segment
    country = Column(String)  # Country
    city = Column(String)  # City
    state = Column(String)  # State
    postal_code = Column(String)  # Postal Code
    region = Column(String)  # Region

# Tabella Products (da Product ID, Name, etc.)
class Product(Base):
    __tablename__ = 'products'
    id = Column(String, primary_key=True)  # Product ID
    name = Column(String)  # Product Name
    category = Column(String)  # Category
    sub_category = Column(String)  # Sub-Category

# Tabella Orders (da Order ID, Date, etc.)
class Order(Base):
    __tablename__ = 'orders'
    id = Column(String, primary_key=True)  # Order ID
    customer_id = Column(String, ForeignKey('customers.id'))
    order_date = Column(DateTime)  # Order Date
    ship_date = Column(DateTime)  # Ship Date
    ship_mode = Column(String)  # Ship Mode
    total = Column(Float)  # Calcolato come sum(Sales) per ordine
    customer = relationship('Customer')

# Tabella OrderItems (ogni riga CSV è un item)
class OrderItem(Base):
    __tablename__ = 'order_items'
    id = Column(Integer, primary_key=True, autoincrement=True)  # ID auto
    order_id = Column(String, ForeignKey('orders.id'))
    product_id = Column(String, ForeignKey('products.id'))
    quantity = Column(Integer)  # Quantity
    sales = Column(Float)  # Sales (prezzo per item)
    discount = Column(Float)  # Discount
    profit = Column(Float)  # Profit
    order = relationship('Order')
    product = relationship('Product')

# Funzione per creare DB
def create_database():
    import os
    db_path = os.path.join(os.path.dirname(__file__), '../data/database.db')
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    return engine