import logging
from flask import current_app, jsonify
import json
import requests
from api.voice_to_text import VoiceToText
import tempfile
import os
import base64
from api.text_to_voice import TextToVoice

# from app.services.openai_service import generate_response
import re


def call_translate_api(content, lang, published_date):
    url = f"https://improved-fishstick-r9vwgw6p64q25vqj-8080.app.github.dev/translate/"
    headers = {
        "Content-Type": "application/json",
    }
    payload = {
        "content": content,
        "language": lang,
        "published_date": published_date,
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
        return response.json()  # Return the JSON response
    except requests.exceptions.RequestException as e:
        logging.error(f"Request to translate API failed: {e}")
        return None




#watsapp files for configuratuion and recieving of messages

def generate_response(response):
    return response + " is not a valid command \n please enter a valid command or send an hello for a quick intro" 


def generate_response_into(response):
    return "Hey welcome to the translation app here you can translate your text and voice message files in an instant \n please type translate to begin"


def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")




def get_text_message_input(recipient, text):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )

def get_voice_id(file_path):
    url = f"https://graph.facebook.com/v20.0/{current_app.config['PHONE_NUMBER_ID']}/media"
    headers = {
        'Authorization': f"Bearer {current_app.config['ACCESS_TOKEN']}"
    }
    files = {
        'file': (file_path, open(file_path, 'rb'), 'audio/ogg')
    }
    data = {
        'type': 'audio/ogg',
        'messaging_product': 'whatsapp'
    }

    response = requests.post(url, headers=headers, files=files, data=data)
    logging.info(response)
    if response.status_code == 200:
        logging.info(response.json)
        response_json = response.json()
        media_id = response_json.get('id')
        logging.info(f"Media ID: {media_id}")
        return media_id
    else:
        response.raise_for_status()


def get_voice_message_input(recipient,media_id):
    logging.info("logging data")
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "audio",
            "audio": {"id" : media_id},
        }
    )


def send_message(data):
    logging.info("sending message")
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
    }

    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"

    try:
        response = requests.post(
            url, data=data, headers=headers, timeout=10
        )  # 10 seconds timeout as an example
        logging.info(response.status_code)
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except (
        requests.RequestException
    ) as e:  # This will catch any general request exception
        logging.error(f"Request failed due to: {e}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
    else:
        # Process the response as normal
        log_http_response(response)
        return response


def process_text_for_whatsapp(text):
    # Remove brackets
    pattern = r"\【.*?\】"
    # Substitute the pattern with an empty string
    text = re.sub(pattern, "", text).strip()

    # Pattern to find double asterisks including the word(s) in between
    pattern = r"\*\*(.*?)\*\*"

    # Replacement pattern with single asterisks
    replacement = r"*\1*"

    # Substitute occurrences of the pattern with the replacement
    whatsapp_style_text = re.sub(pattern, replacement, text)

    return whatsapp_style_text

user_states = {}

def process_whatsapp_message(body):
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]
    message = body["entry"][0]["changes"][0]["value"]["messages"][0]

    message_type = message.get("type")
    if message_type == "audio":
        audio = message["audio"]
        audio_id = audio["id"]
        logging.info(audio)

        audio_url = f"https://graph.facebook.com/v20.0/{audio_id}/"
        headers={
            "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}"
        }

        try:
            response = requests.get(audio_url, headers=headers)
            if response.status_code == 200:
                audio_info = response.json()
                media_url = audio_info.get("url")

                if media_url:
                    # Download the media from the obtained URL with proper authentication
                    media_response = requests.get(media_url, headers=headers)
                    if media_response.status_code == 200:
                        audio_data = media_response.content

                        # Encode the bytes as base64
                        encoded_audio = base64.b64encode(audio_data)
                        voice_to_text = VoiceToText(encoded_audio)
                        message_body = voice_to_text.base64_to_text()

                        if not message_body:
                            message_body = "Failed to convert audio to text."
                        logging.info(message_body)
                        
                    else:
                        logging.error(f"Failed to download media. Status Code: {media_response.status_code}")
                else:
                    logging.error("No media URL found in the response.")
            else:
                logging.error(f"Failed to retrieve audio information. Status Code: {response.status_code}")

        except requests.exceptions.RequestException as e:
            logging.error(f"Error during request: {str(e)}")
        
        # Read the contents of the file as bytes
        

    else:
        message_body = message["text"]["body"]


    if wa_id not in user_states:
        user_states[wa_id] = {
            'state': 'initial',
            'voice_translate': False,
            'translate': False,
            'awaiting_language': False,
            'awaiting_translation_text': False,
            'language': None
        }

    intro = {"hello", "hi", "Hello", "Hi", "hey", "Hey", "HELLO", "HI", "HEY"}

    if message_body in intro:
        response = generate_response_into(message_body)
        data = get_text_message_input(current_app.config["RECIPIENT_WAID"], response)
        send_message(data)
        return

    state = user_states[wa_id]['state']

    if state == 'initial':
        if message_body.lower() == "voice translate":
            user_states[wa_id]['voice_translate'] = True
            user_states[wa_id]['state'] = 'select_language'
            send_language_options(wa_id)
        elif message_body.lower() == "translate":
            user_states[wa_id]['translate'] = True
            user_states[wa_id]['state'] = 'select_language'
            send_language_options(wa_id)
        else:
            response = generate_response(message_body)
            data = get_text_message_input(current_app.config["RECIPIENT_WAID"], response)
            send_message(data)
    elif state == 'select_language':
        if handle_language_selection(wa_id, message_body):
            user_states[wa_id]['state'] = 'awaiting_translation_text'
            prompt_for_text(wa_id)
        else:
            send_language_options(wa_id)
    elif state == 'awaiting_translation_text':
        language = user_states[wa_id]['language']
        if user_states[wa_id]['voice_translate']:
            translate_response = call_translate_api(message_body, language, "2024-07-10")
            if translate_response:
                translated_content = translate_response.get('translated_content', '')
                handle_voice_message_response(wa_id, translated_content , language)
            else:
                logging.error("Failed to get a response from the translate API")
                data = get_text_message_input(current_app.config["RECIPIENT_WAID"], "Translation failed. Please try again.")
        else:
            handle_translation(wa_id, message_body, language)
        user_states[wa_id]['state'] = 'initial'
    else:
        response = generate_response(message_body)
        data = get_text_message_input(current_app.config["RECIPIENT_WAID"], response)
        send_message(data)






