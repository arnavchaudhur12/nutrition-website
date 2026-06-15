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
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
