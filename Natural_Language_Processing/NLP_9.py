from google.cloud import speech_v1p1beta1 as speech
from google.cloud import texttospeech

# Transcribe Audio to Text
def transcribe_audio(audio_file):
    client = speech.SpeechClient()
    with open(audio_file, "rb") as audio_file:
        audio_data = audio_file.read()
        audio = speech.RecognitionAudio(content=audio_data)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US"
    )
    response = client.recognize(config=config, audio=audio)
    transcript = ""
    for result in response.results:
        transcript += result.alternatives[0].transcript
    return transcript

# Convert Text to Audio in a Different Language
def convert_text_to_audio(text, output_file, language_code):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code, ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    with open(output_file, "wb") as out_file:
        out_file.write(response.audio_content)

# Example usage
audio_file = "path/to/audio.wav"
transcribed_text = transcribe_audio(audio_file)
output_text_file = "path/to/transcribed_text.txt"
with open(output_text_file, "w") as text_file:
    text_file.write(transcribed_text)
output_audio_file = "path/to/output_audio.mp3"
convert_text_to_audio(transcribed_text, output_audio_file, "fr-FR")
