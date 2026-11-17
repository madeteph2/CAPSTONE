"""Carga masiva auditada de entradas REALES de stock en inventario MICA.

Lee CSV delimitado por ; con columnas: nombre_insumo,bodega,cantidad_entrada,observacion
No modifica inventario en modo predeterminado --plan.
--aplicar requiere --lote unico para evitar repetir una misma importacion.
Nunca utiliza cantidades de receta como stock fisico.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def clave(txt: str) -> str:
    return " ".join(txt.strip().casefold().split())


def leer_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        campos = {"nombre_insumo", "bodega", "cantidad_entrada", "observacion"}
        if reader.fieldnames is None or set(reader.fieldnames) != campos:
            raise ValueError("CSV requiere columnas exactas: nombre_insumo;bodega;cantidad_entrada;observacion")
        filas, vistas = [], set()
        for i, linea in enumerate(reader, start=2):
            campo = (linea.get("cantidad_entrada") or "").strip()
            if not campo:
                continue  # No inventar cantidades de stock.
            if "," in campo:
                raise ValueError(f"Fila {i}: usa punto decimal y no separador de miles")
            try:
                valor = Decimal(campo)
            except InvalidOperation as exc:
                raise ValueError(f"Fila {i}: cantidad invalida") from exc
            if not valor.is_finite() or valor <= 0 or -valor.as_tuple().exponent > 3:
                raise ValueError(f"Fila {i}: cantidad debe ser positiva y con maximo 3 decimales")
            nombre = str(linea["nombre_insumo"] or "").strip()
            bodega = str(linea["bodega"] or "").strip()
            if not nombre or not bodega:
                raise ValueError(f"Fila {i}: nombre o bodega vacios")
            k = (clave(nombre), clave(bodega))
            if k in vistas:
                raise ValueError(f"Fila {i}: un insumo/bodega aparece mas de una vez")
            vistas.add(k)
            filas.append((nombre, bodega, valor, str(linea.get("observacion") or "").strip()))
    return filas


def iniciar_django():
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env", override=True)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
    import django
    django.setup()
    from django.db import connection
    if connection.settings_dict.get("ENGINE") != "django.db.backends.postgresql" or connection.settings_dict.get("NAME") != "sig_banqueteria_mica":
        raise RuntimeError("DETENIDO: solo PostgreSQL sig_banqueteria_mica")


def cargar(filas, *, aplicar: bool, lote: str | None):
    from django.db import transaction
    from django.utils import timezone
    from gestion.models import Insumo, Bodega, Inventario, MovimientoInventario

    nombres = {clave(nombre) for nombre, _, _, _ in filas}
    lugares = {clave(bod) for _, bod, _, _ in filas}
    ins = {}
    for x in Insumo.objects.all():
        k = clave(x.nombre_insumo)
        if k in nombres:
            if k in ins:
                raise RuntimeError(f"Insumos duplicados en BD: {k}")
            ins[k] = x
    bod = {}
    for x in Bodega.objects.all():
        k = clave(x.nombre_bodega)
        if k in lugares:
            if k in bod:
                raise RuntimeError(f"Bodegas duplicadas en BD: {k}")
            bod[k] = x
    acciones = []
    for nombre, bodega, cantidad, comentario in filas:
        i = ins.get(clave(nombre))
        b = bod.get(clave(bodega))
        if not i or not b:
            raise RuntimeError(f"Falta insumo o bodega: {nombre} / {bodega}; importa catalogo primero")
        inv = Inventario.objects.filter(id_insumo=i, id_bodega=b).first()
        if inv is None:
            raise RuntimeError(f"Falta inventario para {nombre} en {bodega}; importa catalogo primero")
        acciones.append((i, b, cantidad, comentario, inv.pk))

    if not acciones:
        print("No hay cantidades ingresadas en CSV. Stock sin cambios.")
        return
    print("ENTRADAS A REGISTRAR:", len(acciones))
    for i, b, cantidad, _, pk in acciones:
        current = Inventario.objects.get(pk=pk).stock_actual
        print(f"  {i.nombre_insumo} | {b.nombre_bodega}: {current} + {cantidad} = {current + cantidad} {i.id_unidad.nombre_unidad}")
    if not aplicar:
        print("PLAN COMPLETADO. NO SE MODIFICO INVENTARIO.")
        return
    if not lote or not re.fullmatch(r"[A-Za-z0-9_-]{3,50}", lote):
        raise ValueError("Para aplicar debes indicar --lote con 3 a 50 letras, numeros, guiones o subrayados")
    marca = f"CARGA_MASIVA_MICA:{lote}:"
    with transaction.atomic():
        # Un lote previamente registrado nunca se vuelve a procesar.
        if MovimientoInventario.objects.filter(observacion__startswith=marca).exists():
            raise RuntimeError(f"Lote ya registrado: {lote}. Para una compra NUEVA usa otro lote.")
        for i, b, cantidad, comentario, pk in acciones:
            inv = Inventario.objects.select_for_update().get(pk=pk)
            inv.stock_actual += cantidad
            inv.save(update_fields=["stock_actual"])
            MovimientoInventario.objects.create(
                tipo_movimiento="entrada", fecha_movimiento=timezone.now(),
                cantidad=cantidad, costo_unitario=i.costo_unitario,
                observacion=f"{marca}{i.pk}:{b.pk} | {comentario or 'Entrada verificada por el operador'}",
                id_insumo=i, id_bodega=b, id_pedido=None, id_usuario=None,
            )
    print("ENTRADAS CONFIRMADAS Y REGISTRADAS EN HISTORIAL: lote", lote)


def main():
    parser = argparse.ArgumentParser(description="Entradas masivas verificadas de inventario")
    parser.add_argument("--csv", default=str(ROOT / "plantilla_carga_stock.csv"))
    parser.add_argument("--aplicar", action="store_true", help="Registrar entradas de stock")
    parser.add_argument("--lote", help="Identificador unico de esta carga (obligatorio con --aplicar)")
    args = parser.parse_args()
    filas = leer_csv(Path(args.csv))
    iniciar_django()
    cargar(filas, aplicar=args.aplicar, lote=args.lote)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("DETENIDO:", type(exc).__name__, "-", str(exc))
        sys.exit(1)
