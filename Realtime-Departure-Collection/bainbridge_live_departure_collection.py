import urllib.request
import json
import datetime
import re
import datetime
import time
import boto3
import numpy as np
import pandas as pd

def write_to_file(scheduled_departure, actual_departure):
    """Writes new departure to S3.

    Keyword arguments:
    scheduled_departure -- a datetime object that represents the scheduled departure
    actual_departure -- a datetime object that represents the actual departure
    """
    seconds_late = actual_departure - scheduled_departure
    
    # The boat was early
    if (scheduled_departure > actual_departure):
        seconds_late = (scheduled_departure - actual_departure).seconds * -1
    else:
        seconds_late = actual_departure - scheduled_departure
        
    
    s3_client = boto3.client('s3')

    # Since I am using a model trained on interpolated data I need to pass it interpolated data.
    # Doing the interpolation here so it does not need to be done when the model is invoked.
    s3_bainbridge_live_interpolated_json = s3_client.get_object(Bucket=bucket_name, Key="bainbridge_live_interpolated_data.json")
    object_content = s3_bainbridge_live_interpolated_json['Body'].read().decode('utf-8')
    interpolated_departure_times = json.loads(object_content)

    # This is where the un-interpolated data is stored.
    s3_bainbridge_live_json = s3_client.get_object(Bucket=bucket_name, Key="bainbridge_live_data.json")
    object_content = s3_bainbridge_live_json['Body'].read().decode('utf-8')
    departure_times = json.loads(object_content)
    
    seconds_late_interpolated_list = interpolated_departure_times["seconds_late"]
    seconds_late_list = departure_times["seconds_late"]

    last_departure = datetime.datetime.strptime(interpolated_departure_times["last_departure"], "%H:%M:%S").replace(year = d.year, month = d.month, day = d.day)

    if not datetime.datetime.now().hour >= last_departure.hour:
        last_departure = last_departure - datetime.timedelta(days = 1)

    # Number of 5 minute intervals between the scheduled and actual departure
    intervals = int((scheduled_departure - last_departure).seconds / (5*60))

    # Setting up for interpolation
    nans = [np.nan] * (1 if intervals == 0 else intervals)

    nans[0] = seconds_late_interpolated_list[-1]
    nans[-1] = seconds_late.seconds

    nans = pd.Series(nans)

    interpolated = list(nans.interpolate(method = 'index'))

    seconds_late_interpolated_list = seconds_late_interpolated_list + interpolated
    seconds_late_list.append(seconds_late.seconds)
    
    interpolated_file = {}
    interpolated_file["seconds_late"]  = seconds_late_interpolated_list[-288:]
    interpolated_file["last_departure"] = scheduled_departure.strftime("%H:%M:%S")

    live_file = {}
    live_file["seconds_late"] = seconds_late_list[-288:]
    
    s3_client.put_object(Body = json.dumps(interpolated_file), Bucket = bucket_name, Key = "bainbridge_live_interpolated_data.json")
    s3_client.put_object(Body = json.dumps(live_file), Bucket = bucket_name, Key = "bainbridge_live_data.json")

    print("%s Appended %s to the seconds late list. Cooling down for 60 seconds." % (datetime.datetime.now(), seconds_late.seconds))
    time.sleep(60)
    
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

bucket_name = "#####"
api_access_code = "#####"
request_url = "http://www.wsdot.wa.gov/Ferries/API/Vessels/rest/vessellocations?apiaccesscode={}".format(api_access_code)

lambda_client = boto3.client('lambda')
params = {'departures': 1}

# Infinite loop with sleep statements that invokes the ferry endpoint at each scheduled 
# departure then waits for the actual departure time.
while(True):
    lambda_response = lambda_client.invoke(FunctionName = "next-departure", InvocationType = "RequestResponse", Payload = json.dumps(params))
    departure_time = json.loads(lambda_response['Payload'].read().decode('utf-8'))["departures"]
    d = datetime.datetime.now()
    
    # If statement checking for the case where it is like 10:45pm and our next departure is past midnight.
    # If this is the case then then it needs to be respresented as one day further.
    if(int(departure_time[0].split(":")[0]) < datetime.datetime.now().hour):
        next_departure = datetime.datetime.strptime(departure_time[0], "%H:%M:%S").replace(year = d.year, month = d.month, day = d.day)
        next_departure = next_departure + datetime.timedelta(days = 1)
    else:
        next_departure = datetime.datetime.strptime(departure_time[0], "%H:%M:%S").replace(year = d.year, month = d.month, day = d.day)
    while datetime.datetime.now() < next_departure:
        seconds_to_sleep = datetime.datetime.timestamp(next_departure) - datetime.datetime.timestamp(datetime.datetime.now())
        print("%s Waiting for the next scheduled departure at: %s. Going to sleep for %d (+60) seconds." % (datetime.datetime.now(), next_departure, seconds_to_sleep))
        time.sleep(seconds_to_sleep + 60)

    boatLeft = False

    while(not boatLeft):
        response_text = urllib.request.urlopen(request_url).read().decode("utf-8")
        response_json = json.loads(response_text)
        
        for i in range(len(response_json)):
            if (response_json[i]['DepartingTerminalAbbrev'] == "BBI"):
                bainbridge_data = response_json[i]
                break
                
        if(bainbridge_data['AtDock'] == True):
            print("{} The {} is still at the dock and was scheduled to leave at {}. Waiting for 2 minutes.".format(datetime.datetime.now(), bainbridge_data["VesselName"], next_departure))
            time.sleep(60*2)
        else:
            scheduled_departure = milliseconds_to_time(extract_milliseconds(bainbridge_data["ScheduledDeparture"]))
            if bainbridge_data["LeftDock"] is not None:
                actual_departure = milliseconds_to_time(extract_milliseconds(bainbridge_data["LeftDock"]))
                write_to_file(scheduled_departure, actual_departure)
                print("{} The {} has left the dock. It was scheduled to depart at {}, and actually departed at {}.".format(datetime.datetime.now(), bainbridge_data["VesselName"], scheduled_departure, actual_departure))
                boatLeft = True
            else:
                print("{} The {} is indicating it is no longer 'AtDock', but 'LeftDock' has not been populated. Waiting 1 minute for 'LeftDock'. It was scheduled to depart at {}.".format(datetime.datetime.now(), bainbridge_data["VesselName"], scheduled_departure))
                time.sleep(60)