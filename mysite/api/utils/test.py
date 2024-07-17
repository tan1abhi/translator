import logging
from flask import current_app, jsonify
import json
import requests
from api.voice_to_text import VoiceToText
import tempfile
import os
import base64
from api.text_to_voice import TextToVoice


def get_voice_id(file_path):
    url = f"https://graph.facebook.com/v20.0/{current_app.config['PHONE_NUMBER_ID']}/media"
    headers = {
        'Authorization': f"Bearer {current_app.config['ACCESS_TOKEN']}"
    }
    files = {
        'file': (file_path, open(file_path, 'rb'), 'audio/ogg'),
        'type': (None, 'audio/ogg'),
        'messaging_product': (None, 'whatsapp')
    }

    response = requests.post(url, headers=headers, files=files)
    
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


text_to_voice = TextToVoice("good morning welocome to function",'hi', 918882786162 , save_dir='audio_files')
audio_path = text_to_voice.text_to_base64_audio()
if audio_path:
    logging.info(f"Audio file created at: {audio_path}")
    media_id = get_voice_id(audio_path)
    # data = get_voice_message_input(current_app.config["RECIPIENT_WAID"],media_id)
    # send_message(data)

