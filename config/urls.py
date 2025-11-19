from django.contrib import admin
from django.urls import path
from gestion.views import dashboard # Importa tu vista

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'), # Ruta raíz apunta al dashboard
]