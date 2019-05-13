import json
import boto3
import json
import datetime
from statistics import mean

bucket_name = "#####"
bainbridge_predictions_file_name = "bainbridge_ferry_predictions.json"

def lambda_handler(event, context):
    if "departures" in event.keys():
        departures = event["departures"]
        return {
            'departures' : departures,
            'predictions': get_predictions(departures)
        }
    else:
        return {
            'next_four_hours': next_four_hours()
        }

def getPrediction(starting_date, target):
    """Invokes the prediction model to get predictions starting at some date with specificed target data.

    Keyword arguments:
    starting_date -string representing the starting date
    """
    endpoint_name = "bainbridge-ferry-predictor"

    client = boto3.client('sagemaker-runtime')

    prediction_data = '{"instances": [ {"start": "%s", "target": %s}],"configuration": {"output_types": ["mean"], "num_samples": 100}}' % (starting_date, target)

    response = client.invoke_endpoint(
        EndpointName=endpoint_name,
        Body=prediction_data,
        ContentType='application/json'
    )

    return response

def make_prediction_write_to_s3(starting_date):
    """Makes predictions starting at some date and saves it a file in S3.

    Keyword arguments:
    starting_date  -- string representation of the starting date
    """
    # Getting target values
    s3_client = boto3.client('s3')
    s3_response_object = s3_client.get_object(Bucket=bucket_name, Key="bainbridge_live_interpolated_data.json")
    object_content = s3_response_object['Body'].read().decode('utf-8')
    departure_times = json.loads(object_content)
    
    seconds_late_list = departure_times["seconds_late"]

    # Invoking the model
    prediction = getPrediction(starting_date, seconds_late_list)
    prediction_json = json.loads(prediction["Body"].read().decode('utf-8'))
    predictions_list = prediction_json['predictions'][0]['mean']

    # Saving the data to S3
    predictions_dict = {}

    predictions_dict["start_date"] = starting_date
    predictions_dict["predictions"] = predictions_list
    
    predictions_json = json.dumps(predictions_dict).encode("utf-8")

    s3 = boto3.resource("s3")
    s3.Bucket(bucket_name).put_object(Key="bainbridge_predictions/"+bainbridge_predictions_file_name, Body=predictions_json)
    
def get_predictions(scheduled_departures, today = datetime.datetime.now() - datetime.timedelta(hours = 7)):
    """Makes predictions for each of the departure in the scheduled departures list.

    Keyword arguments:
    starting_date  -- string representation of the starting date
    today -- the current time (subtracting 7 because the Amazon servers are on Greenwich Mean Time and pacific time with daylight savings is 7 hours less than GMT.)
    """
    
    s3_client = boto3.client('s3')
    s3_response_object = s3_client.get_object(Bucket=bucket_name, Key="bainbridge_predictions/"+bainbridge_predictions_file_name)
    object_content = s3_response_object['Body'].read().decode('utf-8')
    predictions_json = json.loads(object_content)
    
    starting_date = datetime.datetime.strptime(predictions_json["start_date"], '%Y-%m-%d %H:%M:%S')
    ending_date = starting_date + datetime.timedelta(minutes = (5*288))
    
    at_date = starting_date
    
    predictions = predictions_json["predictions"]
    
    predictions_to_return = []
    
    for i in range(len(scheduled_departures)):
        scheduled_departure = datetime.datetime.strptime(scheduled_departures[i], '%H:%M:%S').replace(year = today.year, month = today.month, day = today.day)
        if today.hour > scheduled_departure.hour:
            scheduled_departure = scheduled_departure + datetime.timedelta(days = 1)
            today = scheduled_departure
        if (scheduled_departure < starting_date or scheduled_departure > ending_date):
            make_prediction_write_to_s3(scheduled_departure.replace(hour = 0, minute = 0, second = 0).strftime('%Y-%m-%d %H:%M:%S'))
            return predictions_to_return + get_predictions(scheduled_departures[i:], today)          
        
        # Number of 5 minute intervals are in between the two dates
        index = int((scheduled_departure - starting_date).seconds / (5*60))
        
        at_date = starting_date + datetime.timedelta(minutes = (5 * index))
        
        if(at_date > ending_date):
            make_prediction_write_to_s3(at_date.replace(hour = 0, minute = 0, second = 0).strftime('%Y-%m-%d %H:%M:%S'))
            return predictions_to_return + get_predictions(scheduled_departures[i:], today)  
        else:
            if index < len(predictions):
                predictions_to_return.append(predictions[index])
            else:
                print("here")
                return
            
    return predictions_to_return

def next_four_hours():
    """Averages out the seconds late predictions over the next four hours."""
    # 5 minute intervals in 4 hours
    four_hours = (60/5) * 4
    
    today = datetime.datetime.now()
    
    s3_client = boto3.client('s3')
    s3_response_object = s3_client.get_object(Bucket=bucket_name, Key="bainbridge_predictions/"+bainbridge_predictions_file_name)
    object_content = s3_response_object['Body'].read().decode('utf-8')
    predictions_json = json.loads(object_content)
    predictions = predictions_json["predictions"]
    
    starting_date = datetime.datetime.strptime(predictions_json["start_date"], '%Y-%m-%d %H:%M:%S')
    
    if starting_date.day > today.day:
        make_prediction_write_to_s3((starting_date - datetime.timedelta(days = 1)).strftime('%Y-%m-%d %H:%M:%S'))
        return next_four_hours()
    elif starting_date.day < today.day:
        make_prediction_write_to_s3((starting_date + datetime.timedelta(days = 1)).strftime('%Y-%m-%d %H:%M:%S'))
        return next_four_hours()
    
    # Number of 5 minute intervals we are into the day
    index = int((today - starting_date).seconds / (5*60))
    
    return mean(predictions[index:(index + int(four_hours))])