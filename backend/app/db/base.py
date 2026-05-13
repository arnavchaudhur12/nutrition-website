from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import model modules so SQLAlchemy metadata includes every table during create_all.
import app.models.coupon  # noqa: F401,E402
import app.models.feedback  # noqa: F401,E402
import app.models.hero  # noqa: F401,E402
import app.models.newsletter  # noqa: F401,E402
import app.models.order  # noqa: F401,E402
import app.models.product  # noqa: F401,E402
import app.models.user  # noqa: F401,E402
