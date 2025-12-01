from django.urls import path
from .views import dashboard_estrategico, dashboard_nacional

urlpatterns = [
    path('estrategico/', dashboard_estrategico, name='dashboard_estrategico'),
    path('nacional/', dashboard_nacional, name='dashboard_nacional'),
]