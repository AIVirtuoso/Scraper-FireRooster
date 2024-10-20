from twilio.rest import Client
from sqlalchemy.orm import Session
from database import AsyncSessionLocal
from dotenv import load_dotenv
from datetime import datetime
import os
from urllib.parse import quote

load_dotenv()
      
        
twilioPhoneNumber = os.getenv("TWILIO_PHONE_NUMBER")
twilioAccountSID = os.getenv("TWILIO_ACCOUNT_SID")
twilioAuthToken = os.getenv("TWILIO_AUTH_TOKEN")


# async def getTwilioCredentials(db: Session):
#     variables = await crud.get_variables(db)
#     number = ''
#     sid = ''
#     token = ''
#     if variables:
#         number = variables.twilioPhoneNumber or twilioPhoneNumber
#         sid = variables.twilioAccountSID or twilioAccountSID
#         token = variables.twilioAuthToken or twilioAuthToken
#     else:
#         number = twilioPhoneNumber
#         sid = twilioAccountSID
#         token = twilioAuthToken
#     return number, sid, token


def send_new_alert_phone(alert, db: Session, formatted_address):
    # twilioPhoneNumber, twilioAccountSID, twilioAuthToken = await getTwilioCredentials(db)
    
    # Initialize the Twilio client
    client = Client(twilioAccountSID, twilioAuthToken)
    encoded_sub_category = quote(alert.sub_category.replace('/', '-'))
    link = f"https://rooster.report/dashboard/scanners/{alert.scanner_id}/alert/{encoded_sub_category}/{alert.id}"

    star = ""
    for i in range(0, alert.rating):
        star += "(star) "
    body = f"""
New structure alert confirmed!
{alert.headline} ({alert.sub_category})

Rating: {alert.rating} {star}

Address:         {formatted_address}

Description:
{alert.description}

Link to web:     {link}
"""

    print("body: ", body)

    message = client.messages.create(
        to="+17735179242", 
        from_=twilioPhoneNumber,
        body=body
    )
    print("send message: ", message)
    message = client.messages.create(
        to="+1 320 547 1980", 
        from_=twilioPhoneNumber,
        body=body
    )

    # Optionally print the message SID
