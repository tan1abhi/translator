import io
import logging
import speech_recognition as sr
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError

# Path to your audio file


class VoiceToText:
    def __init__(self, ogg_path):
        self.ogg_path = ogg_path
        self.recognizer = sr.Recognizer()

    def ogg_to_text(self):
        try:
            # Convert Ogg data to audio segment in memory
            logging.info("Loading Ogg data...")
            audio_segment = AudioSegment.from_file(self.ogg_path, format='ogg')
            
            # Export audio segment to a file-like object in WAV format
            wav_data = io.BytesIO()
            audio_segment.export(wav_data, format='wav')
            wav_data.seek(0)  # Rewind the stream for reading

            # Recognize text from audio segment
            logging.info("Recognizing text from audio data...")
            with sr.AudioFile(wav_data) as source:
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.record(source)

            text = self.recognizer.recognize_google(audio)
            return text

        except FileNotFoundError as e:
            logging.error(f"FFmpeg not found: {e}")
            return None
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
