from os import getenv

from ratelimiter import RateLimiter
import requests

api_key = getenv('API-KEY')
api_url = 'http://' + getenv('API_URL')
authorization_header = {"X-API-KEY": api_key, 'Content-Type': 'application/json'}

