from openai import OpenAI, AsyncOpenAI
import logging as log
from sqlalchemy.ext.asyncio import AsyncSession  

from dotenv import load_dotenv
import assemblyai as aai
import json
import re
import datetime
from typing import AsyncGenerator  
import os
from pydub import AudioSegment
import time
import asyncio
import aiofiles
import io

import app.Utils.crud as crud
from app.Utils.validate_address import validate_address
from app.Utils.get_geocode_data import get_geocode_data, get_score_by_location_type
from app.Utils.spokeo import run_scraper
from app.Utils.send_alert import send_new_alert_phone
from app.Utils.prompt import get_prompt_for_alert_extraction
from database import AsyncSessionLocal

load_dotenv()

client = AsyncOpenAI()
aai.settings.api_key = os.getenv('ASSEMBLY_API_KEY')

config = aai.TranscriptionConfig(speaker_labels=True, speech_model=aai.SpeechModel.nano)
transcriber = aai.Transcriber(config=config)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:  
        yield session  

def extract_timestamp(name):
    # Extract the timestamp using regex
    match = re.search(r'\d{10}', name)
    if match:
        return int(match.group())
    return None

def convert_timestamp_to_datetime(timestamp):
    date_time = datetime.datetime.fromtimestamp(timestamp)  
    return date_time.strftime('%Y-%m-%d %H:%M:%S')

def format_timestamp(seconds):
    # Convert seconds to hh:mm:ss.sss format
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

async def split_audio(file_path, segment_length_ms=60000):
    return await asyncio.to_thread(split_audio_sync, file_path, segment_length_ms)

