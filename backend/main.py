import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routers import generation, documents, etl

# Create tables if they don't exist
# Base.metadata.create_all(bind=engine)

app = FastAPI(title="ICFES RAG Pedagogical System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generation.router)
app.include_router(documents.router)
app.include_router(etl.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return {"message": "Welcome to ICFES RAG System API v2. Visit /static/index.html for UI."}
