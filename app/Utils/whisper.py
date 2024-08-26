from openai import OpenAI, AsyncOpenAI
import logging as log
from sqlalchemy.ext.asyncio import AsyncSession  

from dotenv import load_dotenv
from database import AsyncSessionLocal
import assemblyai as aai

import app.Utils.crud as crud
from app.Utils.validate_address import validate_address
from app.Utils.get_geocode_data import get_geocode_data, get_score_by_location_type
import json
import re
import datetime
from typing import AsyncGenerator  

load_dotenv()

client = AsyncOpenAI()
aai.settings.api_key = "cc1f8ebab99e4efd851e27e242652e5a"

config = aai.TranscriptionConfig(speaker_labels=True)
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

async def ai_translate(audio_file_path):
    # model = whisper.load_model("medium.en")
    # print(f"STT for {audio_file_path}")
    # result = model.transcribe(audio_file_path, fp16=False)

    # pprint(result)
    # something not good here
    # print(audio_file_path)
    transcript = transcriber.transcribe(audio_file_path)
    print(transcript.text)
    print(transcript.utterances)

    if transcript.status == aai.TranscriptStatus.error:
        print(transcript.error)

    text_with_speaker = ''
    for utt in transcript.utterances:
        text_with_speaker += f"Speaker {utt.speaker}:\n{utt.text}\n"

    # audio_file= open(audio_file_path, "rb")
    # transcription = await client.audio.transcriptions.create(
    #     model="whisper-1", 
    #     file=audio_file,
    #     language="en"
    # )
    
    # print(f"STT DONE for {audio_file_path}")
    return text_with_speaker

def add_sub_category(sub_categories, category, text):
    for sub_category in sub_categories:
        if sub_category.category == category:
            text += sub_category.sub_category + '\n'
    return text + '\n'

async def extract_subcategory(db, state, county, scanner_title, context):
    sub_categories = await crud.get_all_subcategories(db)

    category_prompt = '1. Fire Alerts: \n'
    category_prompt = add_sub_category(sub_categories, "Fire Alerts", category_prompt)
    
    category_prompt += '2. Police Dispatcs: \n'
    category_prompt = add_sub_category(sub_categories, "Police Dispatch", category_prompt)
    
    category_prompt += '3. Medical Emergencies: \n'
    category_prompt = add_sub_category(sub_categories, "Medical Emergencies", category_prompt)
    
    
    category_prompt += '4. Miscellaneous (MISC): \n'
    category_prompt = add_sub_category(sub_categories, "Miscellaneous (MISC)", category_prompt)
    
    print(category_prompt)

    instruction = f"""
        Task: Generate a structured notification/report about an event based on an audio transcription containing various types of communication, including scanner communications, police dispatches, calls, and conversations in JSON format.

        Here are the existing sub-categories for each main category:

        {category_prompt}

        Instructions:
            You are required to categorize each segment of the transcription into one of the following four main categories: Fire Alerts, Police Dispatch, Medical Emergencies, and Miscellaneous (MISC). Each main category must be further broken down into detailed and specific sub-categories.

            Additional Instructions:
                Review the existing sub-categories and suggest any additional sub-categories that could enhance the specificity and comprehensiveness of each main category.
                Create new sub-categories if you identify gaps that warrant further classification, ensuring they align closely with the potential alerts in their respective areas.
                You shouldn't output unknown for sub-category but instead, you need to create new sub-category if you didn't find suitable category in existing examples.
                Format Output: Structure your output in the following JSON format, ensuring each notification/report is complete:""" +  """

                    {  
                        "alerts": [
                            {  
                                "category": "<Main Category>", // Choose one from the four main categories  
                                "sub-category": "<Sub-Category>", // Choose from given examples or create your own  
                                "headline": "<Title of the event occurred>", // Include 'false' in the title if it's a false alarm  
                                "description": "<Segment of Transcription>", // Provide relevant context  
                                "incident_Address": "<Address of event occurred>" // Specify the location of the incident. Extract standardized and structured address that contains county, city name.
                            }  
                        ]  
                    }  

    """

    instruction += f"""
        Note for Incident Addresses: When you extract Incident_Address, please reference the following:

        State Name: {state}
        County Name: {county}
        Scanner Title: {scanner_title}
        Extract and clearly state the formatted street address of the event from the provided text. Make sure the address is as standardized and structured as possible, ideally including street number, street name, city, state, and ZIP code. Don't forget to contain county name and state name.
        Don't forget to contain county name and state name.
    """

    response = await client.chat.completions.create(
        model='gpt-4o',
        max_tokens=4000,
        messages=[
            {'role': 'system', 'content': instruction},
            {'role': 'user', 'content': f"""
                Now, please categorize the following transcription:
                Transcription:
                {context}
            """}
        ],
        seed=2425,
        temperature = 0.7,
        response_format={"type": "json_object"}
    )

    response_message = response.choices[0].message.content
    json_response = json.loads(response_message)
    # print("json_response: ", json_response)
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
   

async def stt_archive(db: AsyncSession, purchased_scanner_id, archive_list):  

    # Fetch the scanner by ID  
    scanner = await crud.get_scanner_by_scanner_id(db, purchased_scanner_id)  
    if not scanner:  
        log.error(f"Scanner with id {purchased_scanner_id} not found.")  
        return  

    state = scanner.state_name  
    county = scanner.county_name  
    scanner_title = scanner.scanner_title  

    for archive in archive_list:  
        audio = await crud.get_audio_by_filename(db, archive['filename'])  
        transcript = ""  
        if audio and audio.context:  
            transcript = audio.context
            continue
        else:  
            try:  
                transcript = await ai_translate(archive['filename'])
                print("transcript: ", transcript)
                timestamp = extract_timestamp(archive['filename'])  
                dateTime = convert_timestamp_to_datetime(timestamp)  
                await crud.insert_audio(db, archive['filename'], transcript, purchased_scanner_id, dateTime)  
            except Exception as e:  
                log.error(f"Failed to translate file {archive['filename']}: {e}")  
                continue  
    
        alerts = await extract_subcategory(db, state, county, scanner_title, transcript)
        print("alerts: ", alerts)
        if alerts:
            for event in alerts:
                print('--------------------------')
                try:
                    print('event: ', event)
                    timestamp = extract_timestamp(archive['filename'])  
                    dateTime = convert_timestamp_to_datetime(timestamp)
                    alert = await crud.insert_alert(db, purchased_scanner_id, event, dateTime)
                    await crud.insert_sub_category(db, event['category'], event['sub-category'])

                    if "incident_Address" in event:
                        # addresses = await get_potential_addresses(state, county, scanner_title, event['incident_Address'])
                        # results = validate_address(event['incident_Address'])
                        formatted_addresses = get_geocode_data(event['incident_Address'])
                        for result in formatted_addresses:
                            formatted_address = result.get('formatted_address')
                            score = get_score_by_location_type(result.get('geometry').get('location_type'))
                            await crud.insert_validated_address(
                                db,
                                formatted_address,
                                score,
                                alert.id
                            )
                except Exception as e:
                    print(e)
                    
                print('++++++++++++++++++++++++++++')