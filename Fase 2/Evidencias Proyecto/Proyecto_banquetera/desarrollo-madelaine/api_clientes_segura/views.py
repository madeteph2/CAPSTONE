"""API W04. SQL parametrizado sobre la tabla cliente ya existente. Sin migraciones."""
import json
import re
from datetime import datetime
from django.contrib.auth import authenticate, login, logout
from django.db import connection, transaction, IntegrityError
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

CAMPOS = ('rut','tipo_cliente','nombre','apellido','nombre_fantasia','giro','email','telefono','direccion','estado')
MAX = {'rut':20,'tipo_cliente':40,'nombre':150,'apellido':100,'nombre_fantasia':150,'giro':200,'email':150,'telefono':30,'estado':20}


def fallo(mensaje, codigo=400, errores=None):
    return JsonResponse({'detail':mensaje, 'errors':errores or {}}, status=codigo)


def rut_valido(valor):
    limpio = re.sub(r'[.\s-]', '', valor).upper()
    if not re.fullmatch(r'\d{1,8}[0-9K]', limpio):
        return False
    numero, digito = limpio[:-1], limpio[-1]
    total = sum(int(n) * (2 + (i % 6)) for i,n in enumerate(reversed(numero)))
    resto = 11 - total % 11
    esperado = '0' if resto == 11 else 'K' if resto == 10 else str(resto)
    return digito == esperado


def normalizar_rut(valor):
    limpio = re.sub(r'[.\s-]', '', valor).upper()
    return limpio[:-1] + '-' + limpio[-1]


def validar(data, parcial=False):
    errores = {}
    if not isinstance(data, dict):
        return {}, {'body':'Se espera un objeto JSON.'}
    extras = set(data) - set(CAMPOS)
    if extras:
        errores['campos'] = 'Campos no admitidos: ' + ', '.join(sorted(extras))
    limpio = {}
    for k in CAMPOS:
        if k in data:
            if data[k] is not None and not isinstance(data[k], str):
                errores[k] = 'Debe ser texto.'
                continue
            limpio[k] = (data[k] or '').strip()
            if k in MAX and len(limpio[k]) > MAX[k]:
                errores[k] = f'Máximo {MAX[k]} caracteres.'
    for k in ('nombre','rut','email','telefono','direccion'):
        if (not parcial or k in data) and not limpio.get(k):
            errores[k] = 'Campo obligatorio.'
    if not parcial and limpio.get('tipo_cliente', 'persona_natural') == 'persona_natural' and not limpio.get('apellido'):
        errores['apellido'] = 'Los apellidos son obligatorios para persona natural.'
    if limpio.get('rut'):
        if not rut_valido(limpio['rut']): errores['rut'] = 'RUT inválido (dígito verificador).'
        else: limpio['rut'] = normalizar_rut(limpio['rut'])
    if limpio.get('email') and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', limpio['email']):
        errores['email'] = 'Correo electrónico inválido.'
    if 'tipo_cliente' in limpio and limpio['tipo_cliente'] not in ('persona_natural','empresa'):
        errores['tipo_cliente'] = 'Tipo de cliente no admitido.'
    if 'estado' in limpio and limpio['estado'] not in ('activo','inactivo'):
        errores['estado'] = 'Estado no admitido.'
    return limpio, errores


def obtener_clientes(cursor):
    cursor.execute('SELECT id_cliente, ' + ', '.join(CAMPOS) + ' FROM cliente ORDER BY id_cliente')
    return [dict(zip(('id_cliente',)+CAMPOS, fila)) for fila in cursor.fetchall()]


def autorizado(request):
    # Solo personal administrativo; no se confía en un rol enviado por React.
    return request.user.is_authenticated and request.user.is_active and request.user.is_staff


@ensure_csrf_cookie
@require_http_methods(['GET'])
def sesion(request):
    return JsonResponse({'authenticated':request.user.is_authenticated,
                         'can_write':autorizado(request),
                         'username':request.user.get_username() if request.user.is_authenticated else ''})


