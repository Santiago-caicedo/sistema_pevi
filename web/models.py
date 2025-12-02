from django.db import models
from gestion.models import Usuario

class Noticia(models.Model):
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    imagen_portada = models.ImageField(upload_to='noticias/')
    resumen = models.TextField(max_length=500)
    contenido = models.TextField() # Aquí podrías usar un editor rico después
    autor = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    publicada = models.BooleanField(default=True)

    def __str__(self):
        return self.titulo