def split_audio_sync(file_path, segment_length_ms=60000):
    from pydub import AudioSegment
    audio = AudioSegment.from_file(file_path)
    segments = []
    print("file_path---: ", file_path)
    suffix = file_path.replace('audios\\', '').replace('_p.mp3', '')
    for i in range(0, len(audio), segment_length_ms):
        segment = audio[i:i + segment_length_ms]
        segment_file = f"segment_{i // segment_length_ms}-{suffix}.mp3"
        segment.export(segment_file, format="mp3")
        segments.append((segment_file, i // segment_length_ms))  # Return file and its start time in minutes
    return segments

async def get_transcript_with_whisper(audio_file_path):
    # Split the audio into 1-minute segments
    audio_segments = await split_audio(audio_file_path)

    transcript = ""
    tasks = []
    for segment_file, segment_index in audio_segments:
        task = asyncio.create_task(process_segment_with_whisper(segment_file, segment_index))
        tasks.append(task)
    # Run transcription tasks concurrently
    results = await asyncio.gather(*tasks)
    # Combine transcripts
    transcript = "\n".join(results)
    return transcript

async def process_segment_with_whisper(segment_file, segment_index):
    print("process_segment_with_whisper --- start")
    segment_start_time = segment_index * 60
    temp = ""
    with open(segment_file, 'rb') as audio_file:
        response = await client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1",
            response_format="verbose_json",
            language="en"
        )
    if not response.segments:
        print("No segments found in the transcription.")
        return ""
    for segment in response.segments:
        start_time = segment['start'] + segment_start_time
        text = segment['text'].strip()
        timestamp = format_timestamp(start_time)
        temp += f"[{timestamp}] {text}\n"
    # Delete the temporary segment file after transcription
    os.remove(segment_file)
    print("process_segment_with_whisper --- success")
    return temp


async def get_transcript_with_assembly(audio_file_path):
    return await asyncio.to_thread(get_transcript_with_assembly_sync, audio_file_path)

def get_transcript_with_assembly_sync(audio_file_path):
    print("assembly---start")
    transcript = transcriber.transcribe(audio_file_path)

    if transcript.status == aai.TranscriptStatus.error:
        print(transcript.error)

    text_with_speaker = ''
    for utt in transcript.utterances:
        text_with_speaker += f"Speaker {utt.speaker}:\n{utt.text}\n"

    print("text_with_speaker: ", text_with_speaker)

    return text_with_speaker

default_prompt = """
Now the timestamp and transcript from whisper model is much accurate than from assembly.
But transcript from assembly ai has diarization.
So, I'm going to combine these two transcripts to get much more accurate transcript that is diarized.
The diarization of assembly could be not accurate so if you think it's not accurate, please modify it.
And even transcript from whisper ai coule be not accurate, so if you think it's not accurate, please modify it.

Provide me cleared, accurate conversation with timestamp and diarization.
Don't provide anything else that is not included in conversation.
"""

async def get_clear_conversation(db, whisper_transcript, assembly_transcript):
    variables = await crud.get_variables(db)
    prompt = variables.transcript_prompt if variables != None else ""

    if prompt == "":
        prompt = default_prompt

    # print("prmpt: ", prompt)
    response = await client.chat.completions.create(
        model='gpt-4o',
        max_tokens=4000,
        messages=[
            {'role': 'system', 'content': f"""
                {prompt}
                
                -----------------------------------
                This is the transcript of audio got from whisper model.

                {whisper_transcript}
                -----------------------------------
                -----------------------------------
                And this is the transcript of audio got from assembly ai model.
                
                {assembly_transcript}
                -----------------------------------

                
            """},
            {'role': 'user', 'content': f"""
                Provide me only conversation transcript with timestamp and diarization but without anything else like '''plain text, etc, 
            """}
        ],
        seed=2425,
        temperature = 0.7
    )
    cleared_conversation = response.choices[0].message.content

    return cleared_conversation

async def extract_subcategory(db, state, county, scanner_title, context):
    sub_categories = await crud.get_all_subcategories(db)
    instruction = get_prompt_for_alert_extraction(sub_categories, state, county, scanner_title)
    # print("instruction: ", instruction)
    response = await client.chat.completions.create(
        model='gpt-4o',
        max_tokens=4000,
        messages=[
            {'role': 'system', 'content': instruction},
            {'role': 'user', 'content': f"""
                Now, please categorize the following transcription.
                When extracting alerts, it's important to group alerts that share the same address.
                If you encounter multiple alerts associated with the same address, please combine them into a single, consolidated alert.
                This will ensure accurate and efficient reporting.
                ---------------------------------------
                Transcript:
                {context}
            """}
        ],
        seed=1123,
        temperature = 0.7,
        response_format={"type": "json_object"}
    )

    response_message = response.choices[0].message.content
    json_response = json.loads(response_message)
    print("json_response: ", json_response)
    return json_response['alerts']


async def get_potential_addresses(state, county, scanner_title, address):
    try:
        prompt = f"""
            I have an address input that might be incomplete or ambiguous. I need your help to generate multiple complete address suggestions (more than 7) in JSON format based on the provided data.
            These are the steps I need you to follow:

            Analyze the provided address data.
            Generate multiple potential complete addresses based on possible interpretations and nearby variations.
            Focus on the state, county, and scanner title (for city name) provided below.
            If a suitable address is not found in the specified city (scanner title), search surrounding cities in that region.
            Details:
            State: {state}
            County: {county}
            Scanner title (City): {scanner_title}
            Address Input: {address}

        """ + """
            Sample output format:
            {
                "addresses": [
                    {"address": "1802 W 9th St, Dixon, IL 61021"},
                    {"address": "1802 West Ninth Street, Dixon, IL 61021"},
                    // additional addresses...
                ]
            }
        """
        
        response = await client.chat.completions.create(
            model='gpt-4o',
            max_tokens=4000,
            messages=[
                {'role': 'system', 'content': "Generate multiple complete address suggestions in json."},
                {'role': 'user', 'content': prompt}
            ],
            seed=2425,
            temperature = 0.7,
            response_format={"type": "json_object"}
        )
        response_message = response.choices[0].message.content
        json_response = json.loads(response_message)
        return json_response
    except Exception as e:
        print(e)
        print("get_potential_addresses--------------")

async def process_archive(db, archive, purchased_scanner_id, state, county, scanner_title):
    audio_list = await crud.get_audio_by_filename(db, archive['filename'])
    audio = audio_list[-1] if audio_list else None
    transcript = ""
    if audio:
        print("********************************")
        print("filename: ", archive['filename'])
        timestamp = extract_timestamp(archive['filename'])
        dateTime = convert_timestamp_to_datetime(timestamp)
        cleared_conversation = await get_clear_conversation(db, audio.context, audio.assembly_transcript)
        print("origin: ", audio.cleared_context + '\n\n')
        print("cleared_conversation: ", cleared_conversation)
        await crud.update_audio(db, audio, archive['filename'], audio.context, audio.assembly_transcript, cleared_conversation, purchased_scanner_id, dateTime)
        transcript = cleared_conversation
        print("********************************")
    else:
        try:
            timestamp = extract_timestamp(archive['filename'])
            dateTime = convert_timestamp_to_datetime(timestamp)
            whisper_transcript = await get_transcript_with_whisper(archive['filename'])
            assembly_transcript = await get_transcript_with_assembly(archive['filename'])
            cleared_conversation = await get_clear_conversation(db, whisper_transcript, assembly_transcript)
            await crud.insert_audio(db, archive['filename'], whisper_transcript, assembly_transcript, cleared_conversation, purchased_scanner_id, dateTime)
            print("cleared_conversation: ", cleared_conversation)
            transcript = cleared_conversation
        except Exception as e:
            log.error(f"Failed to translate file {archive['filename']}: {e}")
            return

    alerts = await extract_subcategory(db, state, county, scanner_title, transcript)
    print("alerts: ", alerts)
    if alerts:
        for event in alerts:
            print('--------------------------')
            try:
                print('event: ', event)
                timestamp = extract_timestamp(archive['filename'])
                dateTime = convert_timestamp_to_datetime(timestamp)
                if "silence" in event['headline'].lower():
                    print("headline: ", event['headline'])
                    continue
                alert = await crud.insert_alert(db, purchased_scanner_id, event, dateTime)
                await crud.insert_sub_category(db, event['category'], event['sub-category'])
                if "incident_Address" in event and event['category'] == "Fire Alerts":
                    formatted_addresses = get_geocode_data(event['incident_Address'])
                    for result in formatted_addresses:
                        formatted_address = result.get('formatted_address')
                        type = validate_address(result)
                        score = get_score_by_location_type(result.get('geometry').get('location_type'))
                        if score == 1:
                            await send_new_alert_phone(alert, db, formatted_address)
                        contact_info = {}
                        await crud.insert_validated_address(
                            db,
                            formatted_address,
                            score,
                            alert.id,
                            type,
                            alert.scanner_id,
                            alert.dateTime,
                            contact_info,
                            0
                        )
            except Exception as e:
                print(e)
            print('++++++++++++++++++++++++++++')

async def stt_archive(db: AsyncSession, purchased_scanner_id, archive):  

    # Fetch the scanner by ID  
    scanner = await crud.get_scanner_by_scanner_id(db, purchased_scanner_id)  
    if not scanner:  
        log.error(f"Scanner with id {purchased_scanner_id} not found.")  
        return  

    state = scanner.state_name  
    county = scanner.county_name  
    scanner_title = scanner.scanner_title

    await process_archive(db, archive, purchased_scanner_id, state, county, scanner_title)