"""MICA v2.5B1: taxonomía comercial sin alterar fichas históricas.

Los paquetes de múltiples fichas se diseñarán aparte; esta versión agrupa
preparaciones individuales y restringe la simulación por tipo en el servidor.
"""

TIPOS_POR_GRUPO = {
    'salados': ('plato_fondo', 'entrada', 'acompanamiento', 'canape', 'bocado_salado'),
    'dulces': ('postre', 'bocado_dulce', 'reposteria'),
    'bebidas_frias': ('bebida_fria',),
    'bebidas_calientes': ('bebida_caliente',),
}
ETIQUETAS_GRUPO = {
    'salados': 'Salados', 'dulces': 'Dulces',
    'bebidas_frias': 'Bebidas frías', 'bebidas_calientes': 'Bebidas calientes',
}
ETIQUETAS_TIPO = {
    'plato_fondo': 'Plato principal', 'entrada': 'Entrada',
    'acompanamiento': 'Acompañamiento', 'canape': 'Canapés',
    'bocado_salado': 'Bocados salados', 'postre': 'Postre',
    'bocado_dulce': 'Bocados dulces', 'reposteria': 'Repostería',
    'bebida_fria': 'Bebidas frías', 'bebida_caliente': 'Bebidas calientes',
}
TODOS_TIPOS = tuple(ETIQUETAS_TIPO)


def grupo_de(tipo):
    """Retorna el grupo de un código normalizado o None si se desconoce."""
    for grupo, tipos in TIPOS_POR_GRUPO.items():
        if tipo in tipos:
            return grupo
    return None


def filtros_compatibles(grupo='', tipo=''):
    """Validación común para no comparar categorías incompatibles."""
    if grupo and grupo not in TIPOS_POR_GRUPO:
        return False
    if tipo and tipo not in ETIQUETAS_TIPO:
        return False
    return not (grupo and tipo and tipo not in TIPOS_POR_GRUPO[grupo])
