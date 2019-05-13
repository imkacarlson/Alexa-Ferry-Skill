import datetime
import urllib.request
import json
import datetime
import time
import re
import boto3
from statistics import mean

def lambda_handler(event, context):
    # TODO implement
    return {
        'speech_output': ferry_state()
    }

def extract_milliseconds(s):
    """Extract milliseconds from date fromatted as such: "/Date(1555098124167-0700)/".

    Keyword arguments:
    s -- The /Date object as a string
    """
    
    regex = "\/Date\(([^)]+)\)"
    
    return re.findall(regex, s)[0].split("-")[0]

def milliseconds_to_time(ms):
    """Convert Unix epoch time to python datetime object.
    
    Note: Automatically subtracts 7 hours because the ferry system is on PST.
    Need to be careful about how this changes with daylight savings time.

    Keyword arguments:
    ms  -- Unix epoch time
    """
    
    return datetime.datetime.utcfromtimestamp(int(ms)/1000) - datetime.timedelta(hours = 7)

def ferry_state():
    """Uses the WSF Vessels API to get information about the ferry in relation to the Bainbridge ferry terminal."""

    bucket_name = "#####"
    api_access_code = "#####"
    request_url = "http://www.wsdot.wa.gov/Ferries/API/Vessels/rest/vessellocations?apiaccesscode={}".format(api_access_code)

    response_text = urllib.request.urlopen(request_url).read().decode("utf-8")
    response_json = json.loads(response_text)
    
    output = ""
    
    bainbridge_data = {}
    for i in range(len(response_json)):
        if (response_json[i]['DepartingTerminalAbbrev'] == "BBI"):
            bainbridge_data = response_json[i]
            break
            
    if bainbridge_data:        
        if bainbridge_data['AtDock']:
            if bainbridge_data['ScheduledDeparture']:
                output = "The " + bainbridge_data["VesselName"] + " is currently at the Bainbridge dock. It is scheduled to depart at " + milliseconds_to_time(extract_milliseconds(bainbridge_data["ScheduledDeparture"])).strftime("%I:%M %p") + "."
    else:
        arriving_bainbridge_data = {}
        for i in range(len(response_json)):
            if (response_json[i]['ArrivingTerminalAbbrev'] == "BBI"):
                arriving_bainbridge_data = response_json[i]
                break
        if arriving_bainbridge_data:
            if arriving_bainbridge_data["Eta"]:
                output = "There is currently no boat at the Bainbridge dock. The " + arriving_bainbridge_data["VesselName"] + " is scheduled to arrive at " + milliseconds_to_time(extract_milliseconds(arriving_bainbridge_data["Eta"])).strftime("%I:%M %p") +"."
        
    s3_client = boto3.client('s3')
    
    s3_bainbridge_live_json = s3_client.get_object(Bucket=bucket_name, Key="bainbridge_live_data.json")
    object_content = s3_bainbridge_live_json['Body'].read().decode('utf-8')
    departure_times = json.loads(object_content)
    
    last_four_minutes_late_average = int(mean(departure_times["seconds_late"][-4:])/60)
    
    if abs(last_four_minutes_late_average) >= 1:
        output = output + " The last four departures from Bainbridge have averaged " + str(last_four_minutes_late_average) + " minutes " + ("early." if last_four_minutes_late_average < 0 else "late.")
        
    return output