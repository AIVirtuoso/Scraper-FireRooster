from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, func  
from datetime import datetime

from schema import Audio, PurchasedScanner, Alert, Address, Scanner, Category, Variables

async def get_all_audios(db:AsyncSession):
    stmt = select(Audio)  
    result = await db.execute(stmt)  
    return result.scalars().all() 

async def get_audio_by_filename(db: AsyncSession, filename):
    stmt = select(Audio).filter(Audio.file_name == filename)
    result = await db.execute(stmt)
    return result.scalars().all()

async def add_object_and_commit(db: AsyncSession, obj):  
    try:  
        db.add(obj)  
        await db.commit()  
        return obj  
    except:  
        await db.rollback()  
        raise

async def remove_duplicate_audios_by_filename(db:AsyncSession):
    async with db.begin(): # Ensuring transaction is within context  
    # Step 1: Find all filenames with duplicates  
        distinct_filenames_stmt = (  
            select(Audio.file_name, func.count(Audio.id))  
            .group_by(Audio.file_name)  
            .having(func.count(Audio.id) > 1)  
        )  
        result = await db.execute(distinct_filenames_stmt)  
        duplicate_filenames = result.all()  

        # Step 2: For each duplicate filename, keep only the first occurrence and delete the rest  
        for filename, count in duplicate_filenames:  
            get_duplicates_stmt = (  
                select(Audio.id)  
                .filter(Audio.file_name == filename)  
                .order_by(Audio.id)  
            )  
            duplicate_result = await db.execute(get_duplicates_stmt)  
            duplicate_ids = [audio_id[0] for audio_id in duplicate_result.all()]  

            # Keep the first occurrence, delete the rest  
            if len(duplicate_ids) > 1:  
                ids_to_delete = duplicate_ids[1:]  # Skip the first occurrence  

                delete_stmt = delete(Audio).where(Audio.id.in_(ids_to_delete))  
                await db.execute(delete_stmt)  

        # Commit changes to the database  
        await db.commit()  

    # Optionally, return the list of deleted IDs or some status  
    return "Duplicates removed successfully"


async def insert_audio(db: AsyncSession, audio, context, assembly_transcript, cleared_conversation, scanner_id, dateTime):
    stmt = select(Audio).filter(Audio.file_name == audio)
    result = await db.execute(stmt)
    data = result.scalar_one_or_none()
    print(data)
    if not data:
        new_audio = Audio(file_name=audio, context=context, assembly_transcript=assembly_transcript, cleared_context=cleared_conversation, scanner_id=scanner_id, dateTime=dateTime)
        db.add(new_audio)
        await db.flush()  # ensure flush and obtain primary key value  
        await db.commit()
        await db.refresh(new_audio)
        return new_audio

async def update_audio(db: AsyncSession, audio, file_name, context, assembly_transcript, cleared_conversation, scanner_id, dateTime):
    audio.file_name = file_name
    audio.context = context
    audio.assembly_transcript = assembly_transcript
    audio.cleared_context = cleared_conversation
    audio.scanner_id = scanner_id
    audio.dateTime = dateTime
    await db.commit()
    await db.refresh(audio)
    print(audio)
        
async def insert_alert(db: AsyncSession, purchased_scanner_id, event, dateTime):
    print("dateTime: ", dateTime)
    new_alert = Alert(
        category=event['category'],
        sub_category=event['sub-category'],
        headline=event['headline'],
        description=event['description'],
        address=event['incident_Address'],
        scanner_id=purchased_scanner_id,
        dateTime=dateTime,
        is_visited=0,
        rating = int(event['rating']),
        rating_title = event['rating_title'],
        rating_criteria = event['rating_criteria'],
        ten_codes = event['10-codes'],
        response_origin_address = event['response_origin_address'],
        response_origin_radius = event['response_origin_radius']
    )
    # return await add_object_and_commit(db, new_alert)
    db.add(new_alert)
    print('new_alert: ', new_alert)
    await db.commit()
    await db.refresh(new_alert)
    return new_alert

async def insert_sub_category(db: AsyncSession, category, sub_category):
    stmt = select(Category).filter(Category.sub_category == sub_category)
    result = await db.execute(stmt)
    data = result.scalar_one_or_none()
    print(data)
    if not data:
        new_sub_category = Category(category=category, sub_category=sub_category)
        db.add(new_sub_category)
        print('new_sub_category: ', new_sub_category)
        await db.commit()  
        await db.refresh(new_sub_category)
        return new_sub_category

async def get_audios_by_scanner_id(db: AsyncSession, purchased_scanner_id):
    stmt = select(Audio).filter(Audio.scanner_id == purchased_scanner_id)
    result = await db.execute(stmt)
    audios = result.scalars().all()
    return audios


async def get_all_purchased_scanners(db: AsyncSession):
    stmt = select(PurchasedScanner)
    result = await db.execute(stmt)
    return result.scalars().all()

async def insert_validated_address(db: AsyncSession, address, score, alert_id, type, scanner_id, dateTime, contact_info, spokeo_status):
    new_address = Address(address=address, score=score, alert_id=alert_id, type=type, scanner_id=scanner_id, dateTime=dateTime, contact_info=contact_info, spokeo_status=spokeo_status)
    db.add(new_address)
    await db.commit()  
    await db.refresh(new_address)
    return new_address

async def get_scanner_by_scanner_id(db: AsyncSession, scanner_id):
    stmt = select(Scanner).filter(Scanner.scanner_id == scanner_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_all_subcategories(db: AsyncSession):
    stmt = select(Category)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_address_by_id(db: AsyncSession, id):
    stmt = select(Address).filter(Address.id == id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def update_address(db: AsyncSession, id, contact_info):
    stmt = select(Address).filter(Address.id == id)
    result = await db.execute(stmt)
    result = result.scalar_one_or_none()
    result.contact_info = contact_info
    result.spokeo_status = 1
    await db.commit()
    await db.refresh(result)



####################################
async def filter_alerts(db: AsyncSession):
    # Define the date threshold (October 3rd of the current year)
    date_threshold = datetime(datetime.now().year, 10, 11)

    # Create a statement to select audios where dateTime is later than October 3rd
    stmt = select(Audio).filter(Audio.dateTime > date_threshold)

    # Execute the statement
    result = await db.execute(stmt)

    # Fetch all results
    audios = result.scalars().all()

    return audios

async def get_variables(db: AsyncSession):
    query = select(Variables)
    result = await db.execute(query)
    return result.scalar_one_or_none()