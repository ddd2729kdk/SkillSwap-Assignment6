import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.exceptions import AppError,app_error_handler
from app.routers import reviews,skills,swaps,user_skills,users
from app.seed import seed_data
@asynccontextmanager
async def lifespan(app:FastAPI):
    if os.getenv("SKILLSWAP_SEED","1")=="1":seed_data()
    yield
app=FastAPI(title="SkillSwap API",version="2.0.0",description="Persistent PostgreSQL backend for student skill exchange.",lifespan=lifespan)
app.add_exception_handler(AppError,app_error_handler)
app.include_router(users.router);app.include_router(user_skills.router);app.include_router(skills.router);app.include_router(swaps.router);app.include_router(reviews.router)
@app.get("/",tags=["Health"])
def root():return {"service":"SkillSwap API","status":"ok","docs":"/docs","database":"PostgreSQL"}
