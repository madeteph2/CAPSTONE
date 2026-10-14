from django.urls import path

from .views import (
    PedidoListView,
    PedidoCreateView,
    PedidoDetailUpdateView,
)

urlpatterns = [
    path(
        "pedidos/",
        PedidoListView.as_view(),
        name="pedidos-list",
    ),

    path(
        "pedidos/nuevo/",
        PedidoCreateView.as_view(),
        name="pedidos-create",
    ),

    path(
        "pedidos/<int:id_pedido>/",
        PedidoDetailUpdateView.as_view(),
        name="pedidos-detail-update",
    ),
]