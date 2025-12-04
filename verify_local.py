import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def create_request(request_type, intent_name=None, slots=None, session_attributes=None):
    req = {
        "version": "1.0",
        "session": {
            "new": session_attributes is None,
            "sessionId": "amzn1.echo-api.session.1234",
            "application": {"applicationId": "amzn1.ask.skill.1234"},
            "user": {"userId": "amzn1.ask.account.TEST_USER"},
            "attributes": session_attributes or {}
        },
        "request": {
            "type": request_type,
            "requestId": "amzn1.echo-api.request.1234",
            "timestamp": "2023-10-27T00:00:00Z",
            "locale": "it-IT"
        }
    }
    if intent_name:
        req["request"]["intent"] = {
            "name": intent_name,
            "confirmationStatus": "NONE"
        }
        if slots:
            req["request"]["intent"]["slots"] = slots
    
    return req

def test_flow():
    print("--- Testing LaunchRequest ---")
    resp = requests.post(BASE_URL, json=create_request("LaunchRequest"))
    print(resp.json()['response']['outputSpeech']['ssml'])
    
    print("\n--- Testing ScriviIntent ---")
    resp = requests.post(BASE_URL, json=create_request("IntentRequest", "ScriviIntent"))
    print(resp.json()['response']['outputSpeech']['ssml'])
    session_attr = resp.json().get('sessionAttributes', {})
    
    print("\n--- Testing DictationIntent (Part 1) ---")
    slots = {"dictation": {"name": "dictation", "value": "Ciao mondo"}}
    resp = requests.post(BASE_URL, json=create_request("IntentRequest", "DictationIntent", slots, session_attr))
    print(resp.json()['response']['outputSpeech']['ssml'])
    session_attr = resp.json().get('sessionAttributes', {})
    
    print("\n--- Testing DictationIntent (Part 2) ---")
    slots = {"dictation": {"name": "dictation", "value": "come stai"}}
    resp = requests.post(BASE_URL, json=create_request("IntentRequest", "DictationIntent", slots, session_attr))
    print(resp.json()['response']['outputSpeech']['ssml'])
    session_attr = resp.json().get('sessionAttributes', {})
    
    print("\n--- Testing FinishIntent ---")
    resp = requests.post(BASE_URL, json=create_request("IntentRequest", "FinishIntent", slots=None, session_attributes=session_attr))
    print(resp.json()['response']['outputSpeech']['ssml'])
    
    print("\n--- Testing ChiudiIntent ---")
    resp = requests.post(BASE_URL, json=create_request("IntentRequest", "ChiudiIntent"))
    print(resp.json()['response']['outputSpeech']['ssml'])

if __name__ == "__main__":
    try:
        test_flow()
    except Exception as e:
        print(f"Test failed: {e}")
        print("Make sure app.py is running!")
