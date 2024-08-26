from fastapi import APIRouter, Depends  
from database import AsyncSessionLocal  
from sqlalchemy.ext.asyncio import AsyncSession  
import asyncio  

from app.Utils.download_audios import download  
from app.Utils.whisper import stt_archive  
import app.Utils.crud as crud
from app.Utils.categorize import all_subcategories
from typing import AsyncGenerator

router = APIRouter()  

async def get_db() -> AsyncGenerator[AsyncSession, None]:  
    async with AsyncSessionLocal() as session:  
        yield session 

async def download_and_process(db: AsyncSession, purchased_scanner_id: int):
    archive_list = await download(purchased_scanner_id)
    print(archive_list)  

    # Call the STT processing function  
    await stt_archive(db, purchased_scanner_id, archive_list)  

async def process_batches(db, batch):  
    semaphore = asyncio.Semaphore(5)  
    tasks = [limited_concurrent_tasks(semaphore, db, scanner_id) for scanner_id in batch]  
    await asyncio.gather(*tasks)


async def limited_concurrent_tasks(semaphore, db, purchased_scanner_id):  
    async with semaphore:  
        await download_and_process(db, purchased_scanner_id)  

@router.get('/update-alerts')  
async def update_alerts_router(db: AsyncSession = Depends(get_db)):  
    purchased_scanner_list = await crud.get_all_purchased_scanners(db)  
    print("purchased_scanner_list: ", purchased_scanner_list)  
    purchased_scanner_id_list = list(  
        {purchased_scanner.scanner_id for purchased_scanner in purchased_scanner_list}  # Remove duplicates  
    )  
    # await download_and_process(db, purchased_scanner_id_list[16])

    for i in range(0, len(purchased_scanner_id_list), 5):  
        batch = purchased_scanner_id_list[i:i+5]  
        await process_batches(db, batch)  

@router.get('/all-subcategories')  
async def get_all_subcategories(db: AsyncSession = Depends(get_db)):
    # alerts = await crud.remove_duplicate_audios_by_filename(db)
    sub_categories = await all_subcategories(db)
    # sub_categories = await crud.get_all_subcategories(db)
    unique_sub_categories = {tuple(item.items()): item for item in sub_categories}.values()
    
    # Convert the unique items back to a list  
    unique_list = list(unique_sub_categories)
    
    # Sort by "Category"  
    sorted_list = sorted(unique_list, key=lambda x: x.get('category'))
    
    return sorted_list