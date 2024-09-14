from fastapi import APIRouter, Depends  
from database import AsyncSessionLocal  
from sqlalchemy.ext.asyncio import AsyncSession  
import asyncio  

import app.Utils.crud as crud
from app.Utils.spokeo import run_scraper
from typing import AsyncGenerator

router = APIRouter()  

async def get_db() -> AsyncGenerator[AsyncSession, None]:  
    async with AsyncSessionLocal() as session:  
        yield session 

@router.get('/verify-address')
async def verify_address_router(address:str, db: AsyncSession = Depends(get_db)):
    await run_scraper(address)