def send_language_options(recipient):
    text = "Please select a language:\n1. English\n2. Hindi\n3. Tamil\n4. Gujarati\n5. Marathi\n6. Assamese\n7. Bengali\n8. Kannada\n9. Kashmiri\n10. Konkani\n11. Malayalam\n12. Manipuri\n13. Nepali\n14. Odia\n15. Punjabi\n16. Sanskrit\n17. Sindhi\n18. Telugu\n19. Urdu\n20. Bodo\n21. Santhali\n22. Maithili\n23. Dogri"
    data = get_text_message_input(recipient, text)
    send_message(data)


def handle_language_selection(wa_id, message_body):
    language_map = {
        "1":"english",    
        "2": "hindi",
        "3": "tamil",
        "4": "gujarati",
        "5": "marathi",
        "6": "assamese",
        "7": "bengali",
        "8": "kannada",
        "9": "kashmiri",
        "10": "konkani",
        "11": "malayalam",
        "12": "manipuri",
        "13": "nepali",
        "14": "odia",
        "15": "punjabi",
        "16": "sanskrit",
        "17": "sindhi",
        "18": "telugu",
        "19": "urdu",
        "20": "bodo",
        "21": "santhali",
        "22": "maithili",
        "23": "dogri"
    }
    if message_body in language_map:
        user_states[wa_id]['language'] = language_map[message_body]
        user_states[wa_id]['awaiting_language'] = False
        return True
    return False

def prompt_for_text(recipient):
    text = "Please enter the text / voice message you want to translate."
    data = get_text_message_input(recipient, text)
    send_message(data)


def handle_translation(wa_id, text, language):
    user_states[wa_id]['awaiting_translation_text'] = False
    translate_response = call_translate_api(text, language, "2024-07-10")  # example parameters

    if translate_response:
        translated_content = translate_response.get('translated_content', '')
        data = get_text_message_input(current_app.config["RECIPIENT_WAID"], translated_content)
        send_message(data)
    else:
        logging.error("Failed to get a response from the translate API")
        data = get_text_message_input(current_app.config["RECIPIENT_WAID"], "Translation failed. Please try again.")
        send_message(data)

def prompt_for_voice_message(recipient):
    text = "Would you like to receive the translation as a voice message? Please reply with 'yes' or 'no'."
    data = get_text_message_input(recipient, text)
    send_message(data)
    user_states[recipient]['awaiting_voice_message'] = True

def handle_voice_message_response(wa_id, text ,language):
    language_map = {
        "english": "en",
        "hindi": "hi",
        "tamil": "ta",
        "gujarati": "gu",
        "marathi": "mr",
        "assamese": "as",
        "bengali": "bn",
        "kannada": "kn",
        "kashmiri": "ks",
        "konkani": "kok",
        "malayalam": "ml",
        "manipuri": "mni",
        "nepali": "ne",
        "odia": "or",
        "punjabi": "pa",
        "sanskrit": "sa",
        "sindhi": "sd",
        "telugu": "te",
        "urdu": "ur",
        "bodo": "brx",
        "santhali": "sat",
        "maithili": "mai",
        "dogri": "doi"
    }
    language_code = language_map.get(language, None)
    if not language_code:
        logging.error(f"Language {language} is not supported.")
        return None
    text_to_voice = TextToVoice(text,language_code, wa_id, save_dir='audio_files')
    audio_path = text_to_voice.text_to_base64_audio()
    if audio_path:
        logging.info(f"Audio file created at: {audio_path}")
        media_id = get_voice_id(audio_path)
        logging.info(media_id)
        data = get_voice_message_input(current_app.config["RECIPIENT_WAID"],media_id)
        logging.info("data logging sucessfull")
        send_message(data)

    else:
        logging.error("Failed to create audio file")
        return None
    



def is_valid_whatsapp_message(body):
    """
    Check if the incoming webhook event has a valid WhatsApp message structure.
    """
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )