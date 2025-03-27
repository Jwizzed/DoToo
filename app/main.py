from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.endpoints import auth, todos
from app.core.config import settings


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="My awesome Todo app",
)

# --- Middleware ---
# CORS (Cross-Origin Resource Sharing) - Adjust origins as needed for your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# --- Static Files (for uploaded images) ---
# Mount the static directory to serve images
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

# --- API Routers ---
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Auth"])
app.include_router(todos.router, prefix=f"{settings.API_V1_STR}/todos", tags=["Todos"])


# --- Root Endpoint ---
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}!"}


# --- Health Check Endpoint ---
@app.get("/health", tags=["Health"], status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
