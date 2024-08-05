import logging
from flask import current_app, jsonify
import json
import time
import threading
import time
import requests
from api.voice_to_text import VoiceToText
import base64
from api.text_to_voice import TextToVoice
# from app.services.openai_service import generate_response
import re
from api.model import UserState , db

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
    logging.info(f"Sending payload to translate API") 
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status() 
        # logging.info(f"Translate API response: {response.json()}") # Raises an HTTPError if the HTTP request returned an unsuccessful status code
        return response.json()  # Return the JSON response
    except requests.exceptions.RequestException as e:
        logging.error(f"Request to translate API failed: {e}")
        logging.error(f"Payload: {payload}")
        logging.error(f"Headers: {headers}")
        return None




#watsapp files for configuratuion and recieving of messages

def generate_response(response):
    return response + " is not a valid command \n please enter a valid command or send an hello for a quick intro" 


def generate_response_into(response):
    return "Hey welcome to the translation app here you can translate your text and voice message files in an instant you can \n \n 1) directly send text or voice message to me or just type 1 \n \n 2) type translate or enter 2 for non stop text translation in one language \n \n  3) type voice translate or enter 3 for voice translation non stop voice translation in one language  \n\n To quit just type end or break  \n\n *In mode1 you are allowed to enter one message at a time for multiple message translations switch to mode 2 or 3 by appliying the break command*"


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
        'file': (file_path, open(file_path, 'rb'), 'audio/mpeg')
    }
    data = {
        'type': 'audio/mpeg',
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


def send_whatsapp_message(wa_id):
    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"
    headers = {
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
        "Content-Type": "application/json",
    }
    data = {
        "messaging_product": "whatsapp",
        "to": wa_id,
        "type": "template",
        "template": {"name": "hello_world", "language": {"code": "en_US"}},
    }
    response = requests.post(url, headers=headers, json=data)
    return response


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

activity_timestamps = {}
INACTIVITY_LIMIT = 60 

def reset_inactive_users():
    while True:
        current_time = time.time()
        for wa_id, last_activity in list(activity_timestamps.items()):
            if current_time - last_activity > INACTIVITY_LIMIT:
                logging.info(f"Resetting state for inactive user: {wa_id}")
                user = UserState(
                    wa_id = wa_id,
                    state = 'initial',
                    voice_translate = False,
                    translate = False,
                    awaiting_language = False,
                    awaiting_translation_text = False,
                    send_to_someone = False,
                    language = None,
                    awaiting_number = False,
                    message_body = "",
                    recipient_number = None,
                )
                del activity_timestamps[wa_id]
        time.sleep(5)  # Check every 5 seconds

# Start the background thread
threading.Thread(target=reset_inactive_users, daemon=True).start()


def reset_user_state(user):
    user.state = 'initial'
    user.list = False
    user.voice_translate = False
    user.translate = False
    user.awaiting_language = False
    user.awaiting_translation_text = False
    user.send_to_someone = False
    user.language = None
    user.awaiting_number = False
    user.message_body = ""
    user.recipient_number = None
    db.session.commit()



def process_whatsapp_message(body):
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]    
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]
    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    logging.info(message)

    message_type = message.get("type")

    user = UserState.query.filter_by(wa_id=wa_id).first()
    state = UserState.state

    if message_type == "contacts":
        phone = message["contacts"][0]["phones"][0]
        phone_no = phone.get("wa_id")
        logging.info("Contact message processed")

        recipient = UserState.query.filter_by(wa_id=phone_no).first()

        if phone_no and not recipient:
            recipient = UserState(
                wa_id=phone_no,
                state='initial',
                voice_translate=False,
                translate=False,
                awaiting_language=False,
                awaiting_translation_text=False,
                send_to_someone=False,
                language=None,
                awaiting_number=False,
                message_body="",
                recipient_number=None,
            )
            db.session.add(recipient)
            db.session.commit()

        user = UserState.query.filter_by(wa_id=wa_id).first()
        
        if user:
            user.recipient_number = phone_no
            translate_response = call_translate_api(user.message_body, user.language, "2024-07-10")
            
            if translate_response:
                translated_content = translate_response.get('translated_content', '')
                handle_voice_message_response(user.recipient_number, translated_content, user.language)
                data = get_text_message_input(user.recipient_number, translated_content)
                send_message(data)

            user.message_body = ""
            user.recipient_number = ""
            data = get_text_message_input(wa_id, text='message sent successfully')
            send_message(data)

            user.state = 'initial'
            user.list = False
            user.voice_translate = False
            user.translate = False
            user.awaiting_language = False
            user.awaiting_translation_text = False
            user.send_to_someone = False
            user.language = None
            user.awaiting_number = False
            user.message_body = ""
            user.recipient_number = None
            db.session.commit()

            logging.info(user.wa_id) # Update phone number if user already exists
        return

    elif message_type == "audio":
        audio = message["audio"]
        audio_id = audio["id"]
        logging.info(audio)

        audio_url = f"https://graph.facebook.com/v20.0/{audio_id}/"
        headers = {
            "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}"
        }

        try:
            response = requests.get(audio_url, headers=headers)
            if response.status_code == 200:
                audio_info = response.json()
                media_url = audio_info.get("url")

                if media_url:
                    media_response = requests.get(media_url, headers=headers)
                    if media_response.status_code == 200:
                        audio_data = media_response.content

                        encoded_audio = base64.b64encode(audio_data)
                        voice_to_text = VoiceToText(encoded_audio)
                        message_body = voice_to_text.base64_to_text()

                        if not message_body:
                            message_body = "Failed to convert audio to text."
                        logging.info(message_body)
                    else:
                        logging.error(f"Failed to download media. Status Code: {media_response.status_code}")
                        message_body = "Failed to download media."
                else:
                    logging.error("No media URL found in the response.")
                    message_body = "No media URL found in the response."
            else:
                logging.error(f"Failed to retrieve audio information. Status Code: {response.status_code}")
                message_body = "Failed to retrieve audio information."
        except requests.exceptions.RequestException as e:
            logging.error(f"Error during request: {str(e)}")
            message_body = "Error during request."

    elif message_type == "text":
        message_body = message["text"]["body"]

        if not UserState.query.filter_by(wa_id=wa_id).first():
            user = UserState(
                wa_id=wa_id,
                state= 'initial',
                list = False,
                voice_translate = False,
                translate = False,
                awaiting_language = False,
                awaiting_translation_text = False,
                send_to_someone = False,
                language = None,
                awaiting_number = False,
                message_body = "",
                recipient_number = None,
            )

            activity_timestamps[wa_id] = time.time()

        intro = {"hello", "hi", "Hello", "Hi", "hey", "Hey", "HELLO", "HI", "HEY"}

        end = {"end","kill","break"}

        if message_body.lower() in end:
            logging.info("end message")
            reset_user_state(user)
            response = "thankyou for using our services"
            data = get_text_message_input(wa_id,response)
            send_message(data)
            db.session.commit()
            return

        if message_body.lower() in intro:
            logging.info("intro message")
            reset_user_state(user)
            response = generate_response_into(message_body)
            data = get_text_message_input(wa_id, response)
            send_message(data)
            db.session.commit()
            return

        state = user.state

        if state == 'initial':
            logging.info("intitial - state ")
            if message_body.lower() == "voice translate" or message_body == '3':
                user.voice_translate = True
                user.state = 'select_language'
                response = "please enter the language you want to translate messages in and type list to get a list of avilable languages"
                data = get_text_message_input(wa_id,response)
                send_message(data)

               
            elif message_body.lower() == "translate" or message_body == '2':
                user.translate = True
                user.state = 'select_language'
                response = "please enter the language you want to translate messages and type list to get a list of avilable languages"
                data = get_text_message_input(wa_id,response)
                send_message(data)
                
            elif message_body.lower() == '1':
                response = "please enter the text you want to translate"
                data = get_text_message_input(wa_id, response)
                send_message(data)
            else:
                user.state = 'select_language'
                user.message_body = message_body
                response = "please enter the language you want to translate messages in and type list to get a list of avilable languages"
                data = get_text_message_input(wa_id,response)
                send_message(data)
                
        elif state == 'select_language':
            logging.info( " select_language")
            if message_body.lower() == 'list':
                send_language_options(wa_id)

            
            if handle_language_selection(wa_id, message_body):
                user.state = 'awaiting_translation_text'
                if user.message_body == "":
                    prompt_for_text(wa_id)
                else:
                    proceed_with_translation(wa_id, user.message_body)
            else:
                response = "please enter the language you want to translate the messages"
                data = get_text_message_input(wa_id,response)
                send_message(data)

        elif state == 'awaiting_translation_text':

            logging.info("awaiting_translation_text")
            language = user.language
            if user.voice_translate == True:
                logging.info("voice translate")
                translate_response = call_translate_api(message_body, language, "2024-07-10")
                if translate_response:
                    translated_content = translate_response.get('translated_content', '')
                    handle_voice_message_response(wa_id, translated_content, language)
                    
                else:
                    logging.error("Failed to get a response from the translate API")
                    data = get_text_message_input(wa_id, "Translation failed. Please try again.")
                    send_message(data)
            elif user.translate:
                logging.info("translate")
                handle_translation(wa_id, message_body, language)
            else:
                proceed_with_translation(wa_id, user.message_body)
                user.message_body = ""

        elif state == 'send_to_someone':
            logging.info("send_to_someone")
            if message_body.lower() == "yes":
                prompt_to_get_number(wa_id)
                user.state = 'awaiting_number'
            else:
                response = "Thank you for using the translation service."
                data = get_text_message_input(wa_id, response)
                send_message(data)
                reset_user_state(user)
        elif state == 'awaiting_number':
            logging.info("awating_number ")
            user.recipient_number = message_body
            response = f"Message will be sent to {user.recipient_number}."
            data = get_text_message_input(wa_id, response)
            send_message(data)
            reset_user_state(user)
        else:
            response = generate_response(message_body)
            data = get_text_message_input(wa_id, response)
            reset_user_state(user)
            send_message(data)
    else:
        response = "please send a valid message type accepted types are \n1) text \n2) audio \n3) contact"
        data = get_text_message_input(wa_id, response)
        send_message(data)
    db.session.commit()

