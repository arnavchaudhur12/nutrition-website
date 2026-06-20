from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def run_startup_migrations(engine: Engine) -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "orders" not in tables:
        return

    existing_columns = {column["name"] for column in inspector.get_columns("orders")}
    statements: list[str] = []

    if "pincode" not in existing_columns:
        statements.append("ALTER TABLE orders ADD COLUMN pincode VARCHAR(16) DEFAULT ''")
    if "coupon_code" not in existing_columns:
        statements.append("ALTER TABLE orders ADD COLUMN coupon_code VARCHAR(32)")

    if not statements:
        statements = []

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))

    if "order_items" not in tables:
        return

    order_item_columns = {column["name"] for column in inspector.get_columns("order_items")}
    order_item_statements: list[str] = []

    if "product_slug" not in order_item_columns:
        order_item_statements.append("ALTER TABLE order_items ADD COLUMN product_slug VARCHAR(120)")
    if "variant_id" not in order_item_columns:
        order_item_statements.append("ALTER TABLE order_items ADD COLUMN variant_id INTEGER")
    if "mrp" not in order_item_columns:
        order_item_statements.append("ALTER TABLE order_items ADD COLUMN mrp NUMERIC(10, 2)")

    if not order_item_statements:
        return

    with engine.begin() as connection:
        for statement in order_item_statements:
            connection.execute(text(statement))
