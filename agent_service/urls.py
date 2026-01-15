# agent_service/urls.py

from django.urls import path
from .views import AgentAnalyzeAPIView,recommendation_form

urlpatterns = [
    path('analyze/', AgentAnalyzeAPIView.as_view(), name='agent-analyze'),
    # Interface Utilisateur
    path('', recommendation_form, name='recommendation-form'),
]