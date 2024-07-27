from datetime import timedelta
from pydub import AudioSegment, silence
import os



from thershold import get_silence_threshold
import subprocess
import re
import numpy as np
def get_noise_level(audio_file):
    audio = AudioSegment.from_wav(audio_file)
    audio_array = np.array(audio.get_array_of_samples())
    rms = np.sqrt(np.mean(np.square(audio_array)))
    return rms

def get_silence_duration(input_file, noise_level, min_silence_duration):
    command = [
        "ffmpeg",
        "-i", input_file,
        "-af", f"silencedetect=noise={noise_level}dB:d={min_silence_duration}",
        "-f", "null", "-"
    ]
    output = str(subprocess.run(command,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE))
    lines = output.replace("\\r", "").split("\\n")
    time_list = []
    for line in lines:
        if ("silence_duration" in line):
            words = line.split(" ")
            for i in range(len(words)):
                if "silence_duration" in words[i]:
                    time_list.append(float(words[i + 1]))
    if(len(time_list)==0):
       return 1
    else:
       return min(time_list)    # Calculate and return the minimum silence duration
 

# Example usage



def detect_and_split_silence(input_audio_path, silence_thresh, min_silence_len):    
    
    audio = AudioSegment.from_wav(input_audio_path)
    silent_ranges = silence.detect_silence(audio, silence_thresh=silence_thresh, min_silence_len=min_silence_len)
    timestamps_agent=[]
    for x in range(0,len(silent_ranges)-1):
       timestamps_agent.append({"start":silent_ranges[x][1],"end":silent_ranges[x+1][0]})
    return timestamps_agent

def milliseconds_to_hms(milliseconds):

    duration = timedelta(milliseconds=milliseconds)
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return hours, minutes, seconds

def hms_to_str(h,m,s):
    hours=0
    minutes=0
    seconds=0
    if(h<10):
       hours="0"+str(h)
    else:
       hours=h
    if(m<10):
       minutes="0"+str(m)
    else:
       minutes=m
    if(s<10):
       seconds="0"+str(s)
    else:
       seconds=s
    return str(str(hours)+":"+str(minutes)+":"+str(seconds))
t = 18* 60 * 1000

def get_audio_duration(file_path):
    audio = AudioSegment.from_wav(file_path)
    duration_in_seconds = len(audio) / 1000.0  # Convert milliseconds to seconds 
    s=duration_in_seconds
    return float(s)


import os
import speech_recognition as sr


import json
def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

def transcribe_audio_chunk_with_openai(audio_file_path, start_time, end_time,speaker_label,temp_chunk,language):
    recognizer = sr.Recognizer()
    audio = AudioSegment.from_wav(audio_file_path)
    chunk = audio[start_time :end_time + 1000]
    temp_file_path = temp_chunk
    chunk.export(temp_file_path, format="wav")
    with sr.AudioFile(temp_file_path) as source:
        audio_data = recognizer.record(source)
      
       # print(words)
        try:          
                  
             try:
                 if(language.lower()=="fr"):
                    l='fr-CH'
                 if(language.lower()=="de"):
                    l='de-CH'
                 if(language.lower()=="en"):
                    l='en-US'
                 if(language.lower()=="it"):
                    l="it-CH"
                 text1 = recognizer.recognize_google(audio_data,language=l)
            
                 return {"speaker":speaker_label,"start":milliseconds_to_hms(start_time),"end":milliseconds_to_hms(end_time),"content":text1}
             except sr.UnknownValueError as e:
                 pass 
             except sr.RequestError as e1 :
                 pass
            else:
                 return {"speaker":speaker_label,"start":milliseconds_to_hms(start_time),"end":milliseconds_to_hms(end_time),"content":text}
        except Exception as e:
          
             pass
  


def download_audio_from_twilio(url,output_file):
    import requests
    try:
     x = requests.get(url, allow_redirects=True)
     print("x============",x)  
     open(output_file, 'wb').write(x.content)
    except Exception as e:
       print("error:",e)
