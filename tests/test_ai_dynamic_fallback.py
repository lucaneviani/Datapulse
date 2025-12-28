import sys
sys.path.insert(0, "Datapulse")

from backend.ai_service import generate_sql_dynamic, validate_sql_dynamic


def test_generate_sql_dynamic_fallback_count():
    schema = """Table: sales\nColumns: id: INTEGER, total: REAL, product_id: TEXT"""
    tables = ["sales"]
    sql = generate_sql_dynamic("How many sales are there?", schema, tables)
    assert isinstance(sql, str)
    assert sql.strip().upper().startswith("SELECT"), f"unexpected sql: {sql}"
    is_valid, msg = validate_sql_dynamic(sql)
    assert is_valid is True


def test_generate_sql_dynamic_fallback_show():
    schema = """Table: customers\nColumns: id: INTEGER, name: TEXT, region: TEXT"""
    tables = ["customers"]
    sql = generate_sql_dynamic("Show customers", schema, tables)
    assert sql.strip().upper().startswith("SELECT"), sql
    is_valid, msg = validate_sql_dynamic(sql)
    assert is_valid is True
