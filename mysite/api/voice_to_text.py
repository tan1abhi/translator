import base64
import io
import logging
import speech_recognition as sr
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError





class VoiceToText:
    def __init__(self, base64_data):
        self.base64_data = base64_data
        self.recognizer = sr.Recognizer()

    def base64_to_text(self):
        try:
            # Decode base64 data to bytes
            logging.info("Decoding base64 data...")
            audio_data = base64.b64decode(self.base64_data)
            
            # Convert bytes data to audio segment in memory
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_data), format='ogg')
            
            # Get raw audio data
            raw_audio_data = audio_segment.raw_data
            
            # Create an AudioData instance
            audio = sr.AudioData(raw_audio_data, audio_segment.frame_rate, audio_segment.sample_width)
            
            # Recognize text from audio segment
            logging.info("Recognizing text from audio data...")
            text = self.recognizer.recognize_google(audio)
            return text

        except CouldntDecodeError as e:
            logging.error(f"Error decoding audio: {e}")
            return None
        except sr.UnknownValueError:
            logging.error("Google Speech Recognition could not understand audio")
            return None
        except sr.RequestError as e:
            logging.error(f"Could not request results from Google Speech Recognition service; {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return None


# Example usage:

# # Assuming you have the path to the Ogg file and want to convert it to text
# ogg_path = path  # Replace with your actual path to the Ogg file
# voice_to_text = VoiceToText(ogg_path)
# text = voice_to_text.ogg_to_text()
# if text:
#     print(f"Converted text: {text}")
# else:
#     print("Failed to convert audio to text.")
