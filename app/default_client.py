import requests

start = 'http://localhost:5050/'

request = requests.post(start + '/auth/login', {'username': 'Giulio', 'password': '12345'})
response = request.json()
print(response)