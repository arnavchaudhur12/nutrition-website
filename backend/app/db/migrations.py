from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def run_startup_migrations(engine: Engine) -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    _ensure_peanut_butter_hero_image(engine, tables)

    if "orders" not in tables:
        return

    existing_columns = {column["name"] for column in inspector.get_columns("orders")}
    statements: list[str] = []

    if "pincode" not in existing_columns:
        statements.append("ALTER TABLE orders ADD COLUMN pincode VARCHAR(16) DEFAULT ''")
    if "coupon_code" not in existing_columns:
        statements.append("ALTER TABLE orders ADD COLUMN coupon_code VARCHAR(32)")
    if "city" not in existing_columns:
        statements.append("ALTER TABLE orders ADD COLUMN city VARCHAR(120) DEFAULT ''")
    if "state" not in existing_columns:
        statements.append("ALTER TABLE orders ADD COLUMN state VARCHAR(120) DEFAULT ''")
    if "shipment_provider" not in existing_columns:
        statements.append("ALTER TABLE orders ADD COLUMN shipment_provider VARCHAR(64)")
    if "shipment_order_id" not in existing_columns:
        statements.append("ALTER TABLE orders ADD COLUMN shipment_order_id VARCHAR(128)")
    if "shipment_status" not in existing_columns:
        statements.append("ALTER TABLE orders ADD COLUMN shipment_status VARCHAR(120)")
    if "awb_number" not in existing_columns:
        statements.append("ALTER TABLE orders ADD COLUMN awb_number VARCHAR(128)")
    if "shipment_courier" not in existing_columns:
        statements.append("ALTER TABLE orders ADD COLUMN shipment_courier VARCHAR(120)")
    if "shipment_message" not in existing_columns:
        statements.append("ALTER TABLE orders ADD COLUMN shipment_message TEXT")
    if "shipment_label_url" not in existing_columns:
        statements.append("ALTER TABLE orders ADD COLUMN shipment_label_url TEXT")
    if "shipment_estimated_delivery" not in existing_columns:
        statements.append("ALTER TABLE orders ADD COLUMN shipment_estimated_delivery DATE")
    if "shipment_tracking_history" not in existing_columns:
        statements.append("ALTER TABLE orders ADD COLUMN shipment_tracking_history TEXT")
    if "shipment_error" not in existing_columns:
        statements.append("ALTER TABLE orders ADD COLUMN shipment_error TEXT")
    if "shipment_created_at" not in existing_columns:
        statements.append("ALTER TABLE orders ADD COLUMN shipment_created_at DATETIME")
    if "shipment_last_synced_at" not in existing_columns:
        statements.append("ALTER TABLE orders ADD COLUMN shipment_last_synced_at DATETIME")

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


def _ensure_peanut_butter_hero_image(engine: Engine, tables: set[str]) -> None:
    if "hero_settings" not in tables or "hero_images" not in tables:
        return

    image_url = "/uploads/lagads-peanut-butter-hero-second.jpg"
    with engine.begin() as connection:
        hero_settings_id = connection.execute(
            text("SELECT id FROM hero_settings ORDER BY id LIMIT 1")
        ).scalar_one_or_none()
        if hero_settings_id is None:
            return

        existing_id = connection.execute(
            text("SELECT id FROM hero_images WHERE image_url = :image_url LIMIT 1"),
            {"image_url": image_url},
        ).scalar_one_or_none()
        if existing_id is not None:
            connection.execute(
                text("UPDATE hero_images SET sort_order = 1 WHERE id = :existing_id"),
                {"existing_id": existing_id},
            )
            return

        connection.execute(
            text(
                "UPDATE hero_images "
                "SET sort_order = sort_order + 1 "
                "WHERE hero_settings_id = :hero_settings_id AND sort_order >= 1"
            ),
            {"hero_settings_id": hero_settings_id},
        )
        connection.execute(
            text(
                "INSERT INTO hero_images (hero_settings_id, image_url, sort_order) "
                "VALUES (:hero_settings_id, :image_url, 1)"
            ),
            {"hero_settings_id": hero_settings_id, "image_url": image_url},
        )
