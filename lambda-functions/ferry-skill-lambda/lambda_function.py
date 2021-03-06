"""
This is a Python template for Alexa to get you building skills (conversations) quickly.

Original template code taken from: https://github.com/KeithGalli/Alexa-Python
    Be sure to checkout his tutorial: https://www.youtube.com/watch?v=sj7NqS7yytw
"""

from __future__ import print_function
import datetime

import re
import boto3
import json

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }

def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------
def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to your personal ferry tracker!"
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Try asking me to make a prediction about the next ferry to Seattle."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_next_ferry_response(intent):
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    session_attributes = {}
    card_title = "Next Ferry"
    
    arrival_city = intent['slots']['arrival_city']['value']

    lambda_client = boto3.client('lambda')

    speech_output = ""
    if "value" in intent['slots']['num_departures'].keys():
        num_departures = intent['slots']['num_departures']["value"]
        params = {'departures':int(num_departures)}
        lambda_response = lambda_client.invoke(FunctionName = "next-departure", InvocationType = "RequestResponse", Payload = json.dumps(params))
        departure_times = json.loads(lambda_response['Payload'].read().decode('utf-8'))["departures"]
        
        departures_speech = ""
        for departure in departure_times:
            departure = datetime.datetime.strptime(departure, "%H:%M:%S")
            departures_speech = departures_speech + departure.strftime("%I:%M %p") + ", "

        speech_output = ("The next " + str(num_departures) + " ferries to Seattle are at " + departures_speech[:-11] + " and" + departures_speech[-11:])[:-2] + "."
    else:
        params = {'departures': 1}
        lambda_response = lambda_client.invoke(FunctionName = "next-departure", InvocationType = "RequestResponse", Payload = json.dumps(params))
        departure_times = json.loads(lambda_response['Payload'].read().decode('utf-8'))["departures"]
        departure = datetime.datetime.strptime(departure_times[0], "%H:%M:%S")
        speech_output = "The next ferry to " + arrival_city + " is at " + departure.strftime("%I:%M %p")

    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Ask me when the next ferry to Seattle is."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))       

def get_track_ferry_response(intent):
    """Returns a object with information about the next number of predictions asked for by the user.

    Keyword arguments:
    intent  -- the intent JSON object
    """
    d = datetime.datetime.now()
    session_attributes = {}
    card_title = "Next Ferry"
    
    arrival_city = intent['slots']['arrival_city']['value']

    lambda_client = boto3.client('lambda')

    speech_output = ""
    
    # Reused code 
    if "value" in intent['slots']['num_departures'].keys():
        num_departures = intent['slots']['num_departures']["value"]
        params = {'departures':int(num_departures)}
        lambda_response = lambda_client.invoke(FunctionName = "next-departure", InvocationType = "RequestResponse", Payload = json.dumps(params))
        departure_times = json.loads(lambda_response['Payload'].read().decode('utf-8'))["departures"]

        params = {'departures':departure_times}
        lambda_response = lambda_client.invoke(FunctionName = "make-predictions", InvocationType = "RequestResponse", Payload = json.dumps(params))
        predictions = json.loads(lambda_response['Payload'].read().decode('utf-8'))

        predictions_speech = ""
        for i in range(len(predictions["predictions"])):
            departure_time = datetime.datetime.strptime(predictions["departures"][i], "%H:%M:%S").replace(year = d.year, month = d.month, day = d.day)
            predictied_time = int(predictions["predictions"][i])

            if abs(predictied_time < 60):
                predictions_speech = predictions_speech + "The " + departure_time.strftime("%I:%M %p") + " departure is predicted to depart on time. "
            else:
                minutes_late = int(abs(predictied_time / 60))
                if predictied_time < 0:
                    predictions_speech = predictions_speech + "The " + departure_time.strftime("%I:%M %p") + " departure is predicted to be " + str(minutes_late) + (" minutes" if minutes_late > 1 else " minute") + " early. "
                else:
                    predictions_speech = predictions_speech + "The " + departure_time.strftime("%I:%M %p") + " departure is predicted to be " + str(minutes_late) + (" minutes" if minutes_late > 1 else " minute") + " late. "
        speech_output = predictions_speech[:-1]
    else:
        params = {'departures':1}
        lambda_response = lambda_client.invoke(FunctionName = "next-departure", InvocationType = "RequestResponse", Payload = json.dumps(params))
        departure_times = json.loads(lambda_response['Payload'].read().decode('utf-8'))["departures"]
        departure = datetime.datetime.strptime(departure_times[0], "%H:%M:%S").replace(year = d.year, month = d.month, day = d.day)

        params = {'departures':departure_times}
        lambda_response = lambda_client.invoke(FunctionName = "make-predictions", InvocationType = "RequestResponse", Payload = json.dumps(params))
        predictions = json.loads(lambda_response['Payload'].read().decode('utf-8'))
        predicted_time = int(predictions['predictions'][0])
        minutes_late = int(abs(predicted_time / 60))

        if abs(predicted_time) < 60:
            speech_output = "The " + departure.strftime("%I:%M %p") + " departure to " + arrival_city + " is predicted to be on time."
        else:
            if predictions['predictions'][0] < 0:
                speech_output = "The " + departure.strftime("%I:%M %p") + " departure to " + arrival_city + " is predicted to be " + str(minutes_late) + (" minutes" if minutes_late > 1 else " minute") + " early."
            else:
                speech_output = "The " + departure.strftime("%I:%M %p") + " departure to " + arrival_city + " is predicted to be " + str(minutes_late) + (" minutes" if minutes_late > 1 else " minute") + " late."

    reprompt_text = "Ask me to make a prediction about the next ferry to Seattle"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))    

