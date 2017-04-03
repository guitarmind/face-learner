###
# Modifed by Mark Peng, based on Microsoft TTS example
#
#Copyright (c) Microsoft Corporation
#All rights reserved. 
#MIT License
#Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the ""Software""), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
###

import httplib, urlparse, json
from xml.etree import ElementTree

import argparse
import pyaudio
import wave
import StringIO

parser = argparse.ArgumentParser()
parser.add_argument('--text', type=str, default="Welcome back to office!",
                    help='input text')
parser.add_argument('--key', type=str, default="tts.key",
                    help='Bing Speech API key file path')
args = parser.parse_args()

def text_to_speech(text):
  #Note: The way to get api key:
  #Free: https://www.microsoft.com/cognitive-services/en-us/subscriptions?productId=/products/Bing.Speech.Preview
  #Paid: https://portal.azure.com/#create/Microsoft.CognitiveServices/apitype/Bing.Speech/pricingtier/S0
  apiKey = None
  with open(args.key, "rb") as f:
    apiKey = f.readlines()[0]

  params = ""
  headers = {"Ocp-Apim-Subscription-Key": apiKey}

  #AccessTokenUri = "https://api.cognitive.microsoft.com/sts/v1.0/issueToken";
  AccessTokenHost = "api.cognitive.microsoft.com"
  path = "/sts/v1.0/issueToken"

  # Connect to server to get the Access Token
  conn = httplib.HTTPSConnection(AccessTokenHost)
  conn.request("POST", path, params, headers)
  response = conn.getresponse()
  # print(response.status, response.reason)

  data = response.read()
  conn.close()

  accesstoken = data.decode("UTF-8")

  body = ElementTree.Element('speak', version='1.0')
  body.set('{http://www.w3.org/XML/1998/namespace}lang', 'en-us')
  voice = ElementTree.SubElement(body, 'voice')
  voice.set('{http://www.w3.org/XML/1998/namespace}lang', 'en-US')
  voice.set('{http://www.w3.org/XML/1998/namespace}gender', 'Female')
  voice.set('name', 'Microsoft Server Speech Text to Speech Voice (en-US, ZiraRUS)')
  voice.text = text

  headers = {"Content-type": "application/ssml+xml", 
        "X-Microsoft-OutputFormat": "riff-16khz-16bit-mono-pcm", 
        "Authorization": "Bearer " + accesstoken, 
        "X-Search-AppId": "07D3234E49CE426DAA29772419F436CA", 
        "X-Search-ClientID": "1ECFAE91408841A480F00935DC390960", 
        "User-Agent": "TTSForPython"}
        
  #Connect to server to synthesize the wave
  conn = httplib.HTTPSConnection("speech.platform.bing.com")
  conn.request("POST", "/synthesize", ElementTree.tostring(body), headers)
  response = conn.getresponse()
  # print(response.status, response.reason)

  data = response.read()
  conn.close()

  play_wav_bytes(data)

def play_wav_bytes(data):
  buffer = StringIO.StringIO(data)
  chunk = 1024
  wf = wave.open(buffer, 'rb')
  p = pyaudio.PyAudio()
  stream = p.open(
      format = p.get_format_from_width(wf.getsampwidth()),
      channels = wf.getnchannels(),
      rate = wf.getframerate(),
      output = True)
  data = wf.readframes(chunk)
  while data != '':
      stream.write(data)
      data = wf.readframes(chunk)
  stream.close()
  p.terminate()

if __name__ == '__main__':
    text_to_speech(args.text)

