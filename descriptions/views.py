"""
pip install opencv-python google-generativeai
python manage.py runserver
"""

from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from .models import AudioDescription
from .serializers import AudioDescriptionSerializer
from django.http import JsonResponse, FileResponse
import os
from pathlib import Path
import tempfile
from video_processing import VideoProcessor
from django.conf import settings
import uuid
import mimetypes
import logging
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create your views here.

class AudioDescriptionViewSet(viewsets.ModelViewSet):
    queryset = AudioDescription.objects.all()
    serializer_class = AudioDescriptionSerializer

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=False, methods=['get'])
    def user_descriptions(self, request):
        user_id = request.query_params.get('user_id', None)
        if user_id:
            descriptions = AudioDescription.objects.filter(user_id=user_id)
            serializer = self.get_serializer(descriptions, many=True)
            return Response(serializer.data)
        return Response({'error': 'user_id parameter is required'}, status=400)

def is_valid_video_file(file):
    """Check if the file is a valid video file."""
    valid_types = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo']
    file_type = mimetypes.guess_type(file.name)[0]
    logger.debug(f"File type detected: {file_type}")
    return file_type in valid_types

def save_uploaded_file(file, directory='videos'):
    """Save an uploaded file to a permanent location."""
    start_time = time.time()
    logger.debug(f"Starting file upload: {file.name}")
    
    # Create directory if it doesn't exist
    upload_dir = os.path.join(settings.MEDIA_ROOT, directory)
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    ext = os.path.splitext(file.name)[1]
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(upload_dir, filename)
    
    # Save file
    file_size = 0
    with open(filepath, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
            file_size += len(chunk)
    
    duration = time.time() - start_time
    logger.debug(f"File saved: {filepath}")
    logger.debug(f"Upload completed in {duration:.2f} seconds")
    logger.debug(f"File size: {file_size / (1024*1024):.2f} MB")
    
    return filepath

@api_view(['POST'])
def process_video(request):
    """
    Process a video file to generate description.
    Expects a video file in the request.
    """
    processing_start = time.time()
    logger.debug("Starting video processing request")
    
    if 'video' not in request.FILES:
        logger.error("No video file provided in request")
        return Response({
            'error': 'No video file provided',
            'status': 'error',
            'stage': 'validation'
        }, status=status.HTTP_400_BAD_REQUEST)

    video_file = request.FILES['video']
    logger.debug(f"Received video file: {video_file.name} (size: {video_file.size / (1024*1024):.2f} MB)")
    
    # Validate video file
    if not is_valid_video_file(video_file):
        logger.error(f"Invalid video format: {video_file.name}")
        return Response({
            'error': 'Invalid video file format. Please upload MP4, AVI, MOV, or similar video files.',
            'status': 'error',
            'stage': 'validation'
        }, status=status.HTTP_400_BAD_REQUEST)

    processing_status = {
        'status': 'processing',
        'stage': 'upload',
        'progress': 0,
        'start_time': processing_start
    }
    
    try:
        # Save video file permanently
        logger.debug("Saving video file")
        video_path = save_uploaded_file(video_file)
        processing_status['stage'] = 'video_saved'
        processing_status['progress'] = 20
        logger.debug(f"Video saved to: {video_path}")
        
        # Initialize video processor with API key from settings
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            logger.error("Google API key not found in settings")
            return Response({
                'error': 'Google API key not configured',
                'status': 'error',
                'stage': 'api_initialization'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        logger.debug("Initializing video processor")
        processor = VideoProcessor(api_key=api_key)
        processing_status['stage'] = 'extracting_frames'
        processing_status['progress'] = 30

        # Extract frames and generate description
        logger.debug("Extracting frames from video")
        frames = processor.extract_frames(video_path, frame_interval=10)
        if not frames:
            logger.error("Failed to extract frames from video")
            return Response({
                'error': 'Failed to extract frames from video',
                'status': 'error',
                'stage': 'frame_extraction'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.debug(f"Extracted {len(frames)} frames")
        processing_status['stage'] = 'generating_description'
        processing_status['progress'] = 50

        logger.debug("Generating description using Gemini")
        description_text = processor.generate_description(frames)
        if not description_text:
            logger.error("Failed to generate description")
            return Response({
                'error': 'Failed to generate description',
                'status': 'error',
                'stage': 'description_generation'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        logger.debug(f"Generated description (length: {len(description_text)} chars)")
        processing_status['stage'] = 'saving_to_database'
        processing_status['progress'] = 90

        # Store the description in the database
        logger.debug("Saving description to database")
        description = AudioDescription.objects.create(
            input_text=video_file.name,
            input_type='video',
            description_text=description_text,
            description_length='medium',  # Default to medium length
            user_id=request.data.get('user_id', 'anonymous')
        )
        logger.debug(f"Description saved with ID: {description.id}")

        processing_duration = time.time() - processing_start
        logger.debug(f"Video processing completed in {processing_duration:.2f} seconds")

        return Response({
            'status': 'success',
            'description': description_text,
            'description_id': description.id,
            'video_path': os.path.relpath(video_path, settings.MEDIA_ROOT),
            'processing_time': processing_duration,
            'frames_processed': len(frames),
            'description_length': len(description_text),
            'stages_completed': [
                'upload',
                'frame_extraction',
                'description_generation',
                'database_storage'
            ]
        })

    except Exception as e:
        logger.error(f"Error during video processing: {str(e)}", exc_info=True)
        return Response({
            'error': f'Error processing video: {str(e)}',
            'status': 'error',
            'stage': processing_status['stage'],
            'progress': processing_status['progress'],
            'processing_time': time.time() - processing_start
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def process_youtube(request):
    """
    Process a YouTube URL to generate description.
    Expects a YouTube URL in the request body.
    """
    youtube_url = request.data.get('youtube_url')
    if not youtube_url:
        return Response({'error': 'No YouTube URL provided'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # TODO: Add YouTube video download functionality
        # For now, return an error
        return Response({'error': 'YouTube processing not implemented yet'}, 
                       status=status.HTTP_501_NOT_IMPLEMENTED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_audio(request, filename):
    """
    Serve the generated audio file.
    """
    audio_path = os.path.join('audio_outputs', filename)
    if os.path.exists(audio_path):
        return FileResponse(open(audio_path, 'rb'), content_type='audio/mpeg')
    return Response({'error': 'Audio file not found'}, status=status.HTTP_404_NOT_FOUND)