@require_http_methods(['POST'])
def entrar(request):
    try: data = json.loads(request.body)
    except (ValueError, UnicodeDecodeError): return fallo('JSON inválido.')
    user = authenticate(request, username=data.get('username',''), password=data.get('password',''))
    if user is None or not user.is_active: return fallo('Credenciales inválidas.', 401)
    login(request, user)
    return JsonResponse({'authenticated':True,'can_write':autorizado(request),'username':user.get_username()})


@require_http_methods(['POST'])
def salir(request):
    logout(request)
    return JsonResponse({'authenticated':False})


@require_http_methods(['GET','POST'])
def clientes(request):
    if request.method == 'GET':
        # Se protege también la lectura de información personal.
        if not autorizado(request): return fallo('Inicia sesión con una cuenta administrativa.',403)
        with connection.cursor() as cursor: lista = obtener_clientes(cursor)
        return JsonResponse(lista, safe=False)
    if not autorizado(request): return fallo('No tienes permisos para crear clientes.',403)
    try: data = json.loads(request.body)
    except (ValueError, UnicodeDecodeError): return fallo('JSON inválido.')
    limpio, errores = validar(data)
    if errores: return fallo('Datos inválidos.',400,errores)
    limpio.setdefault('tipo_cliente','persona_natural')
    limpio.setdefault('estado','activo')
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SELECT id_cliente FROM cliente WHERE upper(replace(replace(rut,'.',''),'-','')) = %s", [limpio['rut'].replace('-','')])
                if cursor.fetchone(): return fallo('Ya existe un cliente con este RUT.',409,{'rut':'RUT duplicado.'})
                campos = list(limpio)
                cursor.execute('INSERT INTO cliente (' + ', '.join(campos) + ') VALUES (' + ', '.join(['%s']*len(campos)) + ') RETURNING id_cliente', [limpio[k] for k in campos])
                nuevo_id = cursor.fetchone()[0]
    except IntegrityError:
        return fallo('No se pudo guardar. Revisa las relaciones y restricciones.',409)
    return JsonResponse({'id_cliente':nuevo_id, 'detail':'Cliente creado.'},status=201)


@require_http_methods(['PATCH'])
def cliente_detalle(request, id_cliente):
    if not autorizado(request): return fallo('No tienes permisos para actualizar clientes.',403)
    try: data = json.loads(request.body)
    except (ValueError, UnicodeDecodeError): return fallo('JSON inválido.')
    limpio, errores = validar(data,parcial=True)
    if errores: return fallo('Datos inválidos.',400,errores)
    if not limpio: return fallo('No hay campos para actualizar.')
    # Validar el estado final, incluso si PATCH cambia solo tipo_cliente o apellido.
    with connection.cursor() as cursor:
        cursor.execute('SELECT tipo_cliente, apellido FROM cliente WHERE id_cliente = %s', [id_cliente])
        fila = cursor.fetchone()
    if fila is None: return fallo('Cliente no encontrado.',404)
    tipo_final = limpio.get('tipo_cliente', fila[0])
    apellido_final = limpio.get('apellido', fila[1])
    if tipo_final == 'persona_natural' and not (apellido_final or '').strip():
        return fallo('Datos inválidos.',400,{'apellido':'Los apellidos son obligatorios para persona natural.'})
    if tipo_final == 'empresa' and 'tipo_cliente' in limpio and limpio['tipo_cliente'] == 'empresa':
        limpio['apellido'] = ''
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute('SELECT id_cliente FROM cliente WHERE id_cliente = %s FOR UPDATE',[id_cliente])
            if cursor.fetchone() is None: return fallo('Cliente no encontrado.',404)
            if 'rut' in limpio:
                cursor.execute("SELECT id_cliente FROM cliente WHERE upper(replace(replace(rut,'.',''),'-','')) = %s AND id_cliente <> %s",[limpio['rut'].replace('-',''),id_cliente])
                if cursor.fetchone(): return fallo('RUT duplicado.',409,{'rut':'RUT duplicado.'})
            campos = list(limpio)
            cursor.execute('UPDATE cliente SET ' + ', '.join(f'{k} = %s' for k in campos) + ', updated_at = CURRENT_TIMESTAMP WHERE id_cliente = %s', [limpio[k] for k in campos] + [id_cliente])
    return JsonResponse({'id_cliente':id_cliente,'detail':'Cliente actualizado.'})
