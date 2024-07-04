import speech_recognition as sr
from pydub import AudioSegment



class VoiceToText:
    def __init__(self, m4a_file):
        self.m4a_file = m4a_file
        self.wav_file = "output.wav"
        self.recognizer = sr.Recognizer()

    def m4a_to_wav(self):
        audio = AudioSegment.from_file(self.m4a_file)
        audio.export(self.wav_file, format="wav")

    def convert_to_text(self):
        self.m4a_to_wav()
        with sr.AudioFile(self.wav_file) as source:
            print("Processing WAV file...")
            self.recognizer.adjust_for_ambient_noise(source)
            audio = self.recognizer.record(source)
        
        try:
            text = self.recognizer.recognize_google(audio)
            text = text.lower()
            return text
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            return None
        


