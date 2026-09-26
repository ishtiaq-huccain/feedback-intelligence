from fastapi import FastAPI
from backend.api.router import router  # import the APIRouter instance

app = FastAPI(title="Feedback Intelligence API", version="0.2.0")

# Mount central router
app.include_router(router)


@app.get("/", tags=["health"])
def root():
    return {"message": "Feedback Intelligence API is running 🚀"}
