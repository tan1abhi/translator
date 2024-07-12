import base64

# Path to your audio file
path = r"C:\Users\hp\OneDrive\Desktop\test_audio_file.ogg"

# Read the contents of the file as bytes
with open(path, "rb") as audio_file:
    audio_bytes = audio_file.read()

# Encode the bytes as base64
encoded_audio = base64.b64encode(audio_bytes)

# Print or use the base64 encoded data
print("hello")
print(encoded_audio)
