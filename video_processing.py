import cv2
import base64
import os
from typing import List, Optional
import time
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import sys

class VideoProcessor:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the VideoProcessor with Gemini client."""
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
    def extract_frames(self, video_path: str, frame_interval: int = 25) -> List[str]:
        """
        Extract frames from a video file and convert them to base64.
        
        Args:
            video_path: Path to the video file
            frame_interval: Interval between frames to extract (default: 25)
            
        Returns:
            List of base64 encoded frames
        """
        video = cv2.VideoCapture(video_path)
        base64_frames = []
        frame_count = 0
        
        while video.isOpened():
            success, frame = video.read()
            if not success:
                break
                
            # Only keep frames at the specified interval
            if frame_count % frame_interval == 0:
                _, buffer = cv2.imencode(".jpg", frame)
                base64_frames.append(base64.b64encode(buffer).decode("utf-8"))
            
            frame_count += 1
            
        video.release()
        return base64_frames
    
    def generate_description(self, frames: List[str]) -> str:
        """
        Generate a description of the video using Gemini Vision.
        
        Args:
            frames: List of base64 encoded frames
            
        Returns:
            Generated description text
        """
        # Convert base64 frames to image parts
        image_parts = []
        for frame in frames:
            image_parts.append({
                "mime_type": "image/jpeg",
                "data": frame
            })
        
        # Create the prompt
        prompt = "Generate a compelling description that I can upload along with this video. Focus on the characters, their actions, and the overall story being told."
        
        # Generate content using Gemini
        response = self.model.generate_content(
            contents=[prompt] + image_parts,
            generation_config={
                "temperature": 0.4,
                "top_p": 1,
                "top_k": 32,
                "max_output_tokens": 500,
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
        )
        
        return response.text
    
    def analyze_scene(self, frames: List[str]) -> str:
        """
        Analyze the scene details and action sequences in the video.
        
        Args:
            frames: List of base64 encoded frames
            
        Returns:
            Scene analysis text
        """
        image_parts = []
        for frame in frames:
            image_parts.append({
                "mime_type": "image/jpeg",
                "data": frame
            })
        
        prompt = """Analyze this scene from Tom and Jerry. Please describe:
        1. What are the characters doing?
        2. What is the setting?
        3. Any notable gags or comedic moments?
        4. The overall mood of the scene"""
        
        response = self.model.generate_content(
            contents=[prompt] + image_parts,
            generation_config={
                "temperature": 0.7,
                "top_p": 1,
                "top_k": 32,
                "max_output_tokens": 500,
            }
        )
        
        return response.text

def main():
    """Example usage of the VideoProcessor class."""
    if len(sys.argv) != 2:
        print("Usage: python video_processing.py <video_path>")
        sys.exit(1)
        
    video_path = sys.argv[1]
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        sys.exit(1)
        
    # Initialize the processor
    processor = VideoProcessor()
    
    # Extract frames
    print("Extracting frames...")
    frames = processor.extract_frames(video_path)
    print(f"Extracted {len(frames)} frames")
    
    # Generate description
    print("\nGenerating description...")
    description = processor.generate_description(frames)
    print("\nDescription:")
    print(description)
    
    # Analyze scene
    print("\nAnalyzing scene...")
    analysis = processor.analyze_scene(frames)
    print("\nScene Analysis:")
    print(analysis)
    
    # Save the results to a text file
    output_dir = os.path.dirname(video_path)
    output_path = os.path.join(output_dir, "video_analysis.txt")
    with open(output_path, "w") as f:
        f.write("Video Description:\n")
        f.write("================\n")
        f.write(description)
        f.write("\n\nScene Analysis:\n")
        f.write("================\n")
        f.write(analysis)
    print(f"\nAnalysis saved to {output_path}")

if __name__ == "__main__":
    main()
