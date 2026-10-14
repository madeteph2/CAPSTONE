
from django.urls import path
from . import views

urlpatterns = [
    path(
        "eventos/",
        views.eventos,
        name="eventos",
    ),
    path(
        "eventos/<int:id_evento>/",
        views.evento_detalle,
        name="evento_detalle",
    ),
]
