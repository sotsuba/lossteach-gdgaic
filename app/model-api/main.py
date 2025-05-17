from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
    openapi_url="/openapi.json",
    default_response_class=JSONResponse,
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},  # Disable model expansion by default
    swagger_ui_init_oauth={},  # Disable OAuth by default
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
    log_level="info",
    proxy_headers=True,
    server_header=False,
    date_header=False,
    forwarded_allow_ips="*"
)

if __name__ == "__main__":
    server = uvicorn.Server(config)
    server.run()



