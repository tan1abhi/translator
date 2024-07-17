import os
import threading
import time
import logging
from gtts import gTTS
from pydub import AudioSegment

class TextToVoice:
    def __init__(self, text, language , wa_id, save_dir='audio_files'):
        self.text = text
        self.language = language
        self.save_dir = save_dir
        self.wa_id = wa_id

    def text_to_base64_audio(self):
        try:
            # Create the audio directory if it doesn't exist
            if not os.path.exists(self.save_dir):
                os.makedirs(self.save_dir)

            # Generate audio from text
            logging.info("Generating audio from text...")
            tts = gTTS(self.text, lang=self.language)
            temp_mp3_path = os.path.join(self.save_dir  , f"temp_audio{self.wa_id}.mp3")
            tts.save(temp_mp3_path)

            # Convert the MP3 file to OGG format
            audio = AudioSegment.from_mp3(temp_mp3_path)
            ogg_path = os.path.join(self.save_dir, f"output_audio{self.wa_id}.ogg")
            audio.export(ogg_path, format='ogg')
            logging.info(f"Audio file saved to: {ogg_path}")

            # Schedule file deletion after 5 minutes
            # threading.Thread(target=delete_file, args=(ogg_path, 60)).start()

            # Remove the temporary MP3 file
            os.remove(temp_mp3_path)

            return ogg_path

        except PermissionError as e:
            logging.error(f"Permission error: {e}")
            return None
        except Exception as e:
            logging.error(f"Error converting text to audio: {e}")
            return None

# Function to delete file after a delay
def delete_file(file_path, delay):
    time.sleep(delay)
    try:
        os.remove(file_path)
        logging.info(f"Deleted file: {file_path}")
    except Exception as e:
        logging.error(f"Error deleting file: {file_path} - {str(e)}")

# Example usage
# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO)
    
#     text = "शुभ संध्या दोस्तों"
#     language = 'hi'  # Specify the language code here
#     ttv = TextToVoice(text, language=language, save_dir='audio_files')
#     audio_path = ttv.text_to_base64_audio()

#     if audio_path:
#         print(f"Audio file created at: {audio_path}")
#     else:
#         print("Failed to create audio file")
