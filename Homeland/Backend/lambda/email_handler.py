# email_handler.py

import json
import os
import boto3
from botocore.exceptions import ClientError

def send_email(sender_address, receiver_address, region, recepient_email, recepient_query):
    SUBJECT = "CHIP - User Query Needs Manual Assistance"
    
    BODY_TEXT = (
        "Hi,\n\n"
        "Our information portal encountered a user query that it couldn't answer. We need your assistance to provide a manual response.\n"
        "User Email: {email} \n"
        "Query: {query} \n"
        "Please review and reply to the user directly using the email address mentioned above. \n\n"
        "Thanks,\n"
        "Cyber Homeland Information Portal (CHIP)\r\n"
    ).format(email=recepient_email, query=recepient_query)

    CHARSET = "UTF-8"

    client = boto3.client('ses', region_name=region)

    try:
        response = client.send_email(
            Destination={
                'ToAddresses': [receiver_address],
            },
            Message={
                'Body': {
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=sender_address,
            ReplyToAddresses=[recepient_email],
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:")
        print(response['MessageId'])
        return {
            "statusCode" : 200,
            "headers" : {
                'Access-Control-Allow-Origin' : '*',
                'Content-Type' : 'application/json'
            },
            "body" : json.dumps({
                "email_sent": True
            })
        }
        
