import os
import sys
import json

import time

import requests
from flask import Flask, request, redirect, url_for, flash
from flask import render_template

app = Flask(__name__)

@app.route('/')
def index():    
	return render_template("index.html")

@app.route('/webhook', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/webhook', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message 
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text

                    message_text = '+'.join(message_text.split(" "))

                    send_message(sender_id, "Check check")
                    send_state(sender_id)
                    time.sleep(5)
                    send_message(sender_id, "www.yahoo.com")
                    send_state(sender_id)                    
                    time.sleep(5)
                    send_message(sender_id, "www.fb.com")
                    

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

    return "ok", 200

def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
    return "ok", 200
def send_state(recipient_id):

    log("sending state to {recipient}: ".format(recipient=recipient_id))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "sender_action":"typing_on"

    })
    r = requests.post("https://graph.facebook.com/v2.8/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
    return "ok", 200

def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)
