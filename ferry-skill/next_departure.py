import pandas as pd
import datetime

def next_departure_times(num_future_departures_wanted = 3):
    
    df = pd.read_csv("Bainbridge_Departure_Times_2013.csv", dtype=object)
    # holidays = []
    
    d = datetime.datetime.today()
    weekday_departures = [x for x in df["weekday"].dropna() if (int(x.split(":")[0]) >= d.hour and int(x.split(":")[1]) > d.minute)][0:num_future_departures_wanted]
    if(len(weekday_departures) < 3):
        # Tomorrow is a Saturday
        if((d.weekday()) + 1 == 5):
            return(weekday_departures + list(df["holiday_saturday"].dropna()[0:(num_future_departures_wanted - len(weekday_departures))]))
        #Tomorrow is a Sunday
        elif(d.weekday() + 1 == 6):
            return (weekday_departures + list(df["sunday"].dropna()[0:(num_future_departures_wanted - len(weekday_departures))]))
        # Tomorrow is a Monday
        elif(d.weekday() + 1 == 7):
            return (weekday_departures + list(df["weekday"].dropna()[0:(num_future_departures_wanted - len(weekday_departures))]))

    return weekday_departures[0:num_future_departures_wanted]
            