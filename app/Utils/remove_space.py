# ruff: noqa
import datetime
import io
import os
import asyncio
from pprint import pprint
from random import sample
import logging as log

import librosa
import noisereduce as nr
import requests
import numpy as np
import soundfile as sf
from pydub import AudioSegment
from pydub.silence import split_on_silence
from pydub.silence import detect_silence

TEMP_FOLDER = "audios"


def remove_noise(filename):
    # file_path.seek(0)
    data, rate = librosa.load(filename, sr=None)

    if not np.all(np.isfinite(data)):
        print("Audio data contains invalid values.")
        data = np.nan_to_num(data)

    # Perform noise reduction
    reduced_noise_audio = nr.reduce_noise(y=data, sr=rate)

    # Construct the output filename by adding '-nc' before the file extension
    output_filename = filename.rsplit(".", 1)[0] + "_nc.wav"

    # Save the processed audio data as a .wav file
    sf.write(output_filename, reduced_noise_audio, rate, format="wav")
    
    os.remove(filename)
    print("========= Deleted original wav file ==========")
    
    return output_filename


def get_file_type(filename):
    _, file_extension = os.path.splitext(filename)
    return file_extension.lower()

def calculate_loudness(audio_file):  
    y, sr = librosa.load(audio_file, sr=None)  
    return np.sqrt(np.mean(y**2))  

def adjust_volume_to_match_reference(original_audio, reference_audio):  
    # Calculate loudness of both audio files  
    original_loudness = calculate_loudness(original_audio)  
    reference_loudness = calculate_loudness(reference_audio)  
    print("original_loudness: ", original_loudness)
    print("reference_loudness: ", reference_loudness)
    
    # Determine the gain in dB needed to match reference  
    original_sound = AudioSegment.from_file(original_audio, format="wav")  
    gain_needed = 10 * (np.log10(reference_loudness / original_loudness) if original_loudness != 0 else 0)  

    print("gain_needed: ", gain_needed)
    
    # Adjust the volume of the audio  
    adjusted_sound = original_sound.apply_gain(gain_needed)  
    return adjusted_sound  

def remove_silence_from_audio(audio_file_name, silence_thresh=-15, min_silence_len=1000):
    ###### Remove noise from the audio
    noise_reduced_filename = remove_noise(audio_file_name)
    # file_type = get_file_type(noise_reduced_stream)
    # # print(file_type)

    # Load the noise-reducced audio file
    # raw_audio, sr = librosa.load(noise_reduced_filename, sr=None)
    # current_rms = np.sqrt(np.mean(raw_audio**2))
    # target_rms = 0.1
    # gain = target_rms / current_rms
    # normalized_audio = raw_audio * gain

    adjusted_audio = adjust_volume_to_match_reference(noise_reduced_filename, "./silence_audios/output.mp3")  


    audio_buffer = io.BytesIO()
    adjusted_audio.export(audio_buffer, format="wav")  

    # sf.write(audio_buffer, normalized_audio, sr, format='WAV')
    audio_buffer.seek(0)

    audio = AudioSegment.from_file(audio_buffer, format="wav")
    # raw_audio = AudioSegment.from_file(noise_reduced_filename, format="wav")
    # audio = raw_audio.apply_gain(-raw_audio.max_dBFS + -1.0)
    ##################################

    # Detect the silent segments in the audio  
    silences = detect_silence(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh, seek_step=10)  
    # Adjust detecting silence times (start and end) from milliseconds to seconds  
    silences = [(start / 1000, stop / 1000) for start, stop in silences]  
    
    current_stop = 0.0
    combined_audio = AudioSegment.empty()

    for start, stop in silences:
        start_ms = int(current_stop)  
        end_ms = int(start * 1000) 
        
        chunk = audio[start_ms: end_ms]
        combined_audio += chunk
        
        # print("stop, start: ", stop, start)
        if stop - start > 2:
            delta = stop - start
            # print("delta 1: ", delta)
            delta = int(2 + (delta-2) // 5 * 5)
            # print("delta 2: ", delta)
            if delta > 60:
                combined_audio += AudioSegment.from_file("./silence_audios/output.mp3", format="mp3")
            else:
                combined_audio += AudioSegment.from_file(f"./silence_audios/output_{delta}.mp3", format="mp3")
        
        # print(f"  Start time: {current_stop / 1000:.2f} seconds")
        # print(f"  End time: {start:.2f} seconds")
        # print(f"  Duration: {len(chunk) / 1000:.2f} seconds")
        current_stop = stop * 1000
        
        # print(len(chunk))
        
    if current_stop < len(audio):
        combined_audio += audio[current_stop:]

    print("===== Processing audio file =====")
    
    output_filename = audio_file_name.rsplit(".", 1)[0] + "_p.mp3"  # processed
    combined_audio.export(output_filename, format="mp3")
    
    
    os.remove(noise_reduced_filename)
    print("===== Deleted _nc.wav file =====")
    print("===== Finished processing audio file =====")
    
    return output_filename

def process_archive_silence(audio_file_name):
    audio_file_name = remove_silence_from_audio(audio_file_name, silence_thresh=-30)
    return audio_file_name


async def process_audio(audio_file_name):
    return await asyncio.to_thread(process_archive_silence, audio_file_name)