def get_four_hour_trend_response():
    """Returns a object with the average of the seconds late (or early) predictions over the next four hours."""

    session_attributes = {}
    card_title = "Four Hour Trend"

    lambda_client = boto3.client('lambda')
    params = {}
    lambda_response = lambda_client.invoke(FunctionName = "make-predictions", InvocationType = "RequestResponse", Payload = json.dumps(params))
    four_hour_average = int(json.loads(lambda_response['Payload'].read().decode('utf-8'))["next_four_hours"])

    speech_output = ""

    if abs(four_hour_average) < 60:
        speech_output = "Over the next four hours, departures to Seattle are predicted to be on time."
    else:
        minutes_late = int(abs(four_hour_average / 60))
        if four_hour_average < 0:
            speech_output = "Over the next four hours, departures to Seattle are predicted to be " + str(minutes_late) + (" minutes" if minutes_late > 1 else " minute") + " early."
        else:
            speech_output = "Over the next four hours, departures to Seattle are predicted to be " + str(minutes_late) + (" minutes" if minutes_late > 1 else " minute") + " late."

    reprompt_text = "Ask me what the future trend of departures to Seattle is."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))   

def get_bainbridge_terminal_status_response():
    """Returns a object with information about where boats are in relation to the Bainbridge terminal."""
    session_attributes = {}
    card_title = "Bainbridge Terminal Status"

    lambda_client = boto3.client('lambda')
    params = {}
    lambda_response = lambda_client.invoke(FunctionName = "current-state-ferries", InvocationType = "RequestResponse", Payload = json.dumps(params))
    speech_output = json.loads(lambda_response['Payload'].read().decode('utf-8'))["speech_output"]
    
    reprompt_text = "Ask me for a Bainbridge terminal status update."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session)) 


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Have a nice trip!"
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts.
        One possible use of this function is to initialize specific 
        variables from a previous state stored in an external database
    """
    # Add additional code here as needed
    pass

    

def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """
    # Dispatch to your skill's launch message
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "Next_Ferry":
        return get_next_ferry_response(intent)
    elif intent_name == "Track_Ferry":
        return get_track_ferry_response(intent)
    elif intent_name == "Four_Hour_Trend":
        return get_four_hour_trend_response()
    elif intent_name == "Bainbridge_Terminal_Status":
        return get_bainbridge_terminal_status_response()
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.
    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------


def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("Incoming request...")

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
