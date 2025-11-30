from django.urls import path
from .views import dashboard_estrategico

urlpatterns = [
    path('estrategico/', dashboard_estrategico, name='dashboard_estrategico'),
]