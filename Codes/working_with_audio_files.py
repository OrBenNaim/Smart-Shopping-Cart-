from pydub import AudioSegment
from pydub.playback import play
import pygame
import pyaudio
import wave
import numpy as np
import time


def play_audio(audio_file_path):
    pygame.init()
    pygame.mixer.init()
    sound = pygame.mixer.Sound(audio_file_path)

    # Play the sound:
    sound.play()

    # Wait for the sound to finish playing (optional)
    while pygame.mixer.get_busy():
        pygame.time.delay(100)

    # Clean up
    pygame.quit()


def record_audio(audio_file_path, duration=4):
    # Declare about contstans variables:
    FRAMES_PER_BUFFER = 3200
    FORMAT = pyaudio.paInt16  # 16-bit resolution
    CHANNELS = 1
    RATE = 16000

    p = pyaudio.PyAudio()

    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=FRAMES_PER_BUFFER
    )

    print("\nStart Recording...")

    seconds = duration

    frames = []

    for i in range(0, int(RATE / FRAMES_PER_BUFFER * seconds)):
        data = stream.read(FRAMES_PER_BUFFER)
        frames.append(data)

    print("\nRecording Stopped")

    stream.stop_stream()
    stream.close()
    p.terminate()

    # save the audio frames as .wav file
    obj = wave.open(audio_file_path, "wb")
    obj.setnchannels(CHANNELS)
    obj.setsampwidth(p.get_sample_size(FORMAT))
    obj.setframerate(RATE)
    obj.writeframes(b"".join(frames))
    obj.close


""" This function trims the audio file: start_time is the amount of time in seconds
    to trim the audio file from the begining of the audio file"""


def trim_audio_file(audio_file_path, start_time, end_time=None):
    # Open an audio file
    audio_file_obj = AudioSegment.from_file(audio_file_path)

    # pydub does things in milliseconds
    start_time_in_milliseconds = start_time * 1000

    if end_time is not None:
        end_time_in_milliseconds = end_time * 1000

    if start_time > 0 and end_time is not None:
        new_audio_file_obj = audio_file_obj[start_time_in_milliseconds:end_time_in_milliseconds]

    elif start_time > 0 and end_time is None:
        new_audio_file_obj = audio_file_obj[start_time_in_milliseconds:]

    elif start_time == 0 and end_time is not None:
        new_audio_file_obj = audio_file_obj[:end_time_in_milliseconds]

        # save file
    new_audio_file_obj.export("/home/orbennaim1/Desktop/Final_Project/trimmed_audio_file.wav",
                              format="wav")

    print("\nNew Audio file is created and saved")


if __name__ == "__main__":
    Invalid_email_address_file = 'Invalid_email_address.wav'

    scanned_product_file = 'scanned_product.wav'

    over_weight_warning_file = 'over_weight_warning.wav'

    payment_approval_file = 'payment_approval.wav'

    put_your_products_on_weight_scale_file = 'put_your_products_on_weight_scale.wav'

    audio_files_list = [Invalid_email_address_file, scanned_product_file,
                        put_your_products_on_weight_scale_file, over_weight_warning_file, payment_approval_file]

    # record_audio("put_your_products_on_weight_scale.wav", 5)

    # play_audio("put_your_products_on_weight_scale.wav")

    # trim_audio_file(scanned_product_file_path, 0.7, 2.5)

    for audio_file in audio_files_list:
        play_audio(audio_file)


