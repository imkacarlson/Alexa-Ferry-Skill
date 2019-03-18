import json
import datetime

def next_departure_times(num_future_departures_wanted = 3, departure_terminal = "bainbridge", arrival_terminal = 'seattle'):
    with open('bainbridge_departures_2013.json') as f:
        departure_times = json.loads(json.load(f))[departure_terminal]
    
    # holidays = []
    
    d = datetime.datetime.today()

    # Today is a weekday
    if((d.weekday() >= 0) and (d.weekday() <= 4)):
        #departures = [x for x in departure_times["weekday"] if (int(x.split(":")[0]) >= d.hour and int(x.split(":")[1]) > d.minute)]
        departures = [x for x in departure_times["weekday"] if int(x.split(":")[0]) >= d.hour]
    # Today is a Saturday
    elif(d.weekday() == 5):
        departures = [x for x in departure_times["holiday_saturday"] if int(x.split(":")[0]) >= d.hour]
    # Today is a Sunday
    elif(d.weekday() == 6):
        departures = [x for x in departure_times["sunday"] if int(x.split(":")[0]) >= d.hour]


    if(len(departures) < 3):
        # Tomorrow is a Saturday
        if((d.weekday()) + 1 == 5):
            return(departures + list(departure_times["holiday_saturday"][0:(num_future_departures_wanted - len(departures))]))
        #Tomorrow is a Sunday
        elif(d.weekday() + 1 == 6):
            return (departures + list(departure_times["sunday"][0:(num_future_departures_wanted - len(departures))]))
        # Tomorrow is a Monday
        elif(d.weekday() + 1 == 7):
            return (departures + list(departure_times["weekday"][0:(num_future_departures_wanted - len(departures))]))

    return departures[0:num_future_departures_wanted]