def proceed_with_translation(wa_id, message_body):
    user = UserState.query.filter_by(wa_id=wa_id).first()
    language = user.language
    handle_translation(wa_id, message_body, language)
    translate_response = call_translate_api(message_body, language, "2024-07-10")
    if translate_response:
        translated_content = translate_response.get('translated_content', '')
        handle_voice_message_response(wa_id, translated_content, language)
        user.state = 'send_to_someone'
    else:
        logging.error("Failed to get a response from the translate API")
        data = get_text_message_input(wa_id, "Translation failed. Please try again.")
        send_message(data)
        user.state = 'initial'
    db.session.commit()
    prompt_to_send_recipient(wa_id)


        

def send_language_options(recipient):
    text = "Please select a language:\n1. English\n2. Hindi\n3. Tamil\n4. Gujarati\n5. Marathi\n6. Assamese\n7. Bengali\n8. Kannada\n9. Kashmiri\n10. Konkani\n11. Malayalam\n12. Manipuri\n13. Nepali\n14. Odia\n15. Punjabi\n16. Sanskrit\n17. Sindhi\n18. Telugu\n19. Urdu\n20. Bodo\n21. Santhali\n22. Maithili\n23. Dogri"
    data = get_text_message_input(recipient, text)
    send_message(data)


def handle_language_selection(wa_id, message_body):
    user = UserState.query.filter_by(wa_id=wa_id).first()
    language_map = {
        "1": "english",
        "english": "english",
        "eng": "english",
        "2": "hindi",
        "hindi": "hindi",
        "hi": "hindi",
        "3": "tamil",
        "tamil": "tamil",
        "ta": "tamil",
        "4": "gujarati",
        "gujarati": "gujarati",
        "gu": "gujarati",
        "5": "marathi",
        "marathi": "marathi",
        "ma": "marathi",
        "6": "assamese",
        "assamese": "assamese",
        "as": "assamese",
        "7": "bengali",
        "bengali": "bengali",
        "ben": "bengali",
        "8": "kannada",
        "kannada": "kannada",
        "kn": "kannada",
        "9": "kashmiri",
        "kashmiri": "kashmiri",
        "ks": "kashmiri",
        "10": "konkani",
        "konkani": "konkani",
        "kok": "konkani",
        "11": "malayalam",
        "malayalam": "malayalam",
        "ml": "malayalam",
        "12": "manipuri",
        "manipuri": "manipuri",
        "mni": "manipuri",
        "13": "nepali",
        "nepali": "nepali",
        "ne": "nepali",
        "14": "odia",
        "odia": "odia",
        "or": "odia",
        "15": "punjabi",
        "punjabi": "punjabi",
        "pa": "punjabi",
        "16": "sanskrit",
        "sanskrit": "sanskrit",
        "sa": "sanskrit",
        "17": "sindhi",
        "sindhi": "sindhi",
        "sd": "sindhi",
        "18": "telugu",
        "telugu": "telugu",
        "te": "telugu",
        "19": "urdu",
        "urdu": "urdu",
        "ur": "urdu",
        "20": "bodo",
        "bodo": "bodo",
        "brx": "bodo",
        "21": "santhali",
        "santhali": "santhali",
        "sat": "santhali",
        "22": "maithili",
        "maithili": "maithili",
        "mai": "maithili",
        "23": "dogri",
        "dogri": "dogri"
    }
    
    if message_body.lower() in language_map:
        user.language = language_map[message_body.lower()]
        user.awaiting_language = False
        return True
    return False

