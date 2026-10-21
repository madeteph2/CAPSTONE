from django.urls import path
from . import views

urlpatterns = [
    path('auth/session/', views.sesion),
    path('auth/login/', views.entrar),
    path('auth/logout/', views.salir),
    path('clientes/', views.clientes),
    path('clientes/<int:id_cliente>/', views.cliente_detalle),
]
