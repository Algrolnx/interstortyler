from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('story/new/', views.create_story, name='create_story'),
    path('story/<int:pk>/', views.story_detail, name='story_detail'),
    path('story/<int:pk>/continue/', views.continue_story, name='continue_story'),
    path('story/<int:pk>/finish/', views.finish_story, name='finish_story')
]