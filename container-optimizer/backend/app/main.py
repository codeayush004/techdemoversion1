from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import containers, auth

app = FastAPI(
    title="Docker Container Optimizer",
    description="Real-time Docker container optimization & security platform",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(containers.router, prefix="/api")
app.include_router(auth.router, prefix="/api")

@app.get("/")
def health():
    return {"status": "running"}