def prompt_for_text(recipient):
    text = "Please enter the text / voice message you want to translate."
    data = get_text_message_input(recipient, text)
    send_message(data)

def handle_translation(wa_id, text, language):
    user = UserState.query.filter_by(wa_id=wa_id).first()
    user.awaiting_translation_text = False
    translate_response = call_translate_api(text, language, "2024-07-10")  # example parameters

    if translate_response:
        translated_content = translate_response.get('translated_content', '')
        data = get_text_message_input(wa_id, translated_content)
        send_message(data)
    else:
        user.state = 'initial'
        logging.error("Failed to get a response from the translate API")
        data = get_text_message_input(wa_id, "Translation failed. Please try again.")
        send_message(data)
    db.session.commit()

def prompt_to_send_recipient(recipient):
    user = UserState.query.filter_by(wa_id=recipient).first()
    text = "Do you want to send this data to someone else? please type yes or no"
    data = get_text_message_input(recipient, text)
    send_message(data)
    user.send_to_someone = True
    db.session.commit()

def prompt_to_get_number(recipient):
    user = UserState.query.filter_by(wa_id=recipient).first()
    text = "Please share their contact number"
    data = get_text_message_input(recipient,text)
    send_message(data)
    user.awaiting_number = True
    db.session.commit()

def prompt_for_voice_message(recipient):
    user = UserState.query.filter_by(wa_id=recipient).first()
    text = "Would you like to receive the translation as a voice message? Please reply with 'yes' or 'no'."
    data = get_text_message_input(recipient, text)
    send_message(data)
    user.awaiting_voice_message = True
    db.session.commit()

def handle_voice_message_response(wa_id, text ,language):
    user = UserState.query.filter_by(wa_id=wa_id).first()
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
        data = get_voice_message_input(wa_id,media_id)
        logging.info("data logging sucessfull")
        send_message(data)

    else:
        user.state = 'initial'
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