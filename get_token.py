import os
import json
from flask import Flask, request, redirect
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' 

SCOPES = ['https://www.googleapis.com/auth/fitness.activity.read',
          'https://www.googleapis.com/auth/fitness.blood_glucose.read',
          'https://www.googleapis.com/auth/fitness.blood_pressure.read',
          'https://www.googleapis.com/auth/fitness.body.read',
          'https://www.googleapis.com/auth/fitness.body_temperature.read',
          'https://www.googleapis.com/auth/fitness.heart_rate.read',
          'https://www.googleapis.com/auth/fitness.location.read',
          'https://www.googleapis.com/auth/fitness.nutrition.read',
          'https://www.googleapis.com/auth/fitness.oxygen_saturation.read',
          'https://www.googleapis.com/auth/fitness.reproductive_health.read',
          'https://www.googleapis.com/auth/fitness.sleep.read'
          ]

app = Flask(__name__)

flow = Flow.from_client_secrets_file(
    'credentials.json',
    scopes=SCOPES,
    redirect_uri='http://localhost:8000/get-token'
)

@app.route('/')
def index():
    authorization_url, state = flow.authorization_url(access_type='offline')
    return redirect(authorization_url)

@app.route('/get-token')
def get_token():
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    with open('token.json', 'w') as token:
        token.write(credentials.to_json())
    return 'Authentication successful! You can close this window.'

if __name__ == '__main__':
    app.run(port=8000)