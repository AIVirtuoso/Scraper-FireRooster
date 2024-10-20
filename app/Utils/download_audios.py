import datetime  
import io  
import os  
import logging as log  
import asyncio
import aiohttp
import requests  
import json
from pydub import AudioSegment  
from app.Utils.whisper import stt_archive  

from app.Utils.remove_space import process_audio  

TEMP_FOLDER = "audios"  

def format_datetime_for_url(date=None):  
    # parse input date, for Url  
    if date is None:  
        date = datetime.datetime.now().date()  

    datetime_obj = datetime.datetime(date.year, date.month, date.day)  

    formatted_date = date.strftime("%m/%d/%Y")  
    timestamp = int(datetime_obj.timestamp())  

    return formatted_date, timestamp  


def extract_ids_from_archive(archive):  
    return [{"id": item[0], "start_time": item[1], "end_time": item[2]} for item in archive["data"]] if "data" in archive else None  


async def get_full_day_archives(session, feedId, date=None):  
    # default to yesterday  
    if date is None:  
        date = datetime.datetime.now().date() - datetime.timedelta(days=1)  
    feed_archive_url = "https://www.broadcastify.com/archives/ajax.php"  
    url_date = format_datetime_for_url(date)  
    formatted_url = (  
        f"{feed_archive_url}?feedId={feedId}&date={url_date[0]}&_={url_date[1]}"  
    )

    print("formatted_url: ", formatted_url)
    async with session.get(formatted_url) as resp:
        if resp.status != 200:
            print(f"Failed to get feed archive, status code: {resp.status}")
            return None
        try:
            text = await resp.text()  
            feed_archive = json.loads(text) 
        except Exception as e:
            print(f"Failed to parse JSON: {e}")
            text = await resp.text()
            print(f"Response text: {text}")
            return None

    audio_list = extract_ids_from_archive(feed_archive)  
    return audio_list  


async def save_and_convert_to_wav(file_stream, file_name):  
    # download the file as mp3, then convert to wav  
    file_stream.seek(0)  

    print("file_name: ", file_name)  
    
    file_path = os.path.join(TEMP_FOLDER, file_name + '_p.mp3')  
    
    if os.path.exists(file_path):  
        print("yes")  
        return file_path  

    def blocking_operations():

        with open(file_name + ".mp3", "wb") as file:  
            file.write(file_stream.read())  

        # convert MP3 to WAV  
        audio = AudioSegment.from_mp3(file_name + ".mp3")
        
        audio_file_name = os.path.join(TEMP_FOLDER, file_name + ".wav")  
        audio.export(audio_file_name, format="wav")  
        delete_temp_mp3(file_name)  
        return audio_file_name

        
    audio_file_name = await asyncio.to_thread(blocking_operations)
    print("audio_file_name: ", audio_file_name)  
    
    print("removing noizies ")  
    audio_file_name = await process_audio(audio_file_name)  
        
    return audio_file_name  


def delete_temp_mp3(filename):  
    mp3_filename = f"{filename}.mp3"  
    os.remove(mp3_filename)  


async def download_single_archive(archive, session):  
    base_url = "https://www.broadcastify.com"  
    try:  
        archive_id = archive['id']  
        async with session.get(f"{base_url}/archives/downloadv2/{archive_id}") as resp:
            content = await resp.read()
        filename = await save_and_convert_to_wav(  
            io.BytesIO(content), archive_id  
        )

        archive['filename'] = filename
        return archive
    except Exception as e:
        print(e)  
        return None  


async def download_archives_sync(session, archive):  
    return await download_single_archive(archive, session)   


async def parse_date_archive(session, feedId, date=datetime.datetime.now()):  
    username = "alertai"  
    password = "Var+(n42421799)"  
    action = "auth"  
    redirect = "https://www.broadcastify.com/"  
    
    async with session.post(  
        "https://www.broadcastify.com/login/",  
        data={  
            "username": username,  
            "password": password,  
            "action": action,  
            "redirect": redirect,  
        },  
        headers={"Content-Type": "application/x-www-form-urlencoded"},  
    ) as resp:  
        await resp.text()  # Consume response to ensure request is processed

    if 'bcfyuser1' not in [cookie.key for cookie in session.cookie_jar]:  
        print("Login failed")  
        return  

    print("Login successful")

    archive_list = await get_full_day_archives(  
        session,
        feedId=feedId,
        date=date,
    )

    if archive_list and len(archive_list):
        # download full day archive
        archive_list = await download_archives_sync(session, archive_list[0])
    
    return archive_list  


async def download(db, feedId):  
    # parse last 10 days of data  
    result = []
    async with aiohttp.ClientSession() as session:  
        print(f"Processing feedId: {feedId}")  
        result = await parse_date_archive(session, feedId, datetime.datetime.now() - datetime.timedelta(days=0))
        await stt_archive(db, feedId, result)