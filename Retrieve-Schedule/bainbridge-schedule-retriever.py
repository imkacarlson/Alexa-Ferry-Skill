import urllib.request
import datetime
import json
import re

api_access_code         = "c44a23a4-aa03-4df4-b49c-e2939faf1d62"
bainbridge_terminal_id  = 3 # Bainbridge Island
seattle_terminal_id     = 7 # Seattle

weekday     = "2019-04-24"
saturday    = "2019-04-27"
sunday      = "2019-04-28"

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
    Need to be careful for how this changes with daylight savings time.

    Keyword arguments:
    ms  -- Unix epoch time
    """
    
    return datetime.datetime.utcfromtimestamp(int(ms)/1000) - datetime.timedelta(hours = 7)

def get_schedule(date, departing_terminal_id, arriving_terminal_id):
    request_url = "http://www.wsdot.wa.gov/Ferries/API/Schedule/rest/schedule/{}/{}/{}?apiaccesscode={}".format(
    date, departing_terminal_id, arriving_terminal_id, api_access_code)
    
    response_text = urllib.request.urlopen(request_url).read().decode("utf-8")
    
    response_text_json = json.loads(response_text)
    
    timestamps = []
    
    for departure in response_text_json["TerminalCombos"][0]["Times"]:
        time = extract_milliseconds(departure["DepartingTime"])
        timestamps.append(milliseconds_to_time(time))
    
    return timestamps

weekday_departures      = get_schedule(weekday, bainbridge_terminal_id, seattle_terminal_id)
saturday_departures     = get_schedule(saturday, bainbridge_terminal_id, seattle_terminal_id)
sunday_departures       = get_schedule(sunday, bainbridge_terminal_id, seattle_terminal_id)

weekday_next_day = sum([1 for time in weekday_departures if (time.day == int(weekday.split("-")[2]) + 1)])

#combined = weekday_departures + saturday_departures + sunday_departures

#complete_weekday_departures = sorted([time.strftime('%H:%M:%S') for time in combined if (time.day == int(weekday.split("-")[2]) or 
#time.day == int(weekday.split("-")[2]) + 1)])

print(weekday_next_day)

