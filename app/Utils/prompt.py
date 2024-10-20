
dispatch_code_prompt = """
{ "dispatch_codes":{ "10-Codes":{ "10-1":"Signal Weak", "10-2":"Signal Good", "10-3":"Stop Transmitting", "10-4":"Acknowledgment (OK)", "10-5":"Relay", "10-6":"Busy", "10-7":"Out of Service", "10-8":"In Service", "10-9":"Repeat", "10-10":"Negative", "10-11":"On Duty", "10-12":"Stand By", "10-13":"Existing Conditions", "10-14":"Message/Information", "10-15":"Message Delivered", "10-16":"Reply to Message", "10-17":"En Route", "10-18":"Urgent", "10-19":"(In) Contact", "10-20":"Location", "10-21":"Call (by Telephone)", "10-22":"Disregard", (if a 10-22 is called after an address please address this by deleting the address and looking for the next address. Repeat this for all 10-22 calls) "10-23":"Arrived at Scene", "10-24":"Assignment Completed", "10-25":"Report to (Meet)", "10-26":"Estimated Arrival Time", "10-27":"License/Permit Information", "10-28":"Ownership Information", "10-29":"Records Check", "10-30":"Danger/Caution", "10-31":"Pick Up", "10-32":"Units Needed", "10-33":"Emergency", "10-34":"Correct Time", "10-35":"Confidential Information", "10-36":"Correct Time", "10-37":"Investigate Suspicious Vehicle", "10-38":"Stopping Suspicious Vehicle", "10-39":"Urgent – Use Lights/Siren", "10-40":"Silent Run – No Lights/Siren", "10-41":"Beginning Tour of Duty", "10-42":"Ending Tour of Duty", "10-43":"Information", "10-44":"Permission to Leave", "10-45":"Animal Carcass", "10-46":"Assist Motorist", "10-47":"Emergency Road Repair", "10-48":"Traffic Control", "10-49":"Traffic Light Out", "10-50":"Accident", "10-51":"Wrecker Needed", "10-52":"Ambulance Needed", "10-53":"Road Blocked", "10-54":"Livestock on Highway", "10-55":"Intoxicated Driver", "10-56":"Intoxicated Pedestrian", "10-57":"Hit and Run", "10-58":"Direct Traffic", "10-59":"Convoy/Escort", "10-60":"Squad in Vicinity", "10-61":"Personnel in Area", "10-62":"Reply to Message", "10-63":"Prepare to Make Written Copy", "10-64":"Message for Local Delivery", "10-65":"Net Message Assignment", "10-66":"Message Cancellation", "10-67":"Clear to Read/Copy", "10-68":"Dispatch Information", "10-69":"Message Received", "10-70":"Fire Alarm", "10-71":"Proceed with Transmission", "10-72":"Report Progress of Fire", "10-73":"Smoke Report", "10-74":"Negative", "10-75":"In Contact with", "10-76":"En Route", "10-77":"Estimated Time of Arrival", "10-78":"Need Assistance", "10-79":"Notify Coroner", "10-80":"Chase in Progress", "10-81":"Breathalyzer Report", "10-82":"Reserve Lodging", "10-83":"Work School Crossing", "10-84":"If Meeting", "10-85":"Delayed Due to", "10-86":"Operator on Duty", "10-87":"Pick Up/Distribute Checks", "10-88":"Advise Present Telephone Number", "10-89":"Bomb Threat", "10-90":"Bank Alarm", "10-91":"Unnecessary Use of Radio", "10-92":"Improper Use of Radio", "10-93":"Blockage", "10-94":"Drag Racing", "10-95":"Prisoner/Subject in Custody", "10-96":"Mental Subject", "10-97":"Check (Test) Signal", "10-98":"Prison/Jail Break", "10-99":"Wanted/Stolen", "10-100":"Dead Body Found" }, "11-Codes":{ "11-6": "Illegal discharge of firearms", "11-7":"Prowler", "11-8": "Person down", "11-10":"Take a report", "11-12": "Dead animal", "11-13":"Injured animal", "11-14": "Dog bite", "11-15":"Ball game in street", "11-17": "Injured person", "11-18":"Missing person", "11-19": "Trespasser", "11-20":"Vehicle accident", "11-21": "Petty theft", "11-24":"Abandoned vehicle", "11-25": "Traffic hazard", "11-26":"Abandoned bicycle", "11-27": "Return phone call", "11-28":"Registration check", "11-29": "No want", "11-30":"Incomplete phone call", "11-31": "Calling for help", "11-32":"Defective radio", "11-33": "Emergency traffic", "11-34":"Open door or window", "11-35": "Ballgame in progress", "11-36":"Time check", "11-37": "Unit involved in accident", "11-38":"Request assistance", "11-39": "Officer's call", "11-40":"Advise if available", "11-41": "Advise if in service", "11-42":"Continue", "11-43": "Returning to station", "11-44":"All units hold traffic", "11-45": "All units resume normal traffic", "11-48":"Transportation needed", "11-50": "Monitor your radio", "11-51":"Escort", "11-52": "Funeral detail", "11-54":"Suspicious vehicle", "11-55": "Officer needs back-up", "11-56":"Missing person – adult", "11-57": "Missing person – child", "11-58":"Intoxicated subject", "11-59": "Security check", "11-60":"Request for prisoner transportation", "11-65": "Signal", "11-66":"Signal out of order", "11-68": "Record indicated", "11-70":"Fire", "11-71": "Shooting", "11-80":"Major accident", "11-81": "Minor accident", "11-82":"Property damage accident", "11-83": "No details", "11-84":"Direct traffic", "11-85": "Tow truck required", "11-86":"Special detail", "11-87": "Abandoned vehicle", "11-88":"Citizen assist" }, "Common Fire and Medical Codes":{ "Code 1":"Non-urgent response", "Code 2":"Urgent response", "Code 3":"Emergency response with lights and sirens", "Code 4":"No further assistance needed", "Code 5":"Stakeout", "Code 6":"Respond to dispatch", "Code 7":"Meal break", "Code 8":"Non-emergency call", "Code 9":"Pre-arrival instructions", "Code 10":"Stand by", "Code 11":"Individual units or officers", "Code 12":"Requesting additional resources" } } }
"""

