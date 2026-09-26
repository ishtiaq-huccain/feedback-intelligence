from fastapi import FastAPI

from backend.api.router import router
from backend.database.database import bootstrap_schema

app = FastAPI(
    title="Feedback Intelligence API",
    version="0.2.0",
)

@app.on_event("startup")
def startup_event():
    bootstrap_schema()

app.include_router(router)


@app.get("/", tags=["health"])
def root():
    return {"message": "Feedback Intelligence API is running 🚀"}
