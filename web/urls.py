from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home_public'),
    path('nosotros/', views.nosotros, name='nosotros'),
    path('centros/', views.centros, name='centros_public'),

    path('biblioteca/', views.biblioteca, name='biblioteca'),
]