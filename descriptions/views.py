from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import AudioDescription
from .serializers import AudioDescriptionSerializer

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
