import time
import json
import jwt
import random
import string
import requests
import os
from locust import User, task, between, events
import socketio

# Configuration
JWT_SECRET = "jwt_secret_key"
JWT_ALGORITHM = "HS256"
ADMIN_SECRET_KEY = "y8T4vQl5ia2LoU3wbFJ8iWQn917Y3YOR"
USER_CREATION_URL = "https://api-fof-ish-dev.brototype.xyz/user/admin"
WS_HOST = "https://api-fof-ish-dev.brototype.xyz"
USER_CACHE_FILE = "user_cache.json"
MAX_TESTING_USER = 10000

def generate_random_username(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def generate_random_name(length=6):
    return ''.join(random.choices(string.ascii_uppercase, k=length))

def generate_random_telegram_id():
    return random.randint(10**8, 10**9 - 1)  # 9-digit number

def load_user_cache():
    if os.path.exists(USER_CACHE_FILE):
        with open(USER_CACHE_FILE, 'r') as f:
            return json.load(f)
    return []

def save_user_cache(users):
    with open(USER_CACHE_FILE, 'w') as f:
        json.dump(users, f)

def create_user():
    telegram_id = generate_random_telegram_id()
    username = generate_random_username()
    payload = {
        "telegram_id": telegram_id,
        "admin_secret_key": ADMIN_SECRET_KEY,
        "first_name": 'Locust ' + generate_random_name(),
        "last_name": generate_random_name(),
        "ref_code": random.randint(10**10, 10**11 - 1),  # 11-digit number
        "username": username
    }
    response = requests.post(USER_CREATION_URL, json=payload)
    if response.status_code == 201:
        print(f"Create user successfully: {response.text}")
        user_data = response.json()
        new_user = {
            "id": user_data['data'].get('id'),
            "telegram_id": telegram_id,
            "username": username
        }
        return new_user
    else:
        print(f"Failed to create user: {response.text}")
        return None

def get_or_create_user():
    users = load_user_cache()
    if users and len(users) > MAX_TESTING_USER:
        return random.choice(users)
    else:
        new_user = create_user()
        if new_user:
            users.append(new_user)
            save_user_cache(users)
        return new_user

def generate_jwt_token(user_id, telegram_id, username):
    payload = {
        "sub": user_id,
        "telegram_id": telegram_id,
        "user_name": username,
        "iat": int(time.time()),
        "exp": int(time.time()) + 21600  # Token expires in 6 hours
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

class SocketIOUser(User):
    abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = None
        self.user = None
        self.host = WS_HOST

    def on_start(self):
        self.user = get_or_create_user()
        print('User : ', self.user)
        if self.user:
            self.connect_to_socket()

    def on_stop(self):
        if self.client:
            self.client.disconnect()

    def connect_to_socket(self):
        if not self.user:
            return

        token = generate_jwt_token(self.user['id'], self.user['telegram_id'], self.user['username'])
        
        self.client = socketio.Client(reconnection=False)
        
        @self.client.event
        def connect():
            print(f"Connected to Socket.IO server: User {self.user['username']}")

        @self.client.event
        def disconnect():
            print(f"Disconnected from Socket.IO server: User {self.user['username']}")

        @self.client.on('events')
        def on_message(data):
            print(f"Received: {data}")

        try:
            print('Connect to socket with token : ', token)
            self.client.connect(self.host, headers={
                "Authorization": f"Bearer {token}"
            }, transports=['polling'])
        except Exception as e:
            print(f"Connection failed: {repr(e)}")

    def emit_event(self, event_name, data):
        start_time = time.time()
        try:
            self.client.emit(event_name, data)
            total_time = (time.time() - start_time) * 1000
            events.request.fire(
                request_type="websocket",
                name=event_name,
                response_time=total_time,
                response_length=0,
                exception=None,
                context={},
            )
        except Exception as e:
            total_time = (time.time() - start_time) * 1000
            events.request.fire(
                request_type="websocket",
                name=event_name,
                response_time=total_time,
                response_length=0,
                exception=e,
                context={},
            )

class MyUser(SocketIOUser):
    wait_time = between(1, 3)

    @task
    def send_events(self):
        if self.client and self.client.connected:
            self.emit_event('events', 'Hello, WebSocket!')
            self.emit_event('flip-square', {'col': random.randint(0, 2), 'row': random.randint(0, 2)})

# To run this test, use the following command:
# locust -f locust_socketio_test.py