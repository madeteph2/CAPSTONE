from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated, DjangoModelPermissions

from .models import Cliente, Pedido
from .serializers import ClienteSerializer, PedidoSerializer, PedidoWriteSerializer


class ClienteListView(generics.ListAPIView):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [AllowAny]


class PedidoListView(generics.ListAPIView):
    queryset = Pedido.objects.select_related(
        "id_cliente",
        "id_evento",
        "id_estado_pedido",
        "id_usuario_responsable",
    ).all()

    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]


class PedidoCreateView(generics.CreateAPIView):
    queryset = Pedido.objects.all()
    serializer_class = PedidoWriteSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]


class PedidoDetailUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Pedido.objects.all()
    serializer_class = PedidoWriteSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    lookup_field = "id_pedido"