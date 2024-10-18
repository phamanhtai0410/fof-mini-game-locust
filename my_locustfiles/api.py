import time
import random
import string
import json
import hashlib
import hmac
from urllib.parse import urlencode
from locust import HttpUser, task, between

class TelegramUser(HttpUser):
    wait_time = between(1, 3)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot_token = "7691290816:AAGu9XeGPZg-i7OOyyCxyEB5e_2NcuujgKg"
        self.jwt_token = ''
        self.host = 'https://api-fof-ish-dev.brototype.xyz'

    def generate_init_data(self, user_id, first_name, username):
        user_data = {
            "id": user_id,
            "first_name": first_name,
            "username": username,
            "language_code": "en"
        }
        
        auth_date = int(time.time())
        
        init_data = {
            "query_id": f"AAHdF{random.randint(100000000000, 999999999999)}",
            "user": json.dumps(user_data),
            "auth_date": auth_date
        }
        
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(init_data.items()))
        
        secret_key = hmac.new("WebAppData".encode(), self.bot_token.encode(), hashlib.sha256).digest()
        hash_value = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        init_data["hash"] = hash_value
        return urlencode(init_data)

    @task()
    def auth_me(self):
        response_auth_me = self.client.get("/auth/me")
        print(f'Resp to call with jwt : {self.jwt_token}: ', response_auth_me.json())

    # @task(1)
    # def create_test_account(self):
    #     user_id = random.randint(10000000, 999999999)
    #     first_name = ''.join(random.choices(string.ascii_lowercase, k=8))
    #     username = f"test_user_{user_id}"
        
    #     init_data = self.generate_init_data(user_id, first_name, username)
        
    #     payload = {
    #         "initData": init_data,
    #         "is_premium": random.choice([True, False])
    #     }
        
    #     response = self.client.post("/auth/jwt", json=payload)
        
    #     if response.status_code == 201:
    #         # Create a new user
    #         print(f"Created test account for {username}: ", response.json()['data']['token'])
    #         self.jwt_token = response.json()['data']['token']
    #         print(f'Start to call with jwt : {self.jwt_token}')

    #         # Auth/me
    #         headers = {"Authorization": f"Bearer {self.jwt_token}"}
    #         response_auth_me = self.client.get("/auth/me", headers=headers)
    #         print(f'Resp to call with jwt : {self.jwt_token}: ', response_auth_me.json())

    #         # # Flip square
    #         # headers = {"Authorization": f"Bearer {self.jwt_token}"}
    #         # response_game_flip = self.client.post("/game/flip-game/f")
    #     else:
    #         print(f"Failed to create test account: {response.text}")
        
    # @task(5)
    # def get_flip_game_state(self):
    #     if self.jwt_token:
    #         headers = {"Authorization": f"Bearer {self.jwt_token}"}
    #         resp = self.client.get("/game/flip-game", headers=headers, name="/game/flip-game")
    #         print(f'Get game state with token : {self.jwt_token}', resp.json())

    # @task(10)
    # def flip_square(self):
    #     if self.jwt_token:
    #         headers = {"Authorization": f"Bearer {self.jwt_token}"}
    #         payload = {
    #             "row": random.randint(0, 4),
    #             "col": random.randint(0, 4),
    #             "level": random.randint(1, 3)
    #         }
    #         resp = self.client.post("/game/flip-game/flip", json=payload, headers=headers, name="/game/flip-game/flip")
    #         print(f'Flip square with token : {self.jwt_token}', resp.json())

    # @task(2)
    # def claim_mission(self):
    #     if self.jwt_token:
    #         headers = {"Authorization": f"Bearer {self.jwt_token}"}
    #         resp = self.client.post("/game/flip-game/mission/claim", headers=headers, name="/game/flip-game/mission/claim")
    #         print(f'Claim mission with token : {self.jwt_token}', resp.json())

    # @task(1)
    # def reset_mission(self):
    #     if self.jwt_token:
    #         headers = {"Authorization": f"Bearer {self.jwt_token}"}
    #         resp = self.client.post("/game/flip-game/mission/reset", headers=headers, name="/game/flip-game/mission/reset")
    #         print(f'Reset mission with token : {self.jwt_token}', resp.json())

def run():
    import os
    from locust import events
    
    @events.test_start.add_listener
    def on_test_start(environment, **kwargs):
        print("A new test is starting")

    @events.test_stop.add_listener
    def on_test_stop(environment, **kwargs):
        print("A new test is ending")

if __name__ == "__main__":
    run()