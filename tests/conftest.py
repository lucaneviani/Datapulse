"""
DataPulse Test Configuration

Shared pytest fixtures and configuration.
"""

import os
import sys

import pytest

# Add project path to PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_db_schema():
    """Sample database schema for testing."""
    return """
    customers(id, name, segment, country, city, state, postal_code, region)
    products(id, name, category, sub_category)
    orders(id, customer_id, order_date, ship_date, ship_mode, total)
    order_items(id, order_id, product_id, quantity, sales, discount, profit)
    """


@pytest.fixture
def valid_sql_queries():
    """List of valid SQL queries for testing."""
    return [
        "SELECT * FROM customers",
        "SELECT COUNT(*) FROM orders",
        "SELECT name, region FROM customers WHERE segment = 'Consumer'",
        "SELECT c.name, SUM(o.total) FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.name",
    ]


@pytest.fixture
def invalid_sql_queries():
    """List of invalid (dangerous) SQL queries for testing."""
    return [
        "INSERT INTO customers VALUES (1, 'Test')",
        "UPDATE customers SET name = 'Hacked'",
        "DELETE FROM customers",
        "DROP TABLE customers",
        "ALTER TABLE customers ADD COLUMN hack TEXT",
        "TRUNCATE TABLE orders",
    ]


@pytest.fixture
def sample_questions():
    """Sample questions for testing."""
    return [
        "How many customers are there?",
        "What are the total sales by region?",
        "List the top 5 products by sales",
        "Show orders from last month",
        "Which customer has the highest total orders?",
    ]
