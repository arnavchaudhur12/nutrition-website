from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.api.routes import admin, auth, feedback, health, hero, metrics, newsletter, orders, payments, products
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.seed import seed_defaults
from app.db.session import SessionLocal, engine

try:
    settings = get_settings()
    
    configure_logging()
    
    Base.metadata.create_all(bind=engine)
    
    with SessionLocal() as session:
        seed_defaults(session)
    
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(exc)}"},
        )

    app.include_router(health.router, prefix="/api/health", tags=["health"])
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(hero.router, prefix="/api/hero", tags=["hero"])
    app.include_router(products.router, prefix="/api/products", tags=["products"])
    app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
    app.include_router(feedback.router, prefix="/api/feedback", tags=["feedback"])
    app.include_router(newsletter.router, prefix="/api/newsletter", tags=["newsletter"])
    app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
    app.include_router(metrics.router, prefix="/api/admin/metrics", tags=["metrics"])
    app.include_router(payments.router, prefix="/api", tags=["payments"])
    
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

    @app.get("/")
    def root() -> dict[str, str]:
        return {"message": "Lagads Nutrition API is running."}

except Exception as e:
    raise
