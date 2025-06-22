import os
from pathlib import Path
import requests
import json
from django.conf import settings

def text_to_speech(input_file_path, output_dir="audio_outputs"):
    """
    Convert text from a file to speech using ElevenLabs Text to Speech API
    
    Args:
        input_file_path (str): Path to the input text file
        output_dir (str): Directory to store the audio output
    """
    # Check if API key is set
    api_key = settings.ELEVENLABS_API_KEY
    if not api_key:
        raise ValueError("Please set ELEVENLABS_API_KEY in Django settings")
    
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Read the input text file
    try:
        with open(input_file_path, 'r', encoding='utf-8') as file:
            text_content = file.read().strip()
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file not found: {input_file_path}")
    
    if not text_content:
        raise ValueError("Input file is empty")
    
    # ElevenLabs Text to Speech API endpoint
    url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"  # Default voice ID
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    data = {
        "text": text_content,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    # Make the API request
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")
    
    # Create output filename based on input filename
    input_filename = Path(input_file_path).stem
    output_file = output_path / f"{input_filename}_audio.mp3"
    
    # Save the audio file
    with open(output_file, 'wb') as f:
        f.write(response.content)
    
    return str(output_file)

if __name__ == "__main__":
    # Example usage
    input_file = "/Users/jianyuhou/Downloads/video_description.txt"
    try:
        output_file = text_to_speech(input_file)
        print(f"Audio file generated successfully: {output_file}")
    except Exception as e:
        print(f"Error: {str(e)}")
