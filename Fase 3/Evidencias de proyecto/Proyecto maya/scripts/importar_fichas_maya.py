"""Importador no destructivo de fichas_maya_20.json para MICA Banqueteria Maya.

Modo predeterminado: --plan, solo lectura de PostgreSQL.
--validar: revisa JSON sin conectar a BD.
--aplicar: crea catalogo, recetas, pasos e inventarios con stock 0, en una transaccion.
No modifica fichas, insumos, stock o precios ya existentes.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CENTAVO = Decimal("0.01")


def num(v, campo: str, *, positivo: bool = False) -> Decimal:
    if isinstance(v, bool):
        raise ValueError(f"{campo}: booleano no es un numero valido")
    try:
        x = Decimal(str(v))
    except (TypeError, ValueError, InvalidOperation) as exc:
        raise ValueError(f"{campo}: no es un numero decimal") from exc
    if not x.is_finite() or x < 0 or (positivo and x <= 0):
        raise ValueError(f"{campo}: numero fuera de rango")
    return x


def dinero(x: Decimal) -> Decimal:
    return x.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def clave(nombre: str) -> str:
    return " ".join(nombre.strip().casefold().split())


def validar_json(ruta: Path) -> dict:
    data = json.loads(ruta.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or not isinstance(data.get("insumos"), list) or not isinstance(data.get("fichas"), list):
        raise ValueError("Estructura: requiere listas 'insumos' y 'fichas'")
    if not data["insumos"] or not data["fichas"]:
        raise ValueError("El archivo no puede estar vacio")
    insumos = {}
    for row in data["insumos"]:
        nombre = str(row.get("nombre_insumo", "")).strip()
        unidad = str(row.get("unidad", "")).strip().casefold()
        if not nombre or unidad not in {"kg", "g", "lt", "l", "ml", "unidades", "unidad"}:
            raise ValueError(f"Insumo invalido: {nombre!r}, unidad: {unidad!r}")
        k = clave(nombre)
        if k in insumos:
            raise ValueError(f"Insumo duplicado en JSON: {nombre}")
        num(row.get("costo_unitario"), f"costo del insumo {nombre}", positivo=True)
        insumos[k] = row
    codigos, nombres, nlineas, npasos = set(), set(), 0, 0
    for ficha in data["fichas"]:
        nombre = str(ficha.get("nombre_ficha", "")).strip()
        codigo = str(ficha.get("codigo", "")).strip()
        if not nombre or not codigo or codigo in codigos or clave(nombre) in nombres:
            raise ValueError(f"Nombre/codigo repetido o vacio: {nombre!r} ({codigo})")
        codigos.add(codigo)
        nombres.add(clave(nombre))
        rendimiento = num(ficha.get("rendimiento"), f"rendimiento de {codigo}", positivo=True)
        if str(ficha.get("unidad_rendimiento", "")).casefold() not in {"unidades", "unidad", "porciones", "porción"}:
            raise ValueError(f"Unidad de rendimiento incompatible con MICA en {codigo}")
        if str(ficha.get("estado", "")).casefold() != "activo":
            raise ValueError(f"Ficha no activa: {codigo}")
        receta = ficha.get("receta", [])
        pasos = ficha.get("detalle_preparacion", [])
        if not isinstance(receta, list) or not receta or not isinstance(pasos, list):
            raise ValueError(f"Falta receta o instrucciones en {codigo}")
        vistos, total = set(), Decimal("0")
        for lin in receta:
            k = clave(str(lin.get("insumo", "")))
            if k not in insumos or k in vistos:
                raise ValueError(f"Insumo desconocido o duplicado {k} en {codigo}")
            vistos.add(k)
            maestro = insumos[k]
            if str(lin.get("unidad", "")).casefold() != str(maestro["unidad"]).casefold():
                raise ValueError(f"Unidades distintas para {k} en {codigo}")
            cantidad = num(lin.get("cantidad"), f"cantidad {k} en {codigo}", positivo=True)
            if cantidad.as_tuple().exponent < -3:
                raise ValueError(f"Cantidad con mas de 3 decimales: {k} en {codigo}")
            precio = num(lin.get("costo_unitario"), f"costo {k} en {codigo}", positivo=True)
            if precio != num(maestro["costo_unitario"], "costo catalogo"):
                raise ValueError(f"Precio distinto entre insumo y receta: {k} en {codigo}")
            parcial = num(lin.get("costo_total"), f"subtotal {k} en {codigo}")
            if parcial != dinero(cantidad * precio):
                raise ValueError(f"Costo subtotal incorrecto para {k} en {codigo}")
            total += parcial
            nlineas += 1
        if total != num(ficha.get("costo_total"), f"total {codigo}"):
            raise ValueError(f"Costo total de {codigo} no coincide con suma de ingredientes")
        if dinero(total / rendimiento) != num(ficha.get("costo_insumos_por_porcion"), f"costo porcion {codigo}"):
            raise ValueError(f"Costo por porcion de {codigo} no cuadra")
        numeros = set()
        for paso in pasos:
            orden = int(paso.get("orden", 0))
            if orden <= 0 or orden in numeros or not str(paso.get("instruccion", "")).strip():
                raise ValueError(f"Paso de preparacion invalido en {codigo}")
            numeros.add(orden)
            npasos += 1
    print("JSON VALIDADO: fichas=%d, insumos=%d, lineas_receta=%d, pasos=%d" % (
        len(data["fichas"]), len(data["insumos"]), nlineas, npasos
    ))
    print("AVISO: los precios son referenciales y las recetas NO representan stock disponible.")
    return data


def preparar_bd():
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env", override=True)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
    import django
    django.setup()
    from django.db import connection
    db = connection.settings_dict
    if db.get("ENGINE") != "django.db.backends.postgresql" or db.get("NAME") != "sig_banqueteria_mica":
        raise RuntimeError("OPERACION DETENIDA: se requiere PostgreSQL / sig_banqueteria_mica")
    return db


def mapa_unico(objetos, nombre_campo: str, buscados: set[str], etiqueta: str):
    encontrados = {}
    for item in objetos:
        k = clave(getattr(item, nombre_campo))
        if k in buscados:
            if k in encontrados:
                raise RuntimeError(f"{etiqueta} duplicado en base de datos: {k}. Resolver manualmente antes de importar.")
            encontrados[k] = item
    return encontrados


def ejecutar(data: dict, *, aplicar: bool, nombre_bodega: str):
    from django.db import transaction
    from django.utils import timezone
    from gestion.models import Unidad, Bodega, Insumo, Inventario, FichaTecnica, Receta, DetallePreparacion

    unidades = mapa_unico(Unidad.objects.all(), "nombre_unidad", {"kg", "g", "lt", "l", "ml", "unidades", "unidad", "porciones", "porción"}, "Unidad")
    if "unidades" not in unidades:
        raise RuntimeError("No existe unidad 'unidades' para rendimiento en base de datos")
    bodegas = mapa_unico(Bodega.objects.all(), "nombre_bodega", {clave(nombre_bodega)}, "Bodega")
    bodega = bodegas.get(clave(nombre_bodega))
    if bodega is None:
        raise RuntimeError(f"No se encontro bodega {nombre_bodega!r}")

    buscados = {clave(x["nombre_insumo"]) for x in data["insumos"]}
    existentes = mapa_unico(Insumo.objects.select_related("id_unidad").all(), "nombre_insumo", buscados, "Insumo")
    fichas_nombres = {clave(f["nombre_ficha"]) for f in data["fichas"]}
    fichas_existentes = mapa_unico(FichaTecnica.objects.all(), "nombre_ficha", fichas_nombres, "Ficha")
    precambios = []
    for x in data["insumos"]:
        k = clave(x["nombre_insumo"])
        unidad = str(x["unidad"]).casefold()
        if unidad not in unidades:
            raise RuntimeError(f"Unidad {unidad!r} no existe en PostgreSQL")
        if k in existentes:
            obj = existentes[k]
            if clave(obj.id_unidad.nombre_unidad) != unidad:
                raise RuntimeError(f"UNIDAD INCOMPATIBLE para {x['nombre_insumo']}: BD={obj.id_unidad.nombre_unidad}, JSON={unidad}")
            if Decimal(obj.costo_unitario) != num(x["costo_unitario"], "costo"):
                precambios.append((x["nombre_insumo"], obj.costo_unitario, x["costo_unitario"]))
    for nombre, actual, ref in precambios:
        print(f"ATENCION: {nombre}: BD costo {actual}; JSON {ref}. Se conservara el costo de BD.")

    inventarios_existentes = set(Inventario.objects.filter(id_bodega=bodega).values_list("id_insumo_id", flat=True))
    res = {
        "insumos_nuevos": 0, "insumos_reutilizados": 0, "fichas_nuevas": 0,
        "fichas_omitidas": 0, "recetas_nuevas": 0, "pasos_nuevos": 0,
        "inventarios_nuevos_cero": 0
    }
    for x in data["insumos"]:
        if clave(x["nombre_insumo"]) not in existentes:
            res["insumos_nuevos"] += 1
        else:
            res["insumos_reutilizados"] += 1
    for f in data["fichas"]:
        if clave(f["nombre_ficha"]) in fichas_existentes:
            res["fichas_omitidas"] += 1
        else:
            res["fichas_nuevas"] += 1
            res["recetas_nuevas"] += len(f["receta"])
            res["pasos_nuevos"] += len(f["detalle_preparacion"])
    res["inventarios_nuevos_cero"] = sum(
        1 for x in data["insumos"]
        if (clave(x["nombre_insumo"]) not in existentes or existentes[clave(x["nombre_insumo"])].pk not in inventarios_existentes)
    )
    print("BASE DESTINO: sig_banqueteria_mica | BODEGA:", bodega.nombre_bodega)
    for k, v in res.items():
        print(f"  {k}: {v}")
    print("CODIGOS: 'FT-001' ... son referencias del JSON; se almacenan en la descripcion de cada ficha.")
    if not aplicar:
        print("PLAN COMPLETADO. NO SE MODIFICO NINGUN REGISTRO.")
        return

    with transaction.atomic():
        # No reescribe costos/stock de insumos ya creados.
        for x in data["insumos"]:
            k = clave(x["nombre_insumo"])
            if k not in existentes:
                now = timezone.now()
                existentes[k] = Insumo.objects.create(
                    nombre_insumo=x["nombre_insumo"],
                    descripcion="Insumo importado de fichas_maya_20.json (precio referencial)",
                    categoria=None, id_unidad=unidades[str(x["unidad"]).casefold()],
                    costo_unitario=num(x["costo_unitario"], "precio", positivo=True),
                    stock_minimo=Decimal("0"), codigo_qr=None, id_proveedor=None,
                    estado="activo", created_at=now, updated_at=now,
                )
            insumo = existentes[k]
            if insumo.pk not in inventarios_existentes:
                Inventario.objects.create(
                    id_insumo=insumo, id_bodega=bodega, stock_actual=Decimal("0"),
                    stock_minimo=insumo.stock_minimo, ubicacion=None, estado="activo",
                )
                inventarios_existentes.add(insumo.pk)

        for f in data["fichas"]:
            k = clave(f["nombre_ficha"])
            if k in fichas_existentes:
                print("SIN CAMBIOS ficha existente:", f["nombre_ficha"])
                continue
            texto = "\n".join(f"{int(p['orden'])}. {p['instruccion']}" for p in sorted(f["detalle_preparacion"], key=lambda p: p["orden"]))
            ficha = FichaTecnica.objects.create(
                nombre_ficha=f["nombre_ficha"],
                descripcion=f"[{f['codigo']}] {f.get('descripcion','')}",
                tipo_preparacion=f.get("tipo_preparacion") or None,
                rendimiento=num(f["rendimiento"], "rendimiento", positivo=True),
                id_unidad_rendimiento=unidades["unidades"],
                costo_total=Decimal("0"), precio_sugerido=Decimal("0"),
                margen_objetivo=Decimal("0"), imagen_url=None, estado="activo",
                procedimiento=texto,
            )
            total_actual = Decimal("0")
            for linea in f["receta"]:
                ins = existentes[clave(linea["insumo"])]
                cantidad = num(linea["cantidad"], "cantidad", positivo=True)
                precio = Decimal(ins.costo_unitario)
                subtotal = dinero(cantidad * precio)
                Receta.objects.create(
                    id_ficha_tecnica=ficha, id_insumo=ins, cantidad=cantidad,
                    id_unidad=unidades[str(linea["unidad"]).casefold()],
                    costo_unitario=precio, costo_total=subtotal,
                    observacion="Importado de fichas_maya_20.json; costos segun catalogo en BD",
                )
                total_actual += subtotal
            FichaTecnica.objects.filter(pk=ficha.pk).update(costo_total=dinero(total_actual))
            for paso in f["detalle_preparacion"]:
                DetallePreparacion.objects.create(
                    id_ficha_tecnica=ficha, orden=int(paso["orden"]), instruccion=paso["instruccion"]
                )
    print("IMPORTACION TERMINADA (TRANSACCION CONFIRMADA).")
    print("No se cargaron existencias reales ni se modifico stock de insumos existentes.")


def main():
    parser = argparse.ArgumentParser(description="Carga masiva de fichas e insumos de Banqueteria Maya")
    parser.add_argument("--archivo", default=str(ROOT / "fichas_maya_20.json"), help="Ruta al archivo JSON")
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--validar", action="store_true", help="Solo validar JSON, sin BD")
    modo.add_argument("--aplicar", action="store_true", help="Confirmar altas en PostgreSQL")
    parser.add_argument("--bodega", default="Bodega Central", help="Bodega existente para nuevos inventarios")
    args = parser.parse_args()
    data = validar_json(Path(args.archivo))
    if args.validar:
        print("VALIDACION COMPLETADA; no se requiere acceso a BD.")
        return
    db = preparar_bd()
    print("Motor de base de datos:", db["ENGINE"], "| Nombre:", db["NAME"])
    ejecutar(data, aplicar=args.aplicar, nombre_bodega=args.bodega)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("DETENIDO:", type(exc).__name__, "-", str(exc))
        sys.exit(1)
