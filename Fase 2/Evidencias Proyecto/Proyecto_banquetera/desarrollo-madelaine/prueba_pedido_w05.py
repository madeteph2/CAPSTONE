
from django.test import Client
from django.contrib.auth import get_user_model
from django.db import transaction
from gestion.models import Pedido

usuario = get_user_model().objects.get(username="seba.zuniga")
pedido = Pedido.objects.order_by("pk").first()

if pedido is None:
    print("ERROR: No existen pedidos para probar.")
else:
    c = Client(
        enforce_csrf_checks=True,
        HTTP_HOST="127.0.0.1",
        raise_request_exception=False
    )
    c.force_login(usuario)
    c.cookies["csrftoken"] = "a" * 32

    observacion_original = pedido.observaciones

    try:
        with transaction.atomic():
            respuesta = c.patch(
                f"/api/pedidos/{pedido.pk}/",
                data={
                    "observaciones": "Prueba de actualizacion W05"
                },
                content_type="application/json",
                HTTP_X_CSRFTOKEN="a" * 32
            )

            print("PATCH autenticado:", respuesta.status_code)
            print("Respuesta:", respuesta.content.decode("utf-8")[:1500])

            pedido.refresh_from_db()

            print("Observacion durante prueba:", pedido.observaciones)

            transaction.set_rollback(True)

    except Exception as error:
        print("ERROR:", type(error).__name__)
        print("Detalle:", str(error)[:1500])

    pedido.refresh_from_db()

    print("Observacion original:", observacion_original)
    print("Observacion despues de revertir:", pedido.observaciones)
    print(
        "Datos restaurados:",
        pedido.observaciones == observacion_original
    )
