import json
import datetime

def next_departure_times(num_future_departures_wanted = 3, departure_terminal = "bainbridge", arrival_terminal = 'seattle', d = datetime.datetime.today() - datetime.timedelta(hours = 7)):

    with open('ferry_departure_schedule.json') as f:
        departure_times = json.loads(json.load(f))[departure_terminal]

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
    i = 0
    for time in departures:
        if(not datetime.datetime.strptime(time, "%H:%M:%S").replace(year = d.year, month = d.month, day = d.day) > d):
            i = i + 1
        else:
            break

    return i
    

def generate_list(num_future_departures_wanted, departure_terminal, arrival_terminal, d, weekday_departures, 
saturday_departures, sunday_departures):
    # holidays = []
    departures = []
    
    # Today is a weekday
    if((d.weekday() >= 0) and (d.weekday() <= 4)):
        i = first_future_instance(weekday_departures, d)
        departures_strings = weekday_departures[i:][:num_future_departures_wanted]
    # Today is a Saturday
    elif(d.weekday() == 5):
        i = first_future_instance(saturday_departures, d)
        departures_strings = saturday_departures[i:][:num_future_departures_wanted]
    # Today is a Sunday
    elif(d.weekday() == 6):
        i = first_future_instance(sunday_departures, d)
        departures_strings = sunday_departures[i:][:num_future_departures_wanted]

    departures = strings_to_datetime(departures_strings, d)

    while(len(departures) < num_future_departures_wanted):
        d = (d + datetime.timedelta(days = 1)).replace(hour = 0, minute = 0)

        departures = departures + generate_list(num_future_departures_wanted - len(departures), departure_terminal, arrival_terminal, d, weekday_departures, saturday_departures, sunday_departures)
    return departures