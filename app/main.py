import socketio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes import generate, health, thread
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


fastapi_app.include_router(health.router)
fastapi_app.include_router(thread.router)
fastapi_app.include_router(generate.router)

app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
