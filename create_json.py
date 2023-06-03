import requests

url = 'http://127.0.0.1:5000/channels'
jwt_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY4NTc3MzExNSwianRpIjoiNmNlY2UyYjgtOWU5My00ZWZlLWJiMmUtNjcxY2NhYzJmZTZmIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6WzI3MzcyXSwibmJmIjoxNjg1NzczMTE1LCJleHAiOjE2ODU3NzQwMTV9.Yf7sSK1IS61D5XmQm3LHJx3eIlJ03hMrgX1ml1fBw-Q'
channels = ["Whatsapp", "SMS", "RCS"]

headers = {
    'Authorization': f'Bearer {jwt_token}',
    'Content-Type': 'application/json'
}
data = {
    'jwt': jwt_token,
    'channels': channels
}

response = requests.post(url, json=data, headers=headers)
print(response.status_code)
print(response.content)