right_channel="right_channel.wav"
left_channel="left_channel.wav"

def separate_stereo_channels(audio_file, left_output, right_output):
    audio = AudioSegment.from_wav(audio_file) 
    channels = audio.split_to_mono()
    if len(channels) != 2:
        raise ValueError("The provided audio file doesn't seem to be stereo.")
    left_channel = channels[1]
    right_channel = channels[0]
    left_channel.export(left_output, format="wav") 
    right_channel.export(right_output, format="wav")
customer_audio_chunks = None
agent_audio_chunks = None
def function1(left_channel,m_s_r,th,language):
   try:
    l1=detect_and_split_silence(left_channel,silence_thresh=-(th),min_silence_len=int(m_s_r))
    #print(l1)
    segments_customer=[]
    for x in l1:
      o=transcribe_audio_chunk_with_openai(left_channel,x["start"],x["end"],"customer","temp_chunk_left.wav",language)
      segments_customer.append(o)
    customer_audio_chunks=segments_customer
    return customer_audio_chunks
   except Exception as e :
      return str(e)

def function2(right_channel,m_s_r,th,language):
   try:
    segments_agent=[]
    l=detect_and_split_silence(right_channel,silence_thresh=-(th),min_silence_len=int(m_s_r))
    for y in l:
      o=transcribe_audio_chunk_with_openai(right_channel,y["start"],y["end"],"agent","temp_chunk_right.wav",language)
      segments_agent.append(o)
    agent_audio_chunks=segments_agent
    return agent_audio_chunks
   except Exception as e:
      return str(e)

def transcribe_with_speaker_labels(url,language):
 try:
  download_audio_from_twilio(url,"recording.wav")
  separate_stereo_channels("recording.wav",left_channel,right_channel)
  th=get_silence_threshold("left_channel.wav")
 #print(th)
  if(th>52):
   th=40
# else:
 #  print(th)
  s=get_noise_level("right_channel.wav")
  s1=get_noise_level("left_channel.wav")

  m_s_d=0
  if(get_audio_duration('recording.wav')>1000):
    m_s_d=1.1
  else:
    m_s_d=1
  silences = get_silence_duration("right_channel.wav",-s,m_s_d)
  silences1=get_silence_duration("left_channel.wav",-s1,m_s_d)
  rounded_number = round(silences*1000)
 #print(rounded_number)
  rounded_number1 = round(silences1*1000)
 #print(rounded_number1)
  import threading
  import sys
  try:
   thread1 = threading.Thread(target=lambda: setattr(sys.modules[__name__], 'customer_audio_chunks',function1("left_channel.wav",rounded_number1,th,language)))
   thread2 = threading.Thread(target=lambda: setattr(sys.modules[__name__], 'agent_audio_chunks',function2("right_channel.wav",rounded_number,th,language)))
   thread1.start()
   thread2.start()
   thread1.join()
   thread2.join()
  except FileNotFoundError as f:
     print(f)
     return str(f)
 
  segments=customer_audio_chunks + agent_audio_chunks
  filtered_list = [obj for obj in segments if obj is not None]
  sorted_items = sorted(filtered_list, key=lambda y: (y['start'], y['end']))
 #print(sorted_items)
  elements=[]
  for element in sorted_items:
    print(element["speaker"],":[",element["start"],":",element["end"],"]:",element['content'])
    elements.append({"speaker":element["speaker"],"start":hms_to_str(element["start"][0],element["start"][1],element["start"][2]),"end":hms_to_str(element["end"][0],element["end"][1],element["end"][2]),"content":element['content']})
  os.remove("left_channel.wav")
  os.remove("right_channel.wav")
 
  os.remove("temp_chunk_left.wav")
  os.remove("temp_chunk_right.wav")
  return elements
 except Exception as e :
    d=transcribe("recording.wav",language) 
    return d