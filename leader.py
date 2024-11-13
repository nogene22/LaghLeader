import os
import json
import time
import threading
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.rtm_v2 import RTMClient
from collections import defaultdict
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

slack_token = os.getenv("SLACK_BOT_TOKEN")
client = WebClient(token=slack_token)
rtm_client = RTMClient(token=slack_token)

user_message_count = defaultdict(int)

try:
    with open("message_counts.json", "r") as file:
        user_message_count = defaultdict(int, json.load(file))
except FileNotFoundError:
    print("No previous message count data found. Starting fresh.")

@rtm_client.on("message")
def handle_message(event_data):
    event = event_data['data']
    if 'user' in event and 'text' in event:
        user_id = event['user']
        user_message_count[user_id] += 1

@rtm_client.on("app_mention")
def handle_app_mention(event_data):
    text = event_data["data"].get("text", "").lower()
    channel_id = event_data['data']['channel']
    if "leader" in text:
        post_leaderboard(channel_id)

def post_leaderboard(channel_id):
    try:
        leaderboard = sorted(user_message_count.items(), key=lambda x: x[1], reverse=True)[:10]
        message = "Leaderboard - Top 10 Users:\n"
        for idx, (user_id, count) in enumerate(leaderboard, start=1):
            user_info = client.users_info(user=user_id)
            username = user_info['user']['name']
            message += f"{idx}. {username} - {count} posts\n"
        client.chat_postMessage(channel=channel_id, text=message)
    except SlackApiError as e:
        print(f"Error posting message: {e}")

def save_message_counts():
    while True:
        with open("message_counts.json", "w") as file:
            json.dump(user_message_count, file)
        time.sleep(60)

threading.Thread(target=save_message_counts, daemon=True).start()

threading.Thread(target=rtm_client.start, daemon=True).start()

@app.route('/leader', methods=['POST'])
def leader_command():
    data = request.form
    channel_id = data.get("channel_id")
    leaderboard = sorted(user_message_count.items(), key=lambda x: x[1], reverse=True)[:10]
    message = "Leaderboard - Top 10 Users:\n"
    for idx, (user_id, count) in enumerate(leaderboard, start=1):
        user_info = client.users_info(user=user_id)
        username = user_info['user']['name']
        message += f"{idx}. {username} - {count} posts\n"
    return jsonify({
        "response_type": "in_channel",
        "text": message
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
