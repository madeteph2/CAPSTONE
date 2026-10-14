
import { useEffect, useState } from "react";

export default function EventoFormulario({
  onCancelar,
  onGuardado,
  csrfToken,
}) {

  const [form, setForm] = useState({
    nombre_evento: "",
    fecha_evento: "",
    hora_evento: "",
    direccion: "",
    cantidad_personas: "",
    observaciones: "",
    estado: "planificado",
    id_cliente: "",
    });
    const [clientes, setClientes] = useState([]);
    const [cargandoClientes, setCargandoClientes] = useState(true);
    const [errorClientes, setErrorClientes] = useState("");
    const [guardando, setGuardando] = useState(false);
    const [errorGuardado, setErrorGuardado] = useState("");
    
    
useEffect(() => {
  const controller = new AbortController();

  async function cargarClientes() {
    try {
      setCargandoClientes(true);
      setErrorClientes("");

      const respuesta = await fetch("/api/clientes/", {
        credentials: "same-origin",
        signal: controller.signal,
      });

      if (!respuesta.ok) {
        throw new Error(
          `No se pudieron cargar los clientes (${respuesta.status}).`
        );
      }

      const datos = await respuesta.json();

      let lista;

      if (Array.isArray(datos)) {
        lista = datos;
      } else if (Array.isArray(datos.results)) {
        lista = datos.results;
      } else {
        throw new Error(
          "La API de clientes devolvió un formato inesperado."
        );
      }

      if (!controller.signal.aborted) {
        setClientes(lista);
      }
    } catch (err) {
      if (err.name !== "AbortError") {
        setErrorClientes(err.message);
      }
    } finally {
      if (!controller.signal.aborted) {
        setCargandoClientes(false);
      }
    }
  }

  cargarClientes();

  return () => controller.abort();
}, []);


    function cambiar(e) {
    const { name, value } = e.target;
    setForm((anterior) => ({
        ...anterior,
        [name]: value,
        }));
    }


async function enviar(e) {
    e.preventDefault();

    if (guardando) return;

    setGuardando(true);
    setErrorGuardado("");

    const datos = {
        nombre_evento: form.nombre_evento.trim(),
        fecha_evento: form.fecha_evento,
        hora_evento: form.hora_evento || null,
        direccion: form.direccion.trim(),
        cantidad_personas: form.cantidad_personas
        ? Number(form.cantidad_personas)
        : null,
        observaciones: form.observaciones.trim() || null,
        estado: form.estado,
        id_cliente: Number(form.id_cliente),
    };

    try {
        const respuesta = await fetch("/api/eventos/", {
        method: "POST",
        credentials: "same-origin",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify(datos),
        });

    const resultado = await respuesta.json();

    if (!respuesta.ok) {
        const detalles = resultado.errors
            ? Object.entries(resultado.errors)
                .map(([campo, mensajes]) => (
                `${campo}: ${Array.isArray(mensajes) ? mensajes.join(", ") : mensajes}`
                ))
                .join(" | ")
            : resultado.detail;

        throw new Error(
            detalles || `No se pudo guardar el evento (${respuesta.status}).`
        );
        }

        if (respuesta.status !== 201) {
        throw new Error(
            `Respuesta inesperada del servidor: ${respuesta.status}.`
        );
        }

        await onGuardado(resultado);
    } catch (err) {
        setErrorGuardado(
        err.message || "No fue posible guardar el evento."
        );
    } finally {
        setGuardando(false);
    }
    }


        return (
        <>
        <div className="w03-heading">
        <div className="w02-intro">
            <div className="w02-breadcrumb">
                Inicio / Eventos / Nuevo evento
            </div>
            <h1>Nuevo evento</h1>
            <p>Registro de un servicio de banquetería.</p>
            </div>
        </div>

        <form onSubmit={enviar}>
        <section className="w02-card w04-section">
            <h2>Información del evento</h2>

          <div className="w04-grid">
            <label className="w04-field">
              <span>Nombre del evento *</span>
              <input
                name="nombre_evento"
                value={form.nombre_evento}
                onChange={cambiar}
                required
                maxLength={150}
                placeholder="Ej. Matrimonio González"
              />
            </label>

            <label className="w04-field">
              <span>Fecha del evento *</span>
              <input
                type="date"
                name="fecha_evento"
                value={form.fecha_evento}
                onChange={cambiar}
                required
              />
            </label>

            <label className="w04-field">
              <span>Hora</span>
              <input
                type="time"
                name="hora_evento"
                value={form.hora_evento}
                onChange={cambiar}
              />
            </label>

            <label className="w04-field">
              <span>Cantidad de personas</span>
              <input
                type="number"
                name="cantidad_personas"
                value={form.cantidad_personas}
                onChange={cambiar}
                min="1"
                step="1"
                placeholder="Ej. 50"
              />
            </label>

            <label className="w04-field">
              <span>Dirección *</span>
              <input
                name="direccion"
                value={form.direccion}
                onChange={cambiar}
                required
                placeholder="Calle, número, comuna"
              />
            </label>

            <label className="w04-field">
              <span>Estado *</span>
              <select
                name="estado"
                value={form.estado}
                onChange={cambiar}
                required
              >
                <option value="planificado">Planificado</option>
              </select>
            </label>

            
<label className="w04-field">
  <span>Cliente asociado *</span>

  <select
    name="id_cliente"
    value={form.id_cliente}
    onChange={cambiar}
    required
    disabled={cargandoClientes || Boolean(errorClientes)}
  >
    <option value="">
      {cargandoClientes
        ? "Cargando clientes..."
        : "Seleccionar cliente"}
    </option>

    {clientes.map((cliente) => {
      const nombre =
        cliente.tipo_cliente === "empresa"
          ? (cliente.nombre_fantasia || cliente.nombre)
          : [cliente.nombre, cliente.apellido]
              .filter(Boolean)
              .join(" ");

      return (
        <option
          key={cliente.id_cliente}
          value={cliente.id_cliente}
        >
          {nombre}
        </option>
      );
    })}
  </select>

  {errorClientes && (
    <small className="w04-error" role="alert">
      {errorClientes}
    </small>
  )}
</label>


            <label className="w04-field">
              <span>Observaciones</span>
              <textarea
                name="observaciones"
                value={form.observaciones}
                onChange={cambiar}
                rows={3}
                placeholder="Información complementaria"
              />
            </label>
          </div>
        </section>

{errorGuardado && (
  <p className="w04-error" role="alert">
    {errorGuardado}
  </p>
)}

        <div className="w04-actions">
          <button
            type="button"
            className="w03-action"
            onClick={onCancelar}
          >
            Cancelar
          </button>
          <button
  className="w03-primary"
  type="submit"
  disabled={guardando || cargandoClientes || Boolean(errorClientes)}
>
  {guardando ? "Guardando..." : "Guardar evento"}
</button>

        </div>
      </form>
    </>
  );
}
