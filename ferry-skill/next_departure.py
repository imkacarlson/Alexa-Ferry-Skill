import pandas as pd
import datetime

def next_departure_times(num_future_departures_wanted = 3):
    
    df = pd.read_csv("Bainbridge_Departure_Times_2013.csv", dtype=object)
    # holidays = []
    
    d = datetime.datetime.today()

    # Today is a weekday
    if((d.weekday() >= 1) and (d.weekday() <= 5)):
        departures = [x for x in df["weekday"].dropna() if (int(x.split(":")[0]) >= d.hour and int(x.split(":")[1]) > d.minute)][0:num_future_departures_wanted]
    # Today is a Saturday
    elif(d.weekday() == 6):
        departures = [x for x in df["holiday_saturday"].dropna() if (int(x.split(":")[0]) >= d.hour and int(x.split(":")[1]) > d.minute)][0:num_future_departures_wanted]
    # Today is a Sunday
    elif(d.weekday() == 7):
        departures = [x for x in df["sunday"].dropna() if (int(x.split(":")[0]) >= d.hour and int(x.split(":")[1]) > d.minute)][0:num_future_departures_wanted]


    if(len(departures) < 3):
        # Tomorrow is a Saturday
        if((d.weekday()) + 1 == 5):
            return(departures + list(df["holiday_saturday"].dropna()[0:(num_future_departures_wanted - len(departures))]))
        #Tomorrow is a Sunday
        elif(d.weekday() + 1 == 6):
            return (departures + list(df["sunday"].dropna()[0:(num_future_departures_wanted - len(departures))]))
        # Tomorrow is a Monday
        elif(d.weekday() + 1 == 7):
            return (departures + list(df["weekday"].dropna()[0:(num_future_departures_wanted - len(departures))]))

    return departures[0:num_future_departures_wanted]
            