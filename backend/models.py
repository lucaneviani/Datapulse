"""
DataPulse Database Models

SQLAlchemy ORM models for the demo Superstore dataset.

Tables:
    - customers: Customer records with demographics
    - products: Product catalog with categories
    - orders: Order headers with dates and totals
    - order_items: Order line items with sales data

Copyright (c) 2024 Luca Neviani
Licensed under the MIT License
"""

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Customer(Base):
    """Customer entity with geographic and segment information."""

    __tablename__ = "customers"
    id = Column(String, primary_key=True)
    name = Column(String)
    segment = Column(String)
    country = Column(String)
    city = Column(String)
    state = Column(String)
    postal_code = Column(String)
    region = Column(String)


class Product(Base):
    """Product entity with category hierarchy."""

    __tablename__ = "products"
    id = Column(String, primary_key=True)
    name = Column(String)
    category = Column(String)
    sub_category = Column(String)


class Order(Base):
    """Order header with dates and shipping information."""

    __tablename__ = "orders"
    id = Column(String, primary_key=True)
    customer_id = Column(String, ForeignKey("customers.id"))
    order_date = Column(DateTime)
    ship_date = Column(DateTime)
    ship_mode = Column(String)
    total = Column(Float)
    customer = relationship("Customer")


class OrderItem(Base):
    """Order line item with sales, quantity, and profit data."""

    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String, ForeignKey("orders.id"))
    product_id = Column(String, ForeignKey("products.id"))
    quantity = Column(Integer)
    sales = Column(Float)
    discount = Column(Float)
    profit = Column(Float)
    order = relationship("Order")
    product = relationship("Product")


def create_database():
    """Initialize the SQLite database and create all tables."""
    import os

    db_path = os.path.join(os.path.dirname(__file__), "../data/database.db")
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    return engine
