import json
import datetime
import boto3

def lambda_handler(event, context):
    num_departures = event["departures"]
    return {'departures': next_departure_times(num_departures)}


def next_departure_times(num_future_departures_wanted = 3, departure_terminal = "bainbridge", arrival_terminal = 'seattle', d = datetime.datetime.now() - datetime.timedelta(hours = 7)):

    bucket_name = "#####"

    s3_client = boto3.client('s3')
    s3_response_object = s3_client.get_object(Bucket=bucket_name, Key="bainbridge_ferry_departure_schedule.json")
    object_content = s3_response_object['Body'].read().decode('utf-8')
    departure_times = json.loads(object_content)

    departure_times = json.loads(departure_times)[departure_terminal]

    weekday_departures = departure_times["weekday"]
    saturday_departures = departure_times["holiday_saturday"]
    sunday_departures = departure_times["sunday"]

    return generate_list(num_future_departures_wanted, departure_terminal, arrival_terminal, d, weekday_departures, saturday_departures, sunday_departures)

def strings_to_datetime(strings, d):
    dates = []
    for date_string in strings:
        date = datetime.datetime.strptime(date_string, "%H:%M:%S").replace(year = d.year, month = d.month, day = d.day)
        dates.append(date)
        
    return dates

def first_future_instance(departures, d):
    #d = datetime.datetime.now() - datetime.timedelta(hours = 7)
    #d = datetime.datetime(2019, 9, 22, 00, 1)
    i = 0
    print(d)
    prev_hour = 0
    for time in departures:
        if not prev_hour <= int(time.split(":")[0]):
            d = d + datetime.timedelta(days = 1). replace(hours = 0, minutes = 0)
            break
        else:
            if(not datetime.datetime.strptime(time, "%H:%M:%S").replace(year = d.year, month = d.month, day = d.day) >= d):
                i = i + 1
                prev_hour = int(time.split(":")[0])
            else:
                break

    print(i)
    return i
    

def generate_list(num_future_departures_wanted, departure_terminal, arrival_terminal, d, weekday_departures, 
saturday_departures, sunday_departures):
    # holidays = []
    departures = []
    
    # For the case when the user askes for a departure between midnight and 3 am, need to go back to the previous day.
    if d.hour <=3 and d.hour >= 0:
        # Today is a Sunday
        if(d.weekday() == 6):
            departures = [x for x in saturday_departures[-2:] if datetime.datetime.strptime(x, "%H:%M:%S").replace(year = d.year, month = d.month, day = d.day) >= d]
            return departures[:num_future_departures_wanted]
        #Today is  Monday
        if(d.weekday() == 0):
            departures = [x for x in sunday_departures[-2:] if datetime.datetime.strptime(x, "%H:%M:%S").replace(year = d.year, month = d.month, day = d.day) >= d]
            return departures[:num_future_departures_wanted]            
        # Today is a Tuesday - Friday
        elif((d.weekday() >= 1) and (d.weekday() <= 4)):
            departures = [x for x in weekday_departures[-2:] if datetime.datetime.strptime(x, "%H:%M:%S").replace(year = d.year, month = d.month, day = d.day) >= d]
            return departures[:num_future_departures_wanted]
    
    # Today is a weekday
    if((d.weekday() >= 0) and (d.weekday() <= 4)):
        i = first_future_instance(weekday_departures, d)
        departures = weekday_departures[i:][:num_future_departures_wanted]
    # Today is a Saturday
    elif(d.weekday() == 5):
        i = first_future_instance(saturday_departures, d)
        departures = saturday_departures[i:][:num_future_departures_wanted]
    # Today is a Sunday
    elif(d.weekday() == 6):
        i = first_future_instance(sunday_departures, d)
        departures = sunday_departures[i:][:num_future_departures_wanted]

    while(len(departures) < num_future_departures_wanted):
        d = (d + datetime.timedelta(days = 1)).replace(hour = 0, minute = 0)

        departures = departures + generate_list(num_future_departures_wanted - len(departures), departure_terminal, arrival_terminal, d, weekday_departures, saturday_departures, sunday_departures)
    return departures
