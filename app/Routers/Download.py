from fastapi import APIRouter, Depends  
from database import AsyncSessionLocal  
from sqlalchemy.ext.asyncio import AsyncSession  
import asyncio  
import aiohttp

from app.Utils.download_audios import download  
from app.Utils.whisper import stt_archive  
import app.Utils.crud as crud
from app.Utils.categorize import all_subcategories
from typing import AsyncGenerator

router = APIRouter()  

batch_size = 3

async def get_db() -> AsyncGenerator[AsyncSession, None]:  
    async with AsyncSessionLocal() as session:  
        yield session 

async def download_and_process(db: AsyncSession, purchased_scanner_id: int):
    print("purchased_scanner_id: ", purchased_scanner_id)
    try:
        archive_list = await download(db, purchased_scanner_id)
    except Exception as e:
        print(e)

async def process_batches(db, scanner_list, start, end):
    tasks = []  
    for index in range(start, end):  
        task = asyncio.create_task(download_and_process(db, scanner_list[index]))  
        tasks.append(task)
    results = await asyncio.gather(*tasks)  


@router.get('/update-alerts')
async def update_alerts_router(db: AsyncSession = Depends(get_db)):
    variables = await crud.get_variables(db)
    print("stop scrapper enabled")
    if not variables.scraper_status:
        return

    purchased_scanner_list = await crud.get_all_purchased_scanners(db)
    print("purchased_scanner_list: ", purchased_scanner_list)
    purchased_scanner_id_list = list(
        {purchased_scanner.scanner_id for purchased_scanner in purchased_scanner_list}  # Remove duplicates
    )
    # await download_and_process(db, purchased_scanner_id_list[16])

    total_scanners = len(purchased_scanner_id_list)
    for i in range(0, total_scanners, batch_size):
        batch = purchased_scanner_id_list[i:i+batch_size]  
        batch_end = min(i + batch_size, total_scanners)
        await process_batches(db, purchased_scanner_id_list, i, batch_end)
    # for i in range(0, len(purchased_scanner_id_list)):
    #     await download_and_process(db, purchased_scanner_id_list[i])

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

@router.get('/extract-alerts')
async def extract_alerts_router(db: AsyncSession = Depends(get_db)):
    audios = await crud.filter_alerts(db)
    print(len(audios))
    for audio in audios:
        print("filename: ", audio.file_name)
        await stt_archive(db, audio.scanner_id, [{"filename": audio.file_name}])