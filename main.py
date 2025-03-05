import sys
import uvicorn, os, time
from typing import Optional
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, Query, Request
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.middleware.sessions import SessionMiddleware 
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from telex_python_apm.fastapi.middleware import MonitorMiddleware

from api.db.database import get_db
from api.loggers.app_logger import app_logger
from api.utils.success_response import success_response
from api.utils.telex_integration import TelexIntegration
from api.v1.routes import api_version_one
from api.utils.settings import settings
from api.utils.log_streamer import log_streamer


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = next(get_db())
    
    yield

app = FastAPI(
    lifespan=lifespan,
    title='smashtravel.com API'
)

# Set up email templates and css static files
email_templates = Jinja2Templates(directory='api/core/dependencies/email/templates')
EMAIL_STATIC_DIR = 'api/core/dependencies/email/static'
app.mount(f'/{EMAIL_STATIC_DIR}', StaticFiles(directory=EMAIL_STATIC_DIR), name='email-static')

MEDIA_DIR = './media'
os.makedirs(MEDIA_DIR, exist_ok=True)

TEMP_DIR = './tmp/media'
os.makedirs(TEMP_DIR, exist_ok=True)

# Load up media static files
app.mount('/media', StaticFiles(directory=MEDIA_DIR), name='media')
app.mount('/tmp/media', StaticFiles(directory=TEMP_DIR), name='tmp-media')


origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://smashtravels.com",
    "https://www.smashtravels.com"
]


# In-memory request counter by endpoint and IP address
request_counter = defaultdict(lambda: defaultdict(int))
# Middleware to track request counts and IP addresses
class RequestCountMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        endpoint = request.url.path
        ip_address = request.client.host
        request_counter[endpoint][ip_address] += 1
        response = await call_next(request)
        return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.add_middleware(RequestCountMiddleware)


# Middleware to log details after each request
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Capture request start time
    start_time = time.time()

    # Process the request
    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time
    formatted_process_time = f"{process_time:.3f}s"

    # Capture request and response details
    client_ip = request.client.host
    method = request.method
    url = request.url.path
    status_code = response.status_code

    # Format the log string similar to your example
    log_string = (
        f"{client_ip} - \"{method} {url} HTTP/1.1\" {status_code} - {formatted_process_time}"
    )

    # Log the formatted string
    app_logger.info(log_string)
    # TelexIntegration(webhook_id='a094d8de6f2e').push_message(
    #     event_name='App logs',
    #     message=log_string,
    #     status='error' if status_code not in [200, 201, 202] else 'success'
    # )

    return response


app.include_router(api_version_one)

@app.get("/", tags=["Home"])
async def get_root(request: Request) -> dict:
    return success_response(
        message="Welcome to API", 
        status_code=status.HTTP_200_OK
    )


@app.get("/request-stats", response_model=success_response, tags=["Home"])
async def get_request_stats():
    '''Endpoint to get request stats'''

    return success_response(
        status_code=status.HTTP_200_OK, 
        message="Endpoints request retreived successfully", 
        data={
            "request_counts": {endpoint: dict(ips) for endpoint, ips in request_counter.items()}
        }
    )


# @app.get("/logs", tags=["Home"])
# async def stream_logs(lines: Optional[int] = Query(None)):
#     '''Endpoint to stream logs'''
    
#     return StreamingResponse(log_streamer('logs/app_logs.log', lines), media_type="text/event-stream")


# REGISTER EXCEPTION HANDLERS
@app.exception_handler(HTTPException)
async def http_exception(request: Request, exc: HTTPException):
    """HTTP exception handler"""

    exc_type, exc_obj, exc_tb = sys.exc_info()
    app_logger.info(f"HTTPException: {request.url.path} | {exc.status_code} | {exc.detail}")
    app_logger.info(f"[ERROR] - An error occured | {exc}, {exc_type} {exc_obj} line {exc_tb.tb_lineno}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": False,
            "status_code": exc.status_code,
            "message": exc.detail,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception(request: Request, exc: RequestValidationError):
    """Validation exception handler"""

    errors = [
        {"loc": error["loc"], "msg": error["msg"], "type": error["type"]}
        for error in exc.errors()
    ]

    exc_type, exc_obj, exc_tb = sys.exc_info()
    app_logger.info(f"RequestValidationError: {request.url.path} | {errors}")
    app_logger.info(f"[ERROR] - An error occured | {exc}, {exc_type} {exc_obj} line {exc_tb.tb_lineno}")

    return JSONResponse(
        status_code=422,
        content={
            "status": False,
            "status_code": 422,
            "message": "Invalid input",
            "errors": errors,
        },
    )


@app.exception_handler(IntegrityError)
async def integrity_exception(request: Request, exc: IntegrityError):
    """Integrity error exception handlers"""

    exc_type, exc_obj, exc_tb = sys.exc_info()
    app_logger.info(f"Exception occured | {request.url.path} | 500")
    app_logger.info(f"[ERROR] - An error occured | {exc}, {exc_type} {exc_obj} {exc_tb.tb_lineno}")

    return JSONResponse(
        status_code=500,
        content={
            "status": False,
            "status_code": 500,
            "message": f"An unexpected error occurred: {exc}",
        },
    )


@app.exception_handler(Exception)
async def exception(request: Request, exc: Exception):
    """Other exception handlers"""

    exc_type, exc_obj, exc_tb = sys.exc_info()
    app_logger.info(f"Exception occured | {request.url.path} | 500")
    app_logger.info(f"[ERROR] - An error occured | {exc}, {exc_type} {exc_obj} {exc_tb.tb_lineno}")
    
    TelexIntegration(webhook_id='f764c13bd28b').push_message(
        event_name='App Exception',
        message=f"Exception occured | {request.url.path}\n[ERROR] - An error occured | {exc}, {exc_type} {exc_obj} {exc_tb.tb_lineno}",
        status='error'
    )

    return JSONResponse(
        status_code=500,
        content={
            "status": False,
            "status_code": 500,
            "message": f"An unexpected error occurred: {exc}",
        },
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        port=7001, 
        reload=True,
        workers=4,
        reload_excludes=['logs']
    )