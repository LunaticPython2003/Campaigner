import requests

url = 'http://127.0.0.1:5000/channels'
jwt_token = 'your_token'
channels = {
    "WhatsApp": {"Phone": 4539405830, "Message":"Something"},
    "SMS": {"Phone": 3578923952, "Message": "Something"}
}

chunks = 50

headers = {
    'Authorization': f'Bearer {jwt_token}',
    'Content-Type': 'application/json'
}
data = {
    'channels': channels,
    'chunks': chunks
}

response = requests.post(url, json=data, headers=headers)
print(response.status_code)
print(response.content)
