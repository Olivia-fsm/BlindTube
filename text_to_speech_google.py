import os
from pathlib import Path
from gtts import gTTS

def text_to_speech(input_file_path, output_dir="audio_outputs"):
    """
    Convert text from a file to speech using Google Text-to-Speech (gTTS)
    
    Args:
        input_file_path (str): Path to the input text file
        output_dir (str): Directory to store the audio output
    """
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
    
    # Create gTTS object
    tts = gTTS(text=text_content, lang='en', slow=False)
    
    # Create output filename based on input filename
    input_filename = Path(input_file_path).stem
    output_file = output_path / f"{input_filename}_audio.mp3"
    
    # Save the audio file
    tts.save(str(output_file))
    
    return str(output_file)

if __name__ == "__main__":
    # Example usage
    input_file = "/Users/jianyuhou/Downloads/video_description.txt"
    try:
        output_file = text_to_speech(input_file)
        print(f"Audio file generated successfully: {output_file}")
    except Exception as e:
        print(f"Error: {str(e)}") 