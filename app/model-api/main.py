from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from routers import predict
import uvicorn
import logging
import asyncio
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Add timeout middleware
class TimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await asyncio.wait_for(call_next(request), timeout=60.0)
        except asyncio.TimeoutError:
            return JSONResponse(
                status_code=504,
                content={"detail": "Request timeout"}
            )

# Create FastAPI app with optimized settings
app = FastAPI(
    title="Fragment Detection API",
    description="API for detecting and analyzing fragments in images",
    version="1.0.0",
    docs_url=None,  # Disable default docs
    redoc_url=None,  # Disable default redoc
    openapi_url="/openapi.json",
    default_response_class=JSONResponse
)

# Custom docs endpoint with optimized settings
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Fragment Detection API - Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
        swagger_ui_parameters={
            "defaultModelsExpandDepth": -1,
            "displayRequestDuration": True,
            "filter": True,
            "tryItOutEnabled": True,
            "syntaxHighlight.theme": "monokai",
            "docExpansion": "none",
            "operationsSorter": "alpha",
            "tagsSorter": "alpha",
            "showExtensions": True,
            "showCommonExtensions": True,
            "supportedSubmitMethods": ["get", "post"],
            "persistAuthorization": True,
            "displayOperationId": False,
            "deepLinking": True,
            "showMutatedRequest": False,
            "defaultModelRendering": "model",
            "defaultModelExpandDepth": 1,
            "defaultModelsExpandDepth": 1,
            "showExtensions": True,
            "showCommonExtensions": True,
            "supportedSubmitMethods": ["get", "post"],
            "validatorUrl": None,
        }
    )

# Add middleware
app.add_middleware(TimeoutMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with prefix
app.include_router(
    predict.router,
    tags=["prediction"]
)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Server configuration
config = uvicorn.Config(
    "main:app",
    host="0.0.0.0",
    port=8000,
    reload=True,
    workers=1,
    timeout_keep_alive=30,
    limit_concurrency=10,
    loop="asyncio",
    http="auto",
    log_level="info"
)

if __name__ == "__main__":
    server = uvicorn.Server(config)
    server.run()



