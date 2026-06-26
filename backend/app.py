from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from pathlib import Path

from api.bills import router as bills_router
from models import create_tables, engine

# Define template directory relative to this file
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "frontend" / "templates"

# Initialize Jinja2Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Creating database tables...")
    create_tables() # Call the function to create tables
    print("Database tables created.")
    yield
    # Shutdown (optional)
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)

# Include routers
app.include_router(bills_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Sribuu API!"}
