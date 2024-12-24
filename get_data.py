import os
import json
import datetime
import time
import requests
from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SCOPES = [
            'https://www.googleapis.com/auth/fitness.activity.read',
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

DATA_SOURCES = {
    "steps": "derived:com.google.step_count.delta:com.google.android.gms:estimated_steps",
    "dist": "derived:com.google.distance.delta:com.google.android.gms:merge_distance_delta",
    "bpm": "derived:com.google.heart_rate.bpm:com.google.android.gms:merge_heart_rate_bpm",
    "rhr": "derived:com.google.heart_rate.bpm:com.google.android.gms:resting_heart_rate<-merge_heart_rate_bpm",
    "sleep" : "derived:com.google.sleep.segment:com.google.android.gms:sleep_from_activity<-raw:com.google.activity.segment:com.heytap.wearable.health:stream_sleep",
    "cal" : "derived:com.google.calories.bmr:com.google.android.gms:merged",
    "move": "derived:com.google.active_minutes:com.google.android.gms:from_steps<-estimated_steps",
    "points" : "derived:com.google.heart_minutes:com.google.android.gms:merge_heart_minutes",
    "height" : "derived:com.google.height:com.google.android.gms:merge_height",
    "weight" : "derived:com.google.weight:com.google.android.gms:merge_weight",
    "duration": "derived:com.google.activity.segment:com.google.android.gms:merge_activity_segments"
}

app = Flask(__name__)

credentials = Credentials.from_authorized_user_file('token.json', SCOPES)
service = build('fitness', 'v1', credentials=credentials)

@app.route('/get-steps')
def get_steps_data():
    start_time = int(datetime.datetime(year=2024, month=11, day=1, hour=0).timestamp()) * 1000
    end_time = int(datetime.datetime(year=2024, month=11, day=11, hour=0).timestamp()) * 1000
    body = {
        'aggregateBy': [
            {
                'dataTypeName': 'com.google.step_count.delta',
                'dataSourceId': DATA_SOURCES['steps']
            }
        ],
        'startTimeMillis': start_time,
        'endTimeMillis': end_time
    }
    try:
        response = service.users().dataset().aggregate(
            userId='me',
            body=body
        ).execute()
        return jsonify(response)
    except Exception as e:
        return f"Error: {e}"

@app.route('/get-daily-steps')
def get_daily_steps_data():
    start_time = int(datetime.datetime(year=2024, month=11, day=1, hour=0).timestamp()) * 1000
    end_time = int(datetime.datetime(year=2024, month=11, day=11, hour=0).timestamp()) * 1000
    body = {
        'aggregateBy': [
            {
                'dataTypeName': 'com.google.step_count.delta',
                'dataSourceId': 'derived:com.google.step_count.delta:com.google.android.gms:estimated_steps'
            }
        ],
        'startTimeMillis': start_time,
        'endTimeMillis': end_time,
        'bucketByTime': {'durationMillis': 86400000}  
    }
    try:
        response = service.users().dataset().aggregate(
            userId='me',
            body=body
        ).execute()
        daily_steps = []
        for bucket in response.get('bucket', []):
            date = datetime.datetime.fromtimestamp(int(bucket['startTimeMillis']) // 1000).strftime('%Y-%m-%d')
            steps = 0
            for dataset in bucket.get('dataset', []):
                for point in dataset.get('point', []):
                    steps += sum([val.get('intVal', 0) for val in point.get('value', [])])
            daily_steps.append({'date': date, 'steps': steps})
        return jsonify({'daily_steps': daily_steps})
    except Exception as e:
        return f"Error: {e}", 500
    
@app.route('/get-monthly-steps')
def get_monthly_steps_data():
    monthly_steps = {}
    try:
        for month in range(1, 13):
            start_time = int(datetime.datetime(year=2024, month=month, day=1, hour=0).timestamp()) * 1000
            if month == 12: 
                end_time = int(datetime.datetime(year=2025, month=1, day=1, hour=0).timestamp()) * 1000
            else:
                end_time = int(datetime.datetime(year=2024, month=month + 1, day=1, hour=0).timestamp()) * 1000
            body = {
                'aggregateBy': [
                    {
                        'dataTypeName': 'com.google.step_count.delta'
                    }
                ],
                'startTimeMillis': start_time,
                'endTimeMillis': end_time,
                'bucketByTime': {
                    'durationMillis': 86400000  
                }
            }
            response = service.users().dataset().aggregate(
                userId='me',
                body=body
            ).execute()
            total_steps = 0
            if 'bucket' in response:
                for bucket in response['bucket']:
                    for dataset in bucket['dataset']:
                        for point in dataset['point']:
                            for value in point['value']:
                                if 'intVal' in value:
                                    total_steps += value['intVal']
            month_name = datetime.date(2024, month, 1).strftime('%B')
            monthly_steps[month_name] = total_steps
        return jsonify({"year": "2024", "monthly_steps": monthly_steps})
    except Exception as e:
        return f"Error: {e}"

@app.route('/get-monthly-bpm')
def get_monthly_average_bpm_data():
    monthly_bpm = {}
    try:
        for month in range(1, 13):
            start_time = int(datetime.datetime(year=2024, month=month, day=1, hour=0).timestamp()) * 1000
            if month == 12:  
                end_time = int(datetime.datetime(year=2025, month=1, day=1, hour=0).timestamp()) * 1000
            else:
                end_time = int(datetime.datetime(year=2024, month=month + 1, day=1, hour=0).timestamp()) * 1000
            body = {
                'aggregateBy': [
                    {
                        'dataTypeName': 'com.google.heart_rate.bpm'
                    }
                ],
                'startTimeMillis': start_time,
                'endTimeMillis': end_time,
                'bucketByTime': {
                    'durationMillis': 86400000  
                }
            }
            response = service.users().dataset().aggregate(
                userId='me',
                body=body
            ).execute()
            total_bpm = 0
            num_days = 0  
            if 'bucket' in response:
                for bucket in response['bucket']:
                    num_days += 1  
                    for dataset in bucket['dataset']:
                        for point in dataset['point']:
                            for value in point['value']:
                                if 'fpVal' in value:
                                    total_bpm = value['fpVal']
            month_name = datetime.date(2024, month, 1).strftime('%B')
            monthly_bpm[month_name] = total_bpm
        return jsonify({"year": "2024", "monthly_average_bpm": monthly_bpm})
    except Exception as e:
        return f"Error: {e}"

@app.route('/get-distance')
def get_distance_data():
    start_time = int(datetime.datetime(year=2024, month=11, day=1, hour=0).timestamp()) * 1000
    end_time = int(datetime.datetime(year=2024, month=11, day=11, hour=0).timestamp()) * 1000
    body = {
        'aggregateBy': [
            {
                'dataTypeName': 'com.google.distance.delta',
                'dataSourceId': DATA_SOURCES['dist']
            }
        ],
        'startTimeMillis': start_time,
        'endTimeMillis': end_time
    }
    try:
        response = service.users().dataset().aggregate(
            userId='me',
            body=body
        ).execute()
        return jsonify(response)
    except Exception as e:
        return f"Error: {e}"
    
@app.route('/get-rhr')
def get_rhr_data():
    try:
        bpm_data = requests.get('http://localhost:8000/get-bpm')
        bpm_json = json.loads(bpm_data)
        points_data = bpm_json['raw_response']['bucket'][0]['dataset'][0]['point']
        rhr_values = [point['fpVal'] for point in points_data if 'fpVal' in point]
        if rhr_values:
            rhr = min(rhr_values) 
            rhr = str(rhr)
            return jsonify({
                'success': True,
                'rhr': rhr,
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get-bpm')
def get_bpm_data():
    start_time = int(datetime.datetime(year=2024, month=11, day=1, hour=0).timestamp()) * 1000
    end_time = int(datetime.datetime(year=2024, month=11, day=11, hour=0).timestamp()) * 1000
    body = {
        'aggregateBy': [
            {
                'dataTypeName': 'com.google.heart_rate.bpm',
                'dataSourceId': DATA_SOURCES['bpm']
            }
        ],
        'startTimeMillis': start_time,
        'endTimeMillis': end_time
    }
    try:
        response = service.users().dataset().aggregate(
            userId='me',
            body=body
        ).execute()
        bpm_data = []
        if 'bucket' in response:
            for bucket in response['bucket']:
                for dataset in bucket['dataset']:
                    for point in dataset['point']:
                        for value in point['value']:
                            if 'fpVal' in value:
                                bpm_data.append(value['fpVal'])
        return jsonify({
            'bpm_data': bpm_data,
            'raw_response': response
        })
    except Exception as e:
        return f"Error: {e}"

@app.route('/get-daily-bpm')
def get_daily_bpm_data():
    start_time = int(datetime.datetime(year=2024, month=11, day=1, hour=0).timestamp()) * 1000
    end_time = int(datetime.datetime(year=2024, month=11, day=11, hour=0).timestamp()) * 1000
    body = {
        'aggregateBy': [
            {
                'dataTypeName': 'com.google.heart_rate.bpm',
                'dataSourceId': 'derived:com.google.heart_rate.bpm:com.google.android.gms:merge_heart_rate_bpm'
            }
        ],
        'startTimeMillis': start_time,
        'endTimeMillis': end_time,
        'bucketByTime': {'durationMillis': 86400000}  
    }
    try:
        response = service.users().dataset().aggregate(
            userId='me',
            body=body
        ).execute()
        daily_bpm_data = []
        if 'bucket' in response:
            for bucket in response['bucket']:
                date = datetime.datetime.fromtimestamp(int(bucket['startTimeMillis']) // 1000).strftime('%Y-%m-%d')
                bpm_values = []
                for dataset in bucket['dataset']:
                    for point in dataset['point']:
                        for value in point['value']:
                            if 'fpVal' in value:
                                bpm_values.append(value['fpVal'])
                if bpm_values:
                    daily_average_bpm = sum(bpm_values) / len(bpm_values)
                else:
                    daily_average_bpm = None  
                daily_bpm_data.append({'date': date, 'average_bpm': daily_average_bpm})
        return jsonify({'daily_bpm_data': daily_bpm_data})
    except Exception as e:
        return f"Error: {e}", 500
 
@app.route('/get-height')
def get_height_data():
    start_time = int(datetime.datetime(year=2024, month=11, day=1, hour=0).timestamp()) * 1000
    end_time = int(datetime.datetime(year=2024, month=11, day=11, hour=0).timestamp()) * 1000
    body = {
        'aggregateBy': [
            {
                'dataTypeName': 'com.google.height',
                'dataSourceId': DATA_SOURCES['height']
            }
        ],
        'startTimeMillis': start_time,
        'endTimeMillis': end_time
    }
    try:
        response = service.users().dataset().aggregate(
            userId='me',
            body=body
        ).execute()
        height_data = []
        if 'bucket' in response:
            for bucket in response['bucket']:
                for dataset in bucket['dataset']:
                    for point in dataset['point']:
                        for value in point['value']:
                            if 'fpVal' in value:
                                height_data.append(value['fpVal'])
        
        return jsonify({
            'height_data': height_data,
            'raw_response': response
        })
    except Exception as e:
        return f"Error: {e}"

@app.route('/get-weight')
def get_weight_data():
    start_time = int(datetime.datetime(year=2024, month=11, day=1, hour=0).timestamp()) * 1000
    end_time = int(datetime.datetime(year=2024, month=11, day=11, hour=0).timestamp()) * 1000
    body = {
        'aggregateBy': [
            {
                'dataTypeName': 'com.google.weight',
                'dataSourceId': DATA_SOURCES['weight']
            }
        ],
        'startTimeMillis': start_time,
        'endTimeMillis': end_time
    }
    try:
        response = service.users().dataset().aggregate(
            userId='me',
            body=body
        ).execute()
        weight_data = []
        if 'bucket' in response:
            for bucket in response['bucket']:
                for dataset in bucket['dataset']:
                    for point in dataset['point']:
                        for value in point['value']:
                            if 'fpVal' in value:
                                weight_data.append(value['fpVal'])
        return jsonify({
            'weight_data': weight_data,
            'raw_response': response
        })
    except Exception as e:
        return f"Error: {e}"

    
@app.route('/get-calories')
def get_calories_data():
    start_time = int(datetime.datetime(year=2024, month=11, day=1, hour=0).timestamp()) * 1000
    end_time = int(datetime.datetime(year=2024, month=11, day=11, hour=0).timestamp()) * 1000
    body = {
        'aggregateBy': [
            {
                'dataTypeName': 'com.google.calories.gms'
            }
        ],
        'startTimeMillis': start_time,
        'endTimeMillis': end_time
    }
    try:
        response = service.users().dataset().aggregate(
            userId='me',
            body=body
        ).execute()
        return response
    except Exception as e:
        return jsonify({'error': str(e)})

def get_bmi(height_data, weight_data):
    if not height_data or not weight_data:
        raise ValueError("Height and weight data must not be empty")
    avg_height = sum(height_data) / len(height_data)
    avg_weight = sum(weight_data) / len(weight_data)
    bmi = round(avg_weight / (avg_height ** 2), 2)
    return bmi

def get_bmi_category(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif 18.5 <= bmi < 25:
        return "Normal"
    elif 25 <= bmi < 30:
        return "Overweight"
    else:
        return "Obese"

@app.route('/get-bmi')
def calculate_bmi():
    try:
        height_response = requests.get('http://localhost:8000/get-height')
        height = height_response.json()
        weight_response = requests.get('http://localhost:8000/get-weight')
        weight = weight_response.json()
        height_data = height['height_data']
        weight_data = weight['weight_data']
        bmi = get_bmi(height_data, weight_data)
        bmi_category = get_bmi_category(bmi)
        return jsonify({
            'success': True,
            'bmi': bmi,
            'bmi_category': bmi_category
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/get-duration')
def get_duration_data():
    start_time = int(datetime.datetime(year=2024, month=11, day=1, hour=0).timestamp()) * 1000
    end_time = int(datetime.datetime(year=2024, month=11, day=11, hour=0).timestamp()) * 1000
    body = {
        'aggregateBy': [
            {
                'dataTypeName': 'com.google.active_minutes',
                'dataSourceId': DATA_SOURCES['duration']
            }
        ],
        'startTimeMillis': start_time,
        'endTimeMillis': end_time
    }
    try:
        response = service.users().dataset().aggregate(
            userId='me',
            body=body
        ).execute()
        duration_data = []
        if 'bucket' in response:
            for bucket in response['bucket']:
                for dataset in bucket['dataset']:
                    for point in dataset['point']:
                        for value in point['value']:
                            if 'intVal' in value:
                                duration_data.append(value['intVal'])
        return jsonify({
            'duration_data': duration_data,
            'raw_response': response
        })
    except Exception as e:
        return f"Error: {e}"

@app.route('/get-pai')
def get_pai():
    try:
        total_pai = 0
        duration_response = requests.get('http://localhost:8000/get-duration')
        duration = duration_response.json()
        duration_value = duration.get('duration_data')
        if not isinstance(duration_value, list) or not all(isinstance(d, (int, float)) for d in duration_value):
            return "Invalid duration data format", 400
        avg_duration = sum(duration_value) / len(duration_value)
        heart_rate_response = requests.get('http://localhost:8000/get-bpm')
        if heart_rate_response.status_code != 200:
            return "Error fetching heart rate data", 500
        heart_rate = heart_rate_response.json()
        bpm_data = heart_rate.get('bpm_data')
        if not isinstance(bpm_data, list) or not all(isinstance(bpm, (int, float)) for bpm in bpm_data):
            return "Invalid heart rate data format", 400
        max_heart_rate = max(bpm_data)
        for bpm in bpm_data:
            intensity = bpm / max_heart_rate
            if intensity >= 0.6:
                pai_points = (intensity - 0.5) * avg_duration * 10
                total_pai += pai_points
        return jsonify({
            "success": True,
            "total_pai": round(total_pai, 2)
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=8000)
