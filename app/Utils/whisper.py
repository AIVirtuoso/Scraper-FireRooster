from openai import OpenAI, AsyncOpenAI
import logging as log
from sqlalchemy.ext.asyncio import AsyncSession  

from dotenv import load_dotenv
from database import AsyncSessionLocal

import app.Utils.crud as crud
from app.Utils.validate_address import validate_address
import json
import re
import datetime
from typing import AsyncGenerator  

load_dotenv()

client = AsyncOpenAI()

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
    audio_file= open(audio_file_path, "rb")
    transcription = await client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file,
        language="en"
    )
    
    # print(f"STT DONE for {audio_file_path}")
    return transcription.text

async def extract_info_from_context(state, county, scanner_title, context):
    instruction = f"""
Task: Generate a general notification/report about the event mentioned in the given context in JSON format.

Instructions:

I have a transcription of audio data containing different types of communication, including scanner communications, police dispatches, calls, and conversations.
Categorize each segment of the transcription accordingly.
Separate the Police/Fire Scanner Codes used by dispatchers so they are not confused with addresses.
If more than one address is given, ensure they all belong to the same dispatch.
Be careful not to assign more than one address to a single dispatch, as multiple dispatches might be sent out for different officers with different addresses one after the other.

Examples:

Transcription: “911, what’s your emergency?”
Output: [Call]: 911, what’s your emergency?

Transcription: “Unit 5, proceed to 123 Main St. over.”
Output: [Police Dispatch]: Unit 5, proceed to 123 Main St. over.

Transcription: “10-4, Unit 5. Report to 456 Elm St.”
Output: [Police Dispatch]: 10-4, Unit 5. Report to 456 Elm St.

Transcription: “Fire at 789 Pine St. Engine 2, respond. 10-70, fire alarm.”
Output: [Fire Dispatch]: Fire at 789 Pine St. Engine 2, respond.
[Scanner Code]: 10-70, fire alarm.

Transcription: “Engine 3, respond to the intersection of Oak St and Maple Ave. 11-16, chief’s request.”
Output: [Fire Dispatch]: Engine 3, respond to the intersection of Oak St and Maple Ave.
[Scanner Code]: 11-16, chief’s request.

Transcription: “Possible brush fire near the corner of 5th Ave and Main St. 11-18, brush fire.”
Output: [Fire Dispatch]: Possible brush fire near the corner of 5th Ave and Main St.
[Scanner Code]: 11-18, brush fire.

Transcription: “Unit 2, proceed to 34th St between Park Ave and Lexington Ave. 10-75, in contact with...”
Output: [Police Dispatch]: Unit 2, proceed to 34th St between Park Ave and Lexington Ave.
[Scanner Code]: 10-75, in contact with...

Transcription: “Multiple car fire in the parking lot behind 678 Elm St. 11-19, vehicle fire.”
Output: [Fire Dispatch]: Multiple car fire in the parking lot behind 678 Elm St.
[Scanner Code]: 11-19, vehicle fire.

Transcription: “Smoke report at the junction of 12th St and Pine Ave. 10-73, smoke report.”
Output: [Fire Dispatch]: Smoke report at the junction of 12th St and Pine Ave.
[Scanner Code]: 10-73, smoke report.

Transcription: “Report of a structure fire at 345 Maple Dr. 11-20, structure fire.”
Output: [Fire Dispatch]: Report of a structure fire at 345 Maple Dr.
[Scanner Code]: 11-20, structure fire.

Note for Incident Addresses: When you extract Incident_Address, please reference the following:

State Name: {state}
County Name: {county}
Scanner Title: {scanner_title}


Dispatch Codes: Here are the dispatch codes you need to distinguish between dispatch codes and addresses:
""" + """
{
   "dispatch_codes":{
      "10-Codes":{
         "10-1":"Signal Weak",
         "10-2":"Signal Good",
         "10-3":"Stop Transmitting",
         "10-4":"Acknowledgment (OK)",
         "10-5":"Relay",
         "10-6":"Busy",
         "10-7":"Out of Service",
         "10-8":"In Service",
         "10-9":"Repeat",
         "10-10":"Negative",
         "10-11":"On Duty",
         "10-12":"Stand By",
         "10-13":"Existing Conditions",
         "10-14":"Message/Information",
         "10-15":"Message Delivered",
         "10-16":"Reply to Message",
         "10-17":"En Route",
         "10-18":"Urgent",
         "10-19":"(In) Contact",
         "10-20":"Location",
         "10-21":"Call (by Telephone)",
         "10-22":"Disregard",
         "10-23":"Arrived at Scene",
         "10-24":"Assignment Completed",
         "10-25":"Report to (Meet)",
         "10-26":"Estimated Arrival Time",
         "10-27":"License/Permit Information",
         "10-28":"Ownership Information",
         "10-29":"Records Check",
         "10-30":"Danger/Caution",
         "10-31":"Pick Up",
         "10-32":"Units Needed",
         "10-33":"Emergency",
         "10-34":"Correct Time",
         "10-35":"Confidential Information",
         "10-36":"Correct Time",
         "10-37":"Investigate Suspicious Vehicle",
         "10-38":"Stopping Suspicious Vehicle",
         "10-39":"Urgent – Use Lights/Siren",
         "10-40":"Silent Run – No Lights/Siren",
         "10-41":"Beginning Tour of Duty",
         "10-42":"Ending Tour of Duty",
         "10-43":"Information",
         "10-44":"Permission to Leave",
         "10-45":"Animal Carcass",
         "10-46":"Assist Motorist",
         "10-47":"Emergency Road Repair",
         "10-48":"Traffic Control",
         "10-49":"Traffic Light Out",
         "10-50":"Accident",
         "10-51":"Wrecker Needed",
         "10-52":"Ambulance Needed",
         "10-53":"Road Blocked",
         "10-54":"Livestock on Highway",
         "10-55":"Intoxicated Driver",
         "10-56":"Intoxicated Pedestrian",
         "10-57":"Hit and Run",
         "10-58":"Direct Traffic",
         "10-59":"Convoy/Escort",
         "10-60":"Squad in Vicinity",
         "10-61":"Personnel in Area",
         "10-62":"Reply to Message",
         "10-63":"Prepare to Make Written Copy",
         "10-64":"Message for Local Delivery",
         "10-65":"Net Message Assignment",
         "10-66":"Message Cancellation",
         "10-67":"Clear to Read/Copy",
         "10-68":"Dispatch Information",
         "10-69":"Message Received",
         "10-70":"Fire Alarm",
         "10-71":"Proceed with Transmission",
         "10-72":"Report Progress of Fire",
         "10-73":"Smoke Report",
         "10-74":"Negative",
         "10-75":"In Contact with",
         "10-76":"En Route",
         "10-77":"Estimated Time of Arrival",
         "10-78":"Need Assistance",
         "10-79":"Notify Coroner",
         "10-80":"Chase in Progress",
         "10-81":"Breathalyzer Report",
         "10-82":"Reserve Lodging",
         "10-83":"Work School Crossing",
         "10-84":"If Meeting",
         "10-85":"Delayed Due to",
         "10-86":"Operator on Duty",
         "10-87":"Pick Up/Distribute Checks",
         "10-88":"Advise Present Telephone Number",
         "10-89":"Bomb Threat",
         "10-90":"Bank Alarm",
         "10-91":"Unnecessary Use of Radio",
         "10-92":"Improper Use of Radio",
         "10-93":"Blockage",
         "10-94":"Drag Racing",
         "10-95":"Prisoner/Subject in Custody",
         "10-96":"Mental Subject",
         "10-97":"Check (Test) Signal",
         "10-98":"Prison/Jail Break",
         "10-99":"Wanted/Stolen",
         "10-100":"Dead Body Found"
      },
      "11-Codes":{
         "11-6": "Illegal discharge of firearms", "11-7":"Prowler",
         "11-8": "Person down", "11-10":"Take a report",
         "11-12": "Dead animal", "11-13":"Injured animal",
         "11-14": "Dog bite", "11-15":"Ball game in street",
         "11-17": "Injured person", "11-18":"Missing person",
         "11-19": "Trespasser", "11-20":"Vehicle accident",
         "11-21": "Petty theft", "11-24":"Abandoned vehicle",
         "11-25": "Traffic hazard", "11-26":"Abandoned bicycle",
         "11-27": "Return phone call", "11-28":"Registration check",
         "11-29": "No want", "11-30":"Incomplete phone call",
         "11-31": "Calling for help", "11-32":"Defective radio",
         "11-33": "Emergency traffic", "11-34":"Open door or window",
         "11-35": "Ballgame in progress", "11-36":"Time check",
         "11-37": "Unit involved in accident", "11-38":"Request assistance",
         "11-39": "Officer’s call", "11-40":"Advise if available",
         "11-41": "Advise if in service", "11-42":"Continue",
         "11-43": "Returning to station", "11-44":"All units hold traffic",
         "11-45": "All units resume normal traffic", "11-48":"Transportation needed",
         "11-50": "Monitor your radio", "11-51":"Escort",
         "11-52": "Funeral detail", "11-54":"Suspicious vehicle",
         "11-55": "Officer needs back-up", "11-56":"Missing person – adult",
         "11-57": "Missing person – child", "11-58":"Intoxicated subject",
         "11-59": "Security check", "11-60":"Request for prisoner transportation",
         "11-65": "Signal", "11-66":"Signal out of order",
         "11-68": "Record indicated", "11-70":"Fire",
         "11-71": "Shooting", "11-80":"Major accident",
         "11-81": "Minor accident", "11-82":"Property damage accident",
         "11-83": "No details", "11-84":"Direct traffic",
         "11-85": "Tow truck required", "11-86":"Special detail",
         "11-87": "Abandoned vehicle", "11-88":"Citizen assist"
      },
      "Common Fire and Medical Codes":{
         "Code 1":"Non-urgent response",
         "Code 2":"Urgent response",
         "Code 3":"Emergency response with lights and sirens",
         "Code 4":"No further assistance needed",
         "Code 5":"Stakeout",
         "Code 6":"Respond to dispatch",
         "Code 7":"Meal break",
         "Code 8":"Non-emergency call",
         "Code 9":"Pre-arrival instructions",
         "Code 10":"Stand by",
         "Code 11":"Individual units or officers",
         "Code 12":"Requesting additional resources"
      }
   }
}


Please provide the output in the following format:
{
    "alerts": [
        {
            "communication": <Type of Communication> (you have to decide type of communication by analyzing the transcr),
            "headline": <title of event occured> (if your fire alarm is false, in other word, if it's not real fire accident, must include 'false' word in headline),
            "description": <Segment of Transcription>,
            "incident_Address": <Address of event occured>,
        },
    ]
}

"""
    
    functions = [
        {
            "name": 'extract_info',
            "description": instruction,
            'parameters': {
                'type': "object",
                "properties":{
                    "event":{
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'Headline': {
                                    'type': 'string',
                                    'description': "A specified headline focusing on the main event."
                                },
                                "Description": {
                                    'type': 'string',
                                    'description': "Over 5 sentences (over 200 words) of professional and informative description of the event, based on the provided context. This description should be provided in detail with over 5 sentences only based on the context."
                                },
                                "Incident_Address": {
                                    'type': 'string',
                                    'description': "Extract and clearly state the formatted street address of the event from the provided text. Make sure the address is as standardized and structured as possible, ideally including street number, street name, city, state, and ZIP code."
                                },
                                "Communication": {
                                    'type': 'string',
                                    'description': "Type of Communication"
                                }
                            }
                        },
                        "required": ["Headline", "Description", "Incident_Address", "Communication"]
                    }
                }
            },
            "required": ["event"]
        }
    ]
    
    try:
        
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
            # functions=functions,
            # function_call={"name": "extract_info"}
            response_format={"type": "json_object"}
        )

        response_message = response.choices[0].message.content
        json_response = json.loads(response_message)
        # print("json_response: ", json_response)
        return json_response

        # response_message = response.choices[0].message
        # system_fingerprint = response.system_fingerprint
        # print(system_fingerprint)

        # if hasattr(response_message, "function_call"):
        #     json_response = json.loads(
        #         response_message.function_call.arguments)
        #     print("json_response: ", json_response)
        #     return json_response
        # else:
        #     print("function_call_error!\n")
        #     return {}
    except Exception as e:
        print(e)
        print("--------------")
        

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
        else:  
            try:  
                transcript = await ai_translate(archive['filename'])  
                timestamp = extract_timestamp(archive['filename'])  
                dateTime = convert_timestamp_to_datetime(timestamp)  
                await crud.insert_audio(db, archive['filename'], transcript, purchased_scanner_id, dateTime)  
            except Exception as e:  
                log.error(f"Failed to translate file {archive['filename']}: {e}")  
                continue  
    
        response = await extract_info_from_context(state, county, scanner_title, transcript)
        print("response: ", response)
        if response:  
            alerts = response['alerts']  
            for event in alerts:
                if 'communication' in event and event['communication'] == 'Fire Dispatch':
                    print('--------------------------')
                    print('event: ', event)
                    if 'headline' in event and 'false' in event['headline']:
                        continue
                    timestamp = extract_timestamp(archive['filename'])  
                    dateTime = convert_timestamp_to_datetime(timestamp)
                    alert = await crud.insert_alert(db, purchased_scanner_id, event, dateTime)

                    if "incident_Address" in event:
                        addresses = await get_potential_addresses(state, county, scanner_title, event['incident_Address'])  
                        results = validate_address(addresses)  
                        sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)  
                        print("sorted_results: ", sorted_results)
                        
                        for result in sorted_results[:3]:  
                            await crud.insert_validated_address(db, result['address'], result['score'], alert.id)  
                    print('++++++++++++++++++++++++++++')