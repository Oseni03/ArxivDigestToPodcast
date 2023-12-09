#!/usr/bin/env python3
# source: https://github.com/unconv/ai-podcaster

from elevenlabs import generate, set_api_key, save, RateLimitError
import subprocess
import random
import openai
import time
import json
import sys
import os

openai.api_key = os.getenv("OPENAI_API_KEY")
elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")

if elevenlabs_key:
    set_api_key(elevenlabs_key)

print("## AI-Podcaster by Unconventional Coding ##\n")


if not os.path.exists("dialogs"):
    os.mkdir("dialogs")

if not os.path.exists("podcasts"):
    os.mkdir("podcasts")

voice_names = {
    "male": [
        "Adam",
        "Antoni",
        "Arnold",
        "Callum",
        "Charlie",
        "Clyde",
        "Daniel",
        "Ethan",
    ],
    "female": [
        "Bella",
        "Charlotte",
        "Domi",
        "Dorothy",
        "Elli",
        "Emily",
        "Gigi",
        "Grace",
    ]
}

voices = {}

def get_voice(name, gender):
    if name not in voices:
        voices[name] = random.choice(voice_names[gender])
        voice_names[gender].remove(voices[name])
    return voices[name]


podcast_duration = "15 minutes"

system_prompt = f"""
You are about to create a podcast script discussing the insights derived from a research paper provided by the user. Your goal is to generate a conversational podcast script between two presenters—Adam and Ethan—based on the content of the user-provided research paper. The podcast aims to deliver engaging content while maintaining a professional and informative tone.

Objective: Discuss the key findings and implications from the ruser-provided research paper. The script should provide an overview of the paper's significance and its impact on the field.

Podcast Duration: {podcast_duration}

Tone: Maintain a conversational yet authoritative tone. Adam and Ethan should engage the audience by discussing the paper's content with enthusiasm and expertise.

Key Sections to Cover:

    Introduction (Adam):
        Welcoming the audience and introducing the research paper.
        Providing context on the significance of the paper's topic.
    Summary of Research Paper (Ethan):
        Briefly summarizing the key points and main findings from the paper.
        Explaining the methodology used in the research.
    Analysis and Discussion (Adam and Ethan):
        Delving deeper into the implications of the research findings.
        Exchanging thoughts, opinions, and potential applications arising from the paper.
    Conclusion (Adam and Ethan):
        Summarize the key takeaways from the research paper.
        Discuss potential future implications, applications, or areas for further research based on the paper's findings.
    Audience Engagement (Adam and Ethan):
        Encouraging listeners to explore the paper for further details.
        Also, engage the user by encouraging their participation in the podcast discussion.
        Opening the floor for questions or comments from the audience.

Additional Notes:
    Use a blend of technical language and layman terms to make the content accessible to a wide audience.
    Keep the discussion engaging and avoid jargon overload.
    Ensure that each section flows naturally into the next, maintaining a coherent narrative throughout the script.

Important: Please use the retrieved content from the research paper to generate the dialogues between Adam and Ethan. Provide informative discussions while capturing the essence of the paper's content in a conversational manner.
"""


def generate_dialog(paper_content, podcast_id):
    transcript_file_name = f"podcasts/podcast{podcast_id}.txt"
    transcript_file = open(transcript_file_name, "w")

    dialogs = []

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": paper_content,
        }
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        functions=[
            {
                "name": "add_dialog",
                "description": "Add dialog to the podcast",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "speaker": {
                            "type": "string",
                            "description": "The name of the speaker"
                        },
                        "gender": {
                            "type": "string",
                            "description": "The gender of the speaker (male or female)"
                        },
                        "content": {
                            "type": "string",
                            "description": "The content of the speech"
                        }
                    },
                    "required": ["speaker", "gender", "content"]
                }
            }
        ],
        function_call={
            "name": "add_dialog",
            "arguments": ["speaker", "gender", "content"]
        }
    )

    message = response["choices"][0]["message"] # type: ignore

    messages.append(message)

    function_call = message["function_call"]
    arguments = json.loads(function_call["arguments"])

    transcript_file.write(arguments['speaker'] + ": " + arguments['content'] + "\n")

    dialogs.append(arguments)

    transcript_file.close()
    return (dialogs, transcript_file_name)


def generate_podcast(paper_content, podcast_id=f"{time.time()}"):
    dialog_files = []
    concat_file = open("concat.txt", "w")

    print("Generating transcript")

    dialogs, transcript_file_name = generate_dialog(paper_content, podcast_id)

    print("Generating audio")
    try:
        for i, dialog in enumerate(dialogs):
            audio = generate(
                text=dialog["content"],
                voice=get_voice(dialog["speaker"], dialog["gender"].lower()),
                model="eleven_monolingual_v1"
            )

            filename = f"dialogs/dialog{i}.wav"
            concat_file.write("file " + filename + "\n")
            dialog_files.append(filename)

            save(audio, filename) # type: ignore
    except RateLimitError:
        print("ERROR: ElevenLabs ratelimit exceeded!")

    concat_file.close()

    podcast_file_name = f"podcasts/podcast{podcast_id}.wav"

    print("Concatenating audio")
    subprocess.run(f"ffmpeg -f concat -safe 0 -i concat.txt -c copy {podcast_file_name}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    os.unlink("concat.txt")

    for file in dialog_files:
        os.unlink(file)
    return podcast_file_name, transcript_file_name


if __name__ == "__main__":
    with open("", "r") as file:
        paper_content = file.read()
    podcast_file_name, transcript_file_name = generate_podcast(paper_content)
    print("\n## Podcast is ready! ##")
    print("Audio: " + podcast_file_name)
    print("Transcript: " + transcript_file_name)
