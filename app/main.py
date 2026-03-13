from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.endpoints.tenant import router as tenant_router
from app.api.v1.endpoints.nutricionista import router as nutricionista_router


app = FastAPI(
    title=settings.APP_NAME,
    version="0.0.1",
    docs_url="/docs" if settings.is_swagger_enabled() else None,
    redoc_url="/redoc" if settings.is_swagger_enabled() else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(tenant_router, prefix="/api/v1")
app.include_router(nutricionista_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}
