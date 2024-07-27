from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from schema import Audio, PurchasedScanner, Alert, Address, Scanner


async def get_audio_by_filename(db: AsyncSession, filename):
    stmt = select(Audio).filter(Audio.file_name == filename)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def insert_audio(db: AsyncSession, audio, context, scanner_id, dateTime):
    stmt = select(Audio).filter(Audio.file_name == audio)
    result = await db.execute(stmt)
    data = result.scalar_one_or_none()
    print(data)
    if not data:
        new_audio = Audio(file_name=audio, context=context, scanner_id=scanner_id, dateTime=dateTime)
        db.add(new_audio)
        await db.commit()  
        await db.refresh(new_audio)
        return new_audio
        
async def insert_alert(db: AsyncSession, purchased_scanner_id, event, dateTime):
    print("dateTime: ", dateTime)
    new_alert = Alert(headline=event['headline'], description=event['description'], address=event['incident_Address'], scanner_id=purchased_scanner_id, dateTime=dateTime)
    db.add(new_alert)
    print('new_alert: ', new_alert)
    await db.commit()  
    await db.refresh(new_alert)
    return new_alert

async def get_audios_by_scanner_id(db: AsyncSession, purchased_scanner_id):
    stmt = select(Audio).filter(Audio.scanner_id == purchased_scanner_id)
    result = await db.execute(stmt)
    audios = result.scalars().all()
    return audios


async def get_all_purchased_scanners(db: AsyncSession):
    stmt = select(PurchasedScanner)
    result = await db.execute(stmt)
    return result.scalars().all()

async def insert_validated_address(db: AsyncSession, address, score, alert_id):
    new_address = Address(address=address, score=score, alert_id=alert_id)
    db.add(new_address)
    await db.commit()  
    await db.refresh(new_address)
    return new_address

async def get_scanner_by_scanner_id(db: AsyncSession, scanner_id):
    stmt = select(Scanner).filter(Scanner.scanner_id == scanner_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()