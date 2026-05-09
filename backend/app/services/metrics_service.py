from collections import Counter

from sqlalchemy.orm import Session

from app.repositories.order import OrderRepository


class MetricsService:
    def __init__(self, db: Session):
        self.db = db
        self.orders = OrderRepository(db)

    def get_dashboard_snapshot(self) -> dict[str, object]:
        all_orders = self.orders.list_orders()
        flavour_counter = Counter()
        for order in all_orders:
            for item in order.items:
                flavour_counter[item.flavour] += item.quantity

        return {
            "total_orders": len(all_orders),
            "total_revenue": self.orders.aggregate_total_revenue(),
            "top_products": flavour_counter.most_common(5),
            "note": "Month-wise, day-wise, and hour-wise aggregations can be extended from this service layer.",
        }

