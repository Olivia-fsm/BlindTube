from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'descriptions', views.AudioDescriptionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('process-video/', views.process_video, name='process-video'),
    path('process-youtube/', views.process_youtube, name='process-youtube'),
    path('audio/<str:filename>', views.get_audio, name='get-audio'),
    path('generate-audio/', views.generate_audio, name='generate-audio'),
    path('generate-audio-eleven/', views.generate_audio_eleven, name='generate-audio-eleven'),
] 