import json
import boto3
import json
import datetime

bucket_name = "#####"
bainbridge_predictions_file_name = "bainbridge_ferry_predictions.json"

def lambda_handler(event, context):
    departures = event["departures"]
    return {
        'departures' : departures,
        'predictions': get_predictions(departures)
    }

def getPrediction(starting_date, target):
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
    s3_data_path = "{}/bainbridge_predictions".format(bucket_name)

    # Getting target values
    s3_client = boto3.client('s3')
    s3_response_object = s3_client.get_object(Bucket=bucket_name, Key="bainbridge_live_data.json")
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
    
def get_predictions(scheduled_departures):
    today = datetime.datetime.today()
    
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
        if (scheduled_departure < starting_date or scheduled_departure > ending_date):
            make_prediction_write_to_s3(scheduled_departure.replace(hour = 0, minute = 0, second = 0).strftime('%Y-%m-%d %H:%M:%S'))
            return predictions_to_return + get_predictions(scheduled_departures[i:])          
        
        # Number of 5 minute intervals are in between the two dates
        index = int((scheduled_departure - starting_date).seconds / (5*60))
        
        at_date = at_date + datetime.timedelta(minutes = (5 * index))
        
        if(at_date > ending_date):
            make_prediction_write_to_s3(at_date.replace(hour = 0, minute = 0, second = 0).strftime('%Y-%m-%d %H:%M:%S'))
            return predictions_to_return + get_predictions(scheduled_departures[i:])  
        else:
            if index < len(predictions):
                predictions_to_return.append(predictions[index])
            else:
                print("here")
                return
            
    return predictions_to_return