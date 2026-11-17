from django.urls import path

from .views import (
    PedidoListView,
    PedidoCreateView,
    PedidoDetailUpdateView,
    UsuarioSelectorListView,
    HistorialPedidoListView,
    FichaTecnicaListView,
    FichaTecnicaDetailView,
    UnidadListView,
    InsumoListView,
    RecetaListCreateView,
    RecetaDetailView,
    CotizacionListCreateView,
    CotizacionDetailView,
    InventarioListView,
    MovimientoInventarioListView,
    RegistrarMovimientoInventarioView,
    VentaListView, 
    FacturaListView,
    PagoListView,
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

    path(
        "usuarios/",
        UsuarioSelectorListView.as_view(),
        name="usuarios-selector",
    ),

    path(
        "pedidos/<int:id_pedido>/historial/",
        HistorialPedidoListView.as_view(),
        name="pedidos-historial",
    ),
    
    path(
        "fichas-tecnicas/",
        FichaTecnicaListView.as_view(),
        name="fichas-tecnicas-list",
    ),

    path(
        "fichas-tecnicas/<int:id_ficha_tecnica>/",
        FichaTecnicaDetailView.as_view(),
        name="fichas-tecnicas-detail",
    ),

    path(
    "unidades/",
    UnidadListView.as_view(),
    name="unidades-list",
    ),

    path(
        "insumos/",
        InsumoListView.as_view(),
        name="insumos-list",
    ),

    path(
        "fichas-tecnicas/<int:id_ficha_tecnica>/recetas/",
        RecetaListCreateView.as_view(),
        name="recetas-list-create",
    ),

    path(
        "fichas-tecnicas/<int:id_ficha_tecnica>/recetas/<int:id_receta>/",
        RecetaDetailView.as_view(),
        name="recetas-detail",
    ),

    path(
        "cotizaciones/",
        CotizacionListCreateView.as_view(),
        name="cotizaciones-list-create",
    ),

    path(
        "cotizaciones/<int:id_cotizacion>/",
        CotizacionDetailView.as_view(),
        name="cotizaciones-detail",
    ),

    path(
        "inventario/",
        InventarioListView.as_view(),
        name="inventario-list",
    ),

    path(
        "movimientos-inventario/",
        MovimientoInventarioListView.as_view(),
        name="movimientos-inventario-list",
    ),

    path(
        "movimientos-inventario/registrar/",
        RegistrarMovimientoInventarioView.as_view(),
        name="movimientos-inventario-registrar",
    ),

    # ==========================================
    # W12 - VENTAS / FACTURACIÓN
    # ==========================================

    path(
        "ventas/",
        VentaListView.as_view(),
        name="ventas-list",
    ),

    path(
        "facturas/",
        FacturaListView.as_view(),
        name="facturas-list",
    ),

    path(
        "pagos/",
        PagoListView.as_view(),
        name="pagos-list",
    ),

]