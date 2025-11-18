import socketio

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes import (
    cluster,
    generate,
    health,
    iterate,
    select,
    thread,
    worklet_iterations,
)
from app.socket_handler import sio

fastapi_app = FastAPI()

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# fastapi_app.mount("/static", StaticFiles(directory="app/public"), name="static")


# Consistent error handlers
@fastapi_app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "path": str(request.url.path),
            }
        },
    )


@fastapi_app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": 422,
                "message": "Validation error",
                "details": exc.errors(),
                "path": str(request.url.path),
            }
        },
    )


@fastapi_app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Avoid leaking internals; log if a logger is configured (omitted here)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal Server Error",
                "path": str(request.url.path),
            }
        },
    )


fastapi_app.include_router(health.router)
fastapi_app.include_router(cluster.router)
fastapi_app.include_router(thread.router)
fastapi_app.include_router(generate.router)
fastapi_app.include_router(iterate.router)
fastapi_app.include_router(select.router)
fastapi_app.include_router(worklet_iterations.router)

app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
