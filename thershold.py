import librosa
import numpy as np
from speech_to_text import transcribe
from pydub import AudioSegment
import speech_recognition as sr

import os

def get_sampling_rate(audio_file):

    y, sr = librosa.load(audio_file, sr=None)
    return sr

def get_hop_length(frame_length):
   
    hop_length = frame_length // 2
    return hop_length

def get_silence_threshold(audio_file, threshold_factor=150000):
  
    frame_duration_ms = 20
    sampling_rate=get_sampling_rate(audio_file)
    frame_length = int(sampling_rate * frame_duration_ms / 1000)
  
    hop_length=get_hop_length(frame_length)

    y, sr = librosa.load(audio_file)

    # Compute short-term energy
    energy = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]

    # Set threshold as a factor of the median energy
    threshold = np.median(energy) * threshold_factor

    return threshold


