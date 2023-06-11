#Importing the libraries
import secret
import openai
import requests
from time import sleep
import os
import wave
import pygame


#Setting up the API keys
uberduck_auth = secret.uberduck_auth
openai.api_key = secret.token

#Setting up the voice models from uberduck
Spongebob = "2231cbd3-15a5-4571-9299-b58f36062c45"
Patrick = "3b2755d1-11e2-4112-b75b-01c47560fb9c"

#Setup of Chatgpt
def chat_gen(script, content):
    reply = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "system", "content": script},
            {"role": "user", "content": content},
        ]
    )
    return reply['choices'][0]['message']['content'] # type: ignore

script = """
    You are to create scripts. 
    You will be giving the topic and who to act like. 
    Make sure you are in character.
    You are the act like the person you are given. 
    You dont need actions just what they say.
    Dont do any actions.
    Make sure the script is over 10 lines long, but under 15.
    Format is: person: "what they say" 
    Keep everything dumb and stupid.
"""

#Setup of the Voice Generator
def gen_voice(text, voice, pos):
    audio_uuid = requests.post(
        "https://api.uberduck.ai/speak",
        json=dict(speech=text, voicemodel_uuid=voice),
        auth=uberduck_auth,
    ).json()["uuid"]
    for t in range(50):
        sleep(1) # check status every second for 10 seconds.
        output = requests.get(
            "https://api.uberduck.ai/speak-status",
            params=dict(uuid=audio_uuid),
            auth=uberduck_auth,
        ).json()
        if output['path'] != None:
            r = requests.get(output["path"], allow_redirects=True)
            file_path = f"speech{pos}.wav"
            with open(file_path, "wb") as f:
                f.write(r.content)
            return

#Merge the audio files     
def merge_wav_files(file_list, output_filename):
    # Open first valid file and get details
    params = None
    for filename in file_list:
        try:
            with wave.open(filename, 'rb') as wave_file:
                params = wave_file.getparams()
                break
        except wave.Error:
            continue

    if params is None:
        print("No valid input files.")
        return

    # Open output file with same details
    with wave.open(output_filename, 'wb') as output_wav:
        output_wav.setparams(params)

        # Go through input files and add each to output file
        for filename in file_list:
            try:
                with wave.open(filename, 'rb') as wave_file:
                    output_wav.writeframes(wave_file.readframes(wave_file.getnframes()))
            except wave.Error:
                print(f"Skipping invalid file: {filename}")

#Cleanup
for filename in os.listdir(os.getcwd()):
    if filename.startswith("speech"):
        os.remove(filename)
    if filename.startswith("output"):
        os.remove(filename)

#Main

def generete(prompt):
    #Grabs the responce from the chatgpt
    responce = chat_gen(script,prompt)
    responce = responce.replace("\n\n","\n")

    print(responce)

    #Splits the responce into lines
    lines = responce.split("\n")

    #Goes through each line and checks if it is spongebob or patrick and then generates the audio file
    x = 0
    for line in lines:
        x += 1
        if line.startswith("Spongebob:"):
            gen_voice(line[11:],Spongebob,x)
        elif line.startswith("Patrick:"):
            gen_voice(line[8:],Patrick,x)
        else:
            print("Error: Line does not start with Spongebob or Patrick")

    #Merges the audio files
    merge_wav_files([f"speech{i}.wav" for i in range(1, x + 1)], "output.wav")

    #Cleans up the audio files
    for filename in os.listdir(os.getcwd()):
        if filename.startswith("speech"):
            os.remove(filename)

    # Plays the audio file
    pygame.mixer.init()
    pygame.mixer.music.load("output.wav")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy() == True:
        continue
    return

#generete('Spongebob, Patrick, Talking about how they commited 9/11')