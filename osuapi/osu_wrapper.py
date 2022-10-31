import requests
import json
from dotenv import load_dotenv


API_URL = 'https://osu.ppy.sh/api/v2'
TOKEN_URL = 'https://osu.ppy.sh/oauth/token'


class OsuWrapper:

    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret

        # possible timeout of auth token after inactivity?
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.get_token()}'
        }

    def get_token(self):
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials',
            'scope': 'public'
        }

        response = requests.post(TOKEN_URL, data=data)
        return response.json().get('access_token')

    def get_match(self, match_id):
        return requests.get(f'{API_URL}/matches/{match_id}', headers=self.headers).json()

    def get_user(self, user_id, mode="", is_id=True):
        """
        Gets a osu user based off of id.

        Args:
            user_id: the username or id of the user you want data on
            mode: the game category you want data of the user on. Format:
                fruits  osu!catch
                mania   osu!mania
                osu     osu!standard
                taiko   osu!taiko
            is_id: whether or not the user_id is a username or an id.

        Returns:
            list: a list of strings representing the header columns

        """
        params = {
            'key': 'id' if is_id else 'username'
        }

        return requests.get(f'{API_URL}/users/{user_id}/{mode}', headers=self.headers, params=params).json()

