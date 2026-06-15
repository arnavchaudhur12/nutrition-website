from datetime import datetime, timedelta
from collections import defaultdict

from sqlalchemy.orm import Session

from app.repositories.order import OrderRepository


class MetricsService:
    def __init__(self, db: Session):
        self.db = db
        self.orders = OrderRepository(db)

    def get_dashboard_snapshot(self, period: str = "all_time") -> dict[str, object]:
        all_orders = self.orders.list_orders()
        successful_orders = [
            order
            for order in all_orders
            if self._is_successful_order(order) and self._matches_period(order.created_at, period)
        ]
        product_summary: dict[str, dict[str, float]] = defaultdict(
            lambda: {"quantity_sold": 0, "total_amount": 0.0}
        )

        for order in successful_orders:
            for item in order.items:
                product_key = f"{item.product_name} - {item.flavour}"
                product_summary[product_key]["quantity_sold"] += item.quantity
                product_summary[product_key]["total_amount"] += float(item.line_total)

        sorted_products = sorted(
            (
                {
                    "product_name": product_name,
                    "quantity_sold": int(values["quantity_sold"]),
                    "total_amount": round(values["total_amount"], 2),
                }
                for product_name, values in product_summary.items()
            ),
            key=lambda item: (-item["quantity_sold"], -item["total_amount"], item["product_name"]),
        )

        return {
            "total_actual_sales_count": len(successful_orders),
            "total_actual_revenue": round(
                sum(float(order.total_amount) for order in successful_orders), 2
            ),
            "total_products_sold": sum(item.quantity for order in successful_orders for item in order.items),
            "product_performance": sorted_products,
            "note": "Metrics are based on successful payments only for the selected date range.",
        }

    @staticmethod
    def _is_successful_order(order) -> bool:
        return order.payment_status == "paid" and order.status != "cancelled"

    @staticmethod
    def _matches_period(created_at: datetime, period: str) -> bool:
        if period == "all_time":
            return True

        now = datetime.utcnow()
        ranges = {
            "last_7_days": now - timedelta(days=7),
            "last_30_days": now - timedelta(days=30),
            "last_90_days": now - timedelta(days=90),
        }
        threshold = ranges.get(period)
        if threshold is None:
            return True
        return created_at >= threshold
