import requests
import json
from datetime import datetime, timedelta
import mysql.connector


# def get_upcoming_matches(sport):
#     api_key = "e036698cb1dc47db0f3ea21179201ba8bf6d4a529d02b956bef75a8698a768c7"
#     base_url = f"https://allsportsapi.com/api/{sport}"
#
#     # Calculate the "from" and "to" dates
#     today = datetime.today().date()
#     from_date = today.strftime("%Y-%m-%d")
#     to_date = (today + timedelta(days=14)).strftime("%Y-%m-%d")
#
#     # API endpoint for upcoming matches
#     endpoint = f"{base_url}/?met=Fixtures&APIkey={api_key}&from={from_date}&to={to_date}"
#
#     try:
#         response = requests.get(endpoint)
#         data = json.loads(response.text)
#         matches = data['result'][:5]
#         num_matches = len(matches)
#         return matches, num_matches
#
#     except requests.exceptions.RequestException:
#         print("Error: Connection error.")

# get_upcoming_matches("football")


