
import { useEffect, useState } from "react";
import EventoFormulario from "./EventoFormulario";

export default function Eventos({ csrfToken }) {
    const [eventos, setEventos] = useState([]);
    const [mostrarFormulario, setMostrarFormulario] = useState(false);
    const [cargando, setCargando] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        const controller = new AbortController();
        
        async function cargarEventos() {
            try {
                setCargando(true);
                setError("");

                const respuesta = await fetch("/api/eventos/", {
                    credentials: "same-origin",
                    signal: controller.signal,
                });
                if (!respuesta.ok) {
                    throw new Error(`Error al consultar eventos: ${respuesta.status}`

                    );
                }

                const datos = await respuesta.json();
                if (!Array.isArray(datos.eventos)) {
                    throw new Error(
                        "La API devolvió un formato inesperado."
                    );
                }
                setEventos(datos.eventos);
            } catch (err) {
                if (err.name !== "AbortError") {
                    setError(err.message);
                }
            } finally {
                if (!controller.signal.aborted) {
                    setCargando(false);
                }
            }
        }
        
        cargarEventos();

        return () => controller.abort();
        }, []);

            if (mostrarFormulario) {
  return (
    <EventoFormulario
      csrfToken={csrfToken}
      onCancelar={() => setMostrarFormulario(false)}
      onGuardado={async () => {
        setMostrarFormulario(false);
        setCargando(true);
        setError("");

        try {
          const respuesta = await fetch("/api/eventos/", {
            credentials: "same-origin",
          });

          if (!respuesta.ok) {
            throw new Error("No se pudo actualizar el listado.");
          }

          const datos = await respuesta.json();

          if (!Array.isArray(datos.eventos)) {
            throw new Error("Respuesta inesperada de la API.");
          }

          setEventos(datos.eventos);
        } catch (err) {
          setError(err.message);
        } finally {
          setCargando(false);
        }
      }}
    />
  );
}

        return (
    <>
        <div className="w03-heading">
        <div className="w02-intro">
        <div className="w02-breadcrumb">
            Inicio / Eventos
            </div>
            <h1>Eventos</h1>
            <p>
                Consulta y seguimiento de eventos de banquetería.
            </p>
            </div>
            <button
                type="button"
                className="w03-primary"
                onClick={() => setMostrarFormulario(true)}
            >
    + Nuevo evento
  </button>
        </div>

        <section className="w02-card w02-section">
        <h2>Eventos registrados ({eventos.length})</h2>

        {cargando && <p>Cargando eventos...</p>}

        {error && (
            <p role="alert" className="w01-error">
            {error}
            </p>
        )}

        {!cargando && !error && (
            <div className="w02-table-scroll">
            <table>
                <thead>
                <tr>
                    <th>Evento</th>
                    <th>Cliente</th>
                    <th>Fecha</th>
                    <th>Dirección</th>
                    <th>Personas</th>
                    <th>Estado</th>
                </tr>
                </thead>

                <tbody>
                {eventos.map((evento) => (
                    <tr key={evento.id_evento}>
                    <td>{evento.nombre_evento}</td>
                    <td>{evento.nombre_cliente}</td>
                    <td>{evento.fecha_evento}</td>
                    <td>{evento.direccion}</td>
                    <td>{evento.cantidad_personas ?? "—"}</td>
                    <td>{evento.estado}</td>
                    </tr>
                ))}

                {eventos.length === 0 && (
                    <tr>
                    <td colSpan="6">
                        No hay eventos registrados.
                    </td>
                    </tr>
                )}
                </tbody>
            </table>
            </div>
        )}
        </section>
    </>
    );
}