def add_sub_category(sub_categories, category, text):
    for sub_category in sub_categories:
        if sub_category.category == category:
            text += sub_category.sub_category + '\n'
    return text + '\n'


def get_prompt_for_alert_extraction(sub_categories, state, county, scanner_title):
    category_prompt = '1. Fire Alerts: \n'
    category_prompt = add_sub_category(sub_categories, "Fire Alerts", category_prompt)
    
    category_prompt += '2. Police Dispatcs: \n'
    category_prompt = add_sub_category(sub_categories, "Police Dispatch", category_prompt)
    
    category_prompt += '3. Medical Emergencies: \n'
    category_prompt = add_sub_category(sub_categories, "Medical Emergencies", category_prompt)
    
    
    category_prompt += '4. Miscellaneous (MISC): \n'
    category_prompt = add_sub_category(sub_categories, "Miscellaneous (MISC)", category_prompt)

    prompt = f"""
Task: Generate a structured notification/report based on an audio transcription containing various types of communication, including scanner communications, police dispatches, fire dispatches, medical emergencies, and conversations in JSON format.

Instructions:
1. Handling Multiple Calls and Fires:
    * Silence Detection: Recognize silence indicators (e.g., "silence 7 seconds") as markers for separating conversations. Silence indicates the potential boundary between distinct conversations or calls.
    * Multiple Conversations: A single transcript may contain multiple fire incidents or calls to different locations. Separate each conversation based on context and silence markers. Each separated conversation must be processed as a distinct call or incident.
    * Overlapping Conversations: In some cases, multiple incidents may overlap within the same transcript. These should be separated by context (e.g., different locations, different units responding), ensuring each event is correctly categorized.
2. Categorization:
    * For each segment of the transcription (separated by silence or context), categorize the communication into one of the following main categories:
        * Fire Alerts
        * Police Dispatch
        * Medical Emergencies
        * Miscellaneous (MISC)
    * Further break down each category into sub-categories specific to the event, such as:
        * Fire Alerts: "Structure Fire," "Wildfire," "False Alarm."
        * Police Dispatch: "Traffic Accident," "Suspicious Activity," "Crime in Progress."
        * Medical Emergencies: "Cardiac Arrest," "Fall Injury," "Respiratory Distress."
        * Miscellaneous: Catch-all for any communications that don't fit into the other categories.
    * New Sub-Categories: If existing sub-categories are insufficient, create new sub-categories based on the event context.
    These are existing sub-categories you can refer to.
    {category_prompt}

3. Code Handling:
    * Separate and Identify Codes: Ensure all scanner codes (e.g., 10-70, 10-4) are categorized separately from addresses or other information. Codes should be applied to the relevant call or event.
    * Convert Dispatch Codes: Convert police, fire, and medical dispatch codes (e.g., 10-Codes, 11-Codes, and Common Fire and Medical Codes) into their natural language equivalents for better understanding and processing.
    Here are the codes to watch for:
    {dispatch_code_prompt}

4. Address Handling:
    * Multiple Addresses: If more than one address is mentioned, ensure that each belongs to the appropriate dispatch. Avoid assigning more than one address to a single dispatch unless it is a continuation of the same incident.
    * Directional Prefixes: Be aware of possible directional prefixes (e.g., North, South, East, West) and ensure the correct version is selected.
    * Omit Invalid Addresses: If a 10-22 code (Disregard) is called after an address, remove that address and look for the next valid one.

5. Incident Analysis:
    * For each Fire Alert, provide:
        * The exact location and address of the fire.
        * A summary of the fire, including the building type, the number of floors affected, and key firefighting efforts.
        * An assessment of potential loss, considering damage extent, property value, resources deployed, and collateral damage.
        * Rate the fire severity on a scale from 1 to 5 using the Fire Incident Severity Rating System.

    List of types of units and how to handle them during rating. When reading the transcript be sure to notice how many and which type of vehicles are being dispatched to a fire. 

    Scoring System for Unit Relevancy to Large Fires:

    1. Critical to large fire response
        * Engine (water): Essential for supplying water to fight the fire.
        * Ladder (Tower): Vital for reaching high floors and attacking fires in multi-story buildings.
        * Quint (engine + ladder): Combines engine and ladder functions, crucial for both water supply and reaching high areas.
        * Battalion (chief vehicle): Battalion chiefs coordinate firefighting efforts, especially for large-scale incidents.
        * Rescue Squad: Specialized in life-saving and rescue operations, essential in large-scale fire scenarios.

    2. Very important, but more specialized
        * Tanker: Provides additional water supply, especially in areas without hydrants.
        * Haz Mat: Important if hazardous materials are involved, but not always needed in a basic large fire.
        * Fire Investigation Unit: Helps determine cause and prevent future incidents, relevant after the fire is under control.
        * Technical Rescue: Needed for complex rescue scenarios in large fire situations, such as structural collapses.

    Support roles, useful but not always critical
        * Ambulance: Necessary for medical emergencies during large fires, but not directly involved in firefighting.
        * Mobile Command: Helps coordinate operations, very useful in large-scale operations, but secondary to fire suppression efforts.
        * Brush: Crucial for wildfires or brush fires, but less relevant in urban or structural fires.
        * Dive: Relevant if there are water-related rescues involved, but not typically required in standard large fires.
        * Utility: Provides various support services, useful but not essential for large-scale fire response.
        * Boats: Important for fires near water or requiring water rescues but not common in structural fires.

    Limited relevancy
        * Polaris: Used for off-road or hard-to-reach areas, not typically used for large urban fires.
        * Chevy Suburban: Mainly used for transportation, not directly involved in firefighting.
        * Twin: May have specific applications but generally not critical to large fire responses.
        * Command: Provides command support but typically secondary to direct firefighting units.

    Least relevant
        * Agent: Less relevant to large fires unless dealing with specialized circumstances.
        *  Quad: May be useful in limited capacities but is not a primary firefighting tool.


6. Fire Incident Severity Rating System:
    Rating 5: Major Fire Incident (Strict Criteria)
        Key Indicators:

        Clear Fire Presence with Significant Damage:

        There must be a visible and confirmed fire that is causing major damage to high-value or large-scale properties.
        Dispatches should include terms such as:
        Still, Still Box, Working Fire, Smoke Visible, Smell Smoke, or Defensive Operations, Line On, Line Off, Fire Spreading, Fire Walkthrough. 
        These terms indicate significant fire activity and often signal large-scale responses, such as street closures and deployment of more than 5 units.

        Extensive Firefighting Effort:
        Active fire suppression efforts should be evident, including the use of hoses with high pressure. Look for phrases like: 550 on line one, two lines on, lines on, or working fire.
        There is confirmed use of multiple fire suppression lines, indicating a serious firefighting effort.

        Mutual Aid and Specialized Units:

        Multiple fire departments or agencies must be involved, providing mutual aid. Specialized units such as:
        Hazmat, high-rise units, technical rescue teams may be deployed.
        Dispatch terms like Box Alarm, Strike Team, or Task Force indicate a coordinated response involving several agencies to manage the fire.

        Complex or High-Risk Scenarios:
        The fire occurs in high-risk areas, such as:
        Commercial buildings, factories, high-rise buildings, or locations with flammable materials.
        These fires have a high potential to spread or escalate due to the location or the contents of the building.
        Dispatch phrases like Exposure Concern may indicate that nearby structures are at risk from the spreading fire.

        Clearly Stated Address:
        The address of the fire must be clearly communicated by the dispatcher and accurately reflect the fire’s location.

        Other Important Characteristics:
        The fire has spread significantly, and there is a clear threat to more than just the building of origin.
        Dispatches are highly detailed, often involving specialized units like hazmat or technical rescue teams.
        Street closures are likely to occur to accommodate large-scale firefighting operations.
        Multiple battalions and over 8 fire units are called out simultaneously, signaling a need for overwhelming resources. 

        Example of a 5-Star Dispatch:
        "Structure fire. District 1037. 1316 Battlefield Road (corrected to Butterfield Road), Downers Grove. Battalion 100. Battalion 44. Chief 101. Chief 183. Deputy 102. Deputy 103. Engine 103. Engine 55. Medic 102. Medic 103. Medic 55. Squad 101. Tower 102. Tower 44. Tower 94. Rockjaw. Rocktree. The beach. Battlefield Road (corrected to Butterfield Road). Downers Drive. "They smell and see smoke in the back room. No flames visible."

        Key Phrases: They Smell Smoke, No Flames Visible

        Contextual Rule:
        Rating 5 cannot be assigned solely based on the number of units dispatched (Except in rare cases where more than 5+ units are dispatched and/or multiple battalions are dispatched).

        Additional contextual details must be present:
        Active fire suppression, confirmed fire severity, high-value or high-risk property type, and dispatch terminology indicating serious incidents (e.g., Still Box, Working Fire, Smell Smoke, or Visible Flame and/or Smoke).

        Most or all of the above criteria must be met for a fire to be rated as 5 stars. 

    Rating 4: Serious Fire Incident
        * Fire Present with Potential for Significant Damage: Fire is confirmed and presents a significant risk, though the full extent of the damage may not yet be clear. Phrases like Still, Still Box, or Working Fire may indicate a serious response, but the fire is not yet fully escalated.
        * Several Units and Possibly Specialized Teams: Multiple fire units respond, and in some cases, specialized teams are involved. The terminology might include Box Alarm or Mutual Aid, showing an increased but not yet overwhelming response.
        * Medium to High-Value Property: The fire involves medium-risk properties like large residential buildings or small commercial spaces. There is potential for escalation but with a manageable risk at this stage.
        * Partial Firefighting Efforts: There may be references to firefighting activities, such as hose deployment or lines being laid out, but the full details of the fire response may be unclear at the time. Characteristics: Can involve multi-story homes or small to medium commercial properties. Risk of fire spreading is moderate, and the response is robust but not overwhelming. Fire requires multiple units, including specialized equipment (e.g., ladder trucks, engines). The fire is not yet fully out of control but has the potential for significant property damage. 
        Contextual Rule: Use this rating when the fire is active, multiple units are involved, and terms like Still Box or Working Fire indicate significant fire activity. However, there may still be uncertainty about the full scale of the event or the extent of damage.
        Gas leaks should not be included expect in cases where fire is present or explicitly mentions in the dispatch as the primary cause.  
        Multiple battalions and over 5+ fire units are called out simultaneously, signaling a need for overwhelming resources.


    Rating 3: Moderate Fire Incident
        * Controlled Fire with Limited Spread: The fire is confirmed but is under control quickly, with localized damage and no further escalation. Phrases like Fire Knocked Down or Fire Under Control are common for this category.
        * Standard Response Units Deployed: Standard firefighting units respond to the scene. This is typical for residential fires or small commercial properties. Phrases like One Line On or Minor Fire may indicate a smaller-scale response.
        * Low-Risk Property or Residential Areas: The fire is in a residential home, garage, or other small-scale property, with minimal risk of spreading or causing extensive damage.
        * Fire Resolved: The fire is resolved without needing extensive resources or further escalation. Characteristics: Damage is localized to a small section of a property. Residential property involvement, such as a detached garage, shed, or a home’s kitchen. Response involves fewer units, typically standard firefighting teams. The risk of escalation is low, but immediate attention is required to control the fire.
        Contextual Rule: This rating applies when a fire is manageable, resolved without major resource deployment, and localized in damage. The key is that fire presence is confirmed, but the overall impact is limited.
        Gas leaks should not be included expect in cases where fire is present or explicitly mentions in the dispatch.
        Multiple battalions and over 4+ fire units are called out simultaneously, signaling a need for overwhelming resources.


    Rating 2: Minor Fire Incident
        * Small Fire or Smoke Detection: A minor fire or smoke condition is detected, but the situation is quickly contained with minimal or no damage to the property.
        * Limited Fire Response: Only a few units (e.g., one or two fire trucks) are dispatched. The fire may have been extinguished quickly, or the smoke may have dissipated before the fire spread.
        * Low-Risk Property: The fire occurs in low-risk areas like small residential properties, garages, or minor outdoor locations, with no major structural damage reported.
        * False Alarm Potential: There is a chance the fire incident was misinterpreted or that the fire was minimal enough to pose little threat. The fire is quickly contained with little effort.
        * Characteristics:  Fire is isolated to a vehicle (e.g., cars, trucks, or even motorcycles). Typically occurs in parking lots, roadsides, or garages but does not threaten structures. Minimal resources required, usually handled by a single truck or small unit. May require traffic control if the fire is in a roadway, but the risk of spreading is minimal.
        Gas leaks should not be included expect in cases where fire is present or explicitly mentions in the dispatch.
        Contextual Rule: Fires rated 2 stars may include small, contained incidents where damage is minimal, or there is a possibility the alarm was raised unnecessarily but without confirmation of a total false alarm.

    Rating 1: Units Dispatched to Potential Fire
        * Dispatched for Possible Fire: Units are dispatched in response to a potential fire, but fire presence is not yet confirmed. The initial reports or alarms suggest a fire, but no visible flames or smoke have been observed at the time of dispatch.
        * Unclear Severity: The severity and presence of the fire are unknown. This rating applies when fire units are still in transit or just arriving on the scene, with no detailed fire information available.
        * No Active Suppression Yet: There is no mention of hoses or firefighting equipment being deployed, and the focus is still on investigating whether or not there is an actual fire.
        * Characteristics: Units are dispatched based on fire alarm systems, not confirmed fires. The incident may involve multi-unit residential or commercial buildings where evacuation or fire investigation is necessary. There is no confirmed fire activity, though units are preparing for a potential fire situation. Could escalate to a higher rating if the presence of fire is confirmed.
        * 
        Contextual  Rule: This rating is used for dispatches based on potential fire reports. If there is no evidence of an actual fire or details are too limited, it remains a 1-star rating until further confirmation.

    Rating 0: No Fire or False Alarm
        * If the transcript is empty it's No Fire (do not rate a 4 or 5)
        * No Fire Detected: Upon arrival, there is no fire present at the scene. The situation is either a false alarm or a non-fire incident.
        * False Alarm Confirmed: It is determined that the alarm was mistakenly triggered (e.g., malfunctioning smoke detectors or accidental reports).
        * Minimal or No Resources Deployed: The incident is resolved with very few or no resources being used. Fire units may have returned to their station after determining that no action is needed.
        * No Damage: There is no structural damage or impact from the incident, confirming that the event was a non-issue.
        *Gas Leaks with response, but no fire showing
        * Characteristics: Incident resolved without any firefighting efforts. Typically involves an error in fire alarm systems or misreported incidents. Units may be sent back before taking any action if the alarm is confirmed false. No damage or fire threat is present.
        Contextual Rule: This rating should be applied only when it is confirmed that there is no fire at the scene, and the event has been cleared without any further risk or damage.
        If it is a Service Call vs. Actual Fire: If the first dispatch involves a service call rather than a true fire. The resident simply needs assistance resetting an alarm triggered by a cooking fire or for any other reason the dispatch poses no ongoing threat.
        No Active Fire: In the second part of the call, Speaker F reports that no fire or hazardous situation was found. The source of concern (burning leaves) is minor and not an emergency.
        Example of 0 Fire Rating: 
        [00:03:19.000] Speaker E: 113, a service call, 12526 Fairview Avenue, 12526 Fairview Avenue, apartment C-104 for the service call. Resident stated that the alarm went off due to cooking fire in the apartment and doesn't know how to reset his alarm.
        [00:04:00.000] Speaker F: Oil points 633. We're all good here at location nothing found. It looks like someone burning leaves across the street on the north side of 115th Chicago sign probably falling over here. We're going to be cleared up.

        No Response Needed: Both instances show that no active firefighting or emergency services were required to address the situation.
        If the words "Fire Ground Out", "All Unit Return", or other such context where the fire is called off.  Rate 0.


7. 10-Codes and Other Dispatch Codes:
    * Identify and convert dispatch codes into their natural language equivalents for clarity. Use the provided 10-Codes, 11-Codes, and Common Fire and Medical Codes tables for accurate conversion.

8. Additional Instructions:
    * Suggest and implement additional sub-categories if they enhance the clarity and specificity of the categorization.
    * Ensure no sub-category is duplicated unless necessary.
    * Focus on capturing as much relevant data as possible without repeating information unnecessarily.

Format Output: Structure your output in the following JSON format, ensuring each notification/report is complete:

""" + """
    {
        "alerts": [
            {
                "category": "<Main Category>", // e.g., Fire Alerts, Police Dispatch, Medical Emergencies, Miscellaneous
                "sub-category": "<Sub-Category>", // Create or use existing sub-categories
                "headline": "<Title of the event occurred>", // For false alarms, include 'false' in the headline
                "description": "<Segment of Transcription>", // Provide relevant transcription details (e.g., 20+ words)
                "incident_Address": "<Address of event occurred>", // Provide the standardized address, including state, city, and zip code
                "rating": <The Rating Number 1-5>, // Fire severity rating based on Fire Incident Severity Rating system - type of integer
                "rating_title": "<The Type of Severity>", // E.g., "Rating 5: Major Fire Incident"
                "rating_criteria": "<Fire description based on Fire Incident Severity Rating Criteria>", // Explain why this rating was selected
                "10-codes": "<codes used in the transcript, comma-separated>", // Include relevant scanner codes from the transcript
                "response_origin_address": <Origin Address of Response>, //Provide Address of responding fire department
                "response_origin_radius": <Radius of Response> //Provide radius for google address search of responding fire department
            }
        ]
    }


""" + f"""
Note for Incident Addresses: When you extract Incident_Address, please reference the following:

State Name: {state}
County Name: {county}
Scanner Title: {scanner_title}

Extract and clearly state the formatted street address of the event from the provided text.
From above Scanner Title, you can also get important information about city or county name.

Don't guess the address but based on above given State, County, City names and the info mentioned in inputted transcript.

Cross reference the below Division and district information based on vehicle code names to determine the general city. For instance Truck 1 is in Akron from heights which has a radius of 14.4 radius jurisdiction.  Make sure the address you provide is within the jurisdiction limitation of 14.4 miles.  If you can’t find one refer “address: NA”. (Listing is coming soon but I don’t have it right now)

Make sure the address is as standardized and structured as possible, ideally including street number, street name, city, county, state, and ZIP code. 
Don't forget to contain county name and state name.
"""

    return prompt