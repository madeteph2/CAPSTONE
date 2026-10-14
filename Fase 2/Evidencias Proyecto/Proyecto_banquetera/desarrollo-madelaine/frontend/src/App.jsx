import { useEffect, useMemo, useState } from "react";
import Eventos from "./Eventos";
import "./App.css";

const MENU = [
  ["Dashboard", "▦"], ["Clientes", "♙"], ["Eventos", "▣"],
  ["Pedidos", "▤"], ["Fichas técnicas", "▧"], ["Inventario", "◫"],
  ["Cotizador", "▥"], ["Ventas / Facturación", "▥"],
  ["Usuarios / Roles", "♙"], ["Incidencias", "⚑"],
];

function normalizarLista(data) {
  if (Array.isArray(data)) return { items: data, total: data.length };
  if (data && Array.isArray(data.results))
    return { items: data.results, total: Number.isFinite(data.count) ? data.count : data.results.length };
  throw new Error("La API devolvió un formato inesperado.");
}

function fechaLegible(fecha) {
  if (!fecha) return "Sin fecha";
  const partes = fecha.slice(0, 10).split("-");
  return partes.length === 3 ? `${partes[2]}/${partes[1]}/${partes[0]}` : fecha;
}

const formularioVacio = {
  nombre: "", apellido: "", nombre_fantasia: "", rut: "", email: "",
  telefono: "", direccion: "", tipo_cliente: "persona_natural",
  giro: "", estado: "activo", observaciones: ""
};

function ClienteFormulario({ inicial, modo, onCancelar, onGuardado, csrfToken }) {
  const [guardando, setGuardando] = useState(false);
  const [mensaje, setMensaje] = useState("");
  const [form, setForm] = useState(() => inicial ? {
    ...formularioVacio,
    ...Object.fromEntries(Object.keys(formularioVacio).map(k => [k, inicial[k] ?? ""])),
    observaciones: ""
  } : formularioVacio);
  const [errores, setErrores] = useState({});
  const [validado, setValidado] = useState(false);
  const cambiar = (e) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value, ...(name === "tipo_cliente" && value === "empresa" ? { apellido: "" } : {}) }));
    setValidado(false);
    setErrores(prev => ({ ...prev, [name]: "" }));
  };
  const validar = async (e) => {
    e.preventDefault();
    const err = {};
    if (!form.nombre.trim()) err.nombre = form.tipo_cliente === "empresa" ? "Ingrese la razón social." : "Ingrese el nombre.";
    if (form.tipo_cliente === "persona_natural" && !form.apellido.trim()) err.apellido = "Ingrese los apellidos.";
    if (!form.rut.trim()) err.rut = "Ingrese el RUT.";
    else if (!/^[0-9.]+-[0-9kK]$/.test(form.rut.trim())) err.rut = "Formato esperado: 12.345.678-9.";
    if (!form.email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) err.email = "Ingrese un correo válido.";
    if (!form.telefono.trim()) err.telefono = "Ingrese un teléfono.";
    if (!form.direccion.trim()) err.direccion = "Ingrese una dirección.";
    setErrores(err);
    if (Object.keys(err).length) { setValidado(false); return; }
    const datos = Object.fromEntries(Object.entries(form).filter(([k]) => k !== "observaciones"));
    const url = modo === "editar" ? `/api/clientes/${inicial.id_cliente}/` : "/api/clientes/";
    try {
      setGuardando(true); setMensaje("");
      const res = await fetch(url, {
        method: modo === "editar" ? "PATCH" : "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
        body: JSON.stringify(datos),
      });
      const respuesta = await res.json();
      if (!res.ok) {
        setErrores(respuesta.errors || {});
        setMensaje(respuesta.detail || "No fue posible guardar el cliente.");
        return;
      }
      setValidado(true);
      await onGuardado();
    } catch {
      setMensaje("Error de conexión. Comprueba Django y vuelve a intentar.");
    } finally { setGuardando(false); }
  };
  const campo = (nombre, titulo, placeholder, requerido = false, tipo = "text") => (
    <label className="w04-field" key={nombre}>
      <span>{titulo} {requerido && <b className="w04-required">*</b>}</span>
      <input type={tipo} name={nombre} value={form[nombre]} onChange={cambiar}
        placeholder={placeholder} aria-invalid={Boolean(errores[nombre])}
        maxLength={nombre === "rut" ? 20 : nombre === "telefono" ? 30 : 150} />
      {errores[nombre] && <small className="w04-error">{errores[nombre]}</small>}
    </label>
  );
  return <>
    <div className="w04-header">
      <div className="w02-intro">
        <div className="w02-breadcrumb">Inicio / Clientes / {modo === "editar" ? "Editar cliente" : "Nuevo cliente"}</div>
        <h1>{modo === "editar" ? "Editar cliente" : "Nuevo cliente"}</h1>
        <p>W04 · Registro y actualización de la información de clientes.</p>
      </div>
      <span className="w04-badge">Guardado protegido · PostgreSQL</span>
    </div>
    <form onSubmit={validar} noValidate>
      <section className="w02-card w04-section">
        <h2>Información del cliente</h2>
        <div className="w04-grid">
          {campo("nombre", form.tipo_cliente === "empresa" ? "Razón social" : "Nombre", form.tipo_cliente === "empresa" ? "Ej. Eventos Maya SpA" : "Ej. María José", true)}
          {campo("rut", "RUT", "12.345.678-9", true)}
          {campo("email", "Correo electrónico", "cliente@correo.cl", true, "email")}
          {campo("telefono", "Teléfono", "+56 9 1234 5678", true, "tel")}
          {campo("direccion", "Dirección", "Calle, número, comuna, ciudad", true)}
          {form.tipo_cliente === "persona_natural" && campo("apellido", "Apellidos", "Ej. González Pérez", true)}
        </div>
      </section>
      <section className="w02-card w04-section">
        <h2>Información complementaria</h2>
        <div className="w04-grid">
          <label className="w04-field"><span>Tipo de cliente</span>
            <select name="tipo_cliente" value={form.tipo_cliente} onChange={cambiar}>
              <option value="persona_natural">Persona natural</option>
              <option value="empresa">Empresa</option>
            </select>
          </label>
          <label className="w04-field"><span>Estado</span>
            <select name="estado" value={form.estado} onChange={cambiar}>
              <option value="activo">Activo</option><option value="inactivo">Inactivo</option>
            </select>
            <small>Un cliente inactivo conserva su información histórica.</small>
          </label>
          {campo("nombre_fantasia", "Nombre de fantasía (opcional)", "Alias o nombre comercial")}
          {campo("giro", "Giro", "Actividad comercial")}
          <label className="w04-field w04-full"><span>Observaciones</span>
            <textarea name="observaciones" rows="4" value={form.observaciones}
              onChange={cambiar} placeholder="Información adicional relevante del cliente..." />
            <small>El esquema actual de cliente no contiene un campo observaciones. Este dato no se guardará.</small>
          </label>
        </div>
      </section>
      {mensaje && <div className="w02-message w02-error" role="alert">{mensaje}</div>}
      {validado && <div className="w04-success" role="status">Cliente guardado correctamente en PostgreSQL.</div>}
      <div className="w04-actions">
        <button type="button" className="w04-secondary" onClick={onCancelar}>Cancelar / Volver a clientes</button>
        <button type="submit" className="w03-primary" disabled={guardando}>{guardando ? "Guardando…" : modo === "editar" ? "Guardar cambios" : "Crear cliente"}</button>
      </div>
    </form>
  </>;
}



const pedidoInicial = {
  numero_pedido: "", id_cliente: "", id_evento: "", id_estado_pedido: "",
  id_usuario_responsable: "", fecha_compromiso: "", fecha_entrega: "",
  costo_estimado: "", margen_objetivo: "", precio_estimado: "", observaciones: ""
};

function PedidoFormulario({ inicial, clientes, pedidos, csrfToken, onCancelar, onGuardado }) {
  const editando = Boolean(inicial);
  const [form, setForm] = useState(() => ({ ...pedidoInicial, ...(inicial || {}),
    fecha_compromiso: inicial?.fecha_compromiso?.slice(0, 10) || "",
    fecha_entrega: inicial?.fecha_entrega?.slice(0, 10) || "",
    id_cliente: String(inicial?.id_cliente ?? ""),
    id_evento: String(inicial?.id_evento ?? ""),
    id_estado_pedido: String(inicial?.id_estado_pedido ?? ""),
    id_usuario_responsable: String(inicial?.id_usuario_responsable ?? "")
  }));
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState("");
  const [errores, setErrores] = useState({});
  const estados = [...new Map(pedidos.filter(p => p.id_estado_pedido != null).map(p => [String(p.id_estado_pedido), p.nombre_estado || `Estado ${p.id_estado_pedido}`])).entries()];
  const cambiar = e => { const {name, value} = e.target; setForm(p => ({...p, [name]: value})); setErrores(p => ({...p, [name]: ""})); };
  const guardar = async e => {
    e.preventDefault(); setError(""); setErrores({});
    const err = {};
    if (!form.numero_pedido.trim()) err.numero_pedido = "Ingrese un número de pedido.";
    if (!form.id_cliente) err.id_cliente = "Seleccione un cliente.";
    if (!form.id_estado_pedido) err.id_estado_pedido = "Seleccione un estado.";
    for (const k of ["costo_estimado", "margen_objetivo", "precio_estimado"]) {
      if (form[k] === "" || !Number.isFinite(Number(form[k])) || Number(form[k]) < 0) err[k] = "Ingrese un valor numérico no negativo.";
    }
    if (form.fecha_compromiso && form.fecha_entrega && form.fecha_entrega < form.fecha_compromiso) err.fecha_entrega = "La entrega no puede ser anterior al compromiso.";
    if (Object.keys(err).length) { setErrores(err); return; }
    const datos = {
      numero_pedido: form.numero_pedido.trim(),
      id_cliente: Number(form.id_cliente),
      id_estado_pedido: Number(form.id_estado_pedido),
      id_evento: form.id_evento ? Number(form.id_evento) : null,
      id_usuario_responsable: form.id_usuario_responsable ? Number(form.id_usuario_responsable) : null,
      fecha_compromiso: form.fecha_compromiso || null,
      fecha_entrega: form.fecha_entrega || null,
      costo_estimado: form.costo_estimado,
      margen_objetivo: form.margen_objetivo,
      precio_estimado: form.precio_estimado,
      observaciones: form.observaciones || ""
    };
    try {
      setGuardando(true);
      const respuesta = await fetch(editando ? `/api/pedidos/${inicial.id_pedido}/` : "/api/pedidos/nuevo/", {
        method: editando ? "PATCH" : "POST", credentials: "same-origin",
        headers: {"Content-Type": "application/json", "X-CSRFToken": csrfToken},
        body: JSON.stringify(datos)
      });
      const resultado = await respuesta.json().catch(() => ({}));
      if (!respuesta.ok) {
        setError(resultado.detail || `No se pudo guardar (HTTP ${respuesta.status}).`);
        setErrores(resultado.errors || Object.fromEntries(Object.entries(resultado).filter(([k]) => k !== "detail")));
        return;
      }
      await onGuardado();
    } catch { setError("No fue posible contactar con Django. Revisa el servidor y el proxy de Vite."); }
    finally { setGuardando(false); }
  };
  const campo = (nombre, titulo, tipo = "text", obligatorio = false) => <label className="w04-field" key={nombre}>
    <span>{titulo}{obligatorio && <b className="w04-required"> *</b>}</span>
    <input name={nombre} type={tipo} value={form[nombre] ?? ""} onChange={cambiar} required={obligatorio} step={tipo === "number" ? "0.01" : undefined} min={tipo === "number" ? "0" : undefined} />
    {errores[nombre] && <small className="w04-error">{String(errores[nombre])}</small>}
  </label>;
  return <>
    <div className="w03-heading w05-heading"><div className="w02-intro"><div className="w02-breadcrumb">Inicio / Pedidos / {editando ? "Editar" : "Nuevo"}</div><h1>{editando ? `Editar ${inicial.numero_pedido}` : "Nuevo pedido"}</h1><p>W05 · Registro de pedidos.</p></div></div>
    <form onSubmit={guardar} className="w05-formulario">
      <section className="w02-card w04-section"><h2>Información del pedido</h2><div className="w04-grid">
        {campo("numero_pedido", "Número de pedido", "text", true)}
        <label className="w04-field"><span>Cliente <b className="w04-required">*</b></span><select name="id_cliente" value={form.id_cliente} onChange={cambiar}><option value="">Seleccione un cliente</option>{clientes.map(c => <option key={c.id_cliente} value={c.id_cliente}>{c.nombre} {c.tipo_cliente === "empresa" ? "" : (c.apellido || "")}</option>)}</select>{errores.id_cliente && <small className="w04-error">{String(errores.id_cliente)}</small>}</label>
        <label className="w04-field"><span>Estado <b className="w04-required">*</b></span><select name="id_estado_pedido" value={form.id_estado_pedido} onChange={cambiar}><option value="">Seleccione un estado</option>{estados.map(([id, nombre]) => <option key={id} value={id}>{nombre}</option>)}</select>{errores.id_estado_pedido && <small className="w04-error">{String(errores.id_estado_pedido)}</small>}<small>Se muestran los estados presentes en los pedidos cargados.</small></label>
        {campo("id_evento", "ID del evento (opcional)", "number")}
        {campo("id_usuario_responsable", "ID del responsable (opcional)", "number")}
        {campo("fecha_compromiso", "Fecha compromiso", "date")}
        {campo("fecha_entrega", "Fecha entrega", "date")}
      </div></section>
      <section className="w02-card w04-section"><h2>Valores y observaciones</h2><div className="w04-grid">
        {campo("costo_estimado", "Costo estimado", "number", true)}
        {campo("precio_estimado", "Precio estimado", "number", true)}
        {campo("margen_objetivo", "Margen objetivo (%)", "number", true)}
        <label className="w04-field w04-full"><span>Observaciones</span><textarea name="observaciones" rows="4" value={form.observaciones || ""} onChange={cambiar}/></label>
      </div></section>
      {error && <div className="w02-message w02-error" role="alert">{error}</div>}
      <div className="w04-actions"><button className="w04-secondary" type="button" onClick={onCancelar}>Cancelar</button><button className="w03-primary" type="submit" disabled={guardando}>{guardando ? "Guardando…" : editando ? "Guardar cambios" : "Crear pedido"}</button></div>
    </form>
  </>;
}

function PedidosVista({ registros, total, cargando, error, onNuevo, onEditar }) {
  const [consulta, setConsulta] = useState("");
  const [estado, setEstado] = useState("todos");
  const [responsable, setResponsable] = useState("todos");
  const [seleccionado, setSeleccionado] = useState(null);
  const estados = useMemo(() => [...new Set(registros.map(p => p.nombre_estado).filter(Boolean))].sort(), [registros]);
  const responsables = useMemo(() => [...new Set(registros.map(p => p.nombre_responsable).filter(Boolean))].sort(), [registros]);
  const filtrados = useMemo(() => registros.filter(p => {
    const texto = [p.numero_pedido, p.nombre_cliente, p.nombre_evento, p.nombre_responsable]
      .filter(Boolean).join(" ").toLocaleLowerCase("es");
    return texto.includes(consulta.trim().toLocaleLowerCase("es")) &&
      (estado === "todos" || p.nombre_estado === estado) &&
      (responsable === "todos" || p.nombre_responsable === responsable);
  }), [registros, consulta, estado, responsable]);
  const formatoDinero = v => v == null || v === "" ? "—" : new Intl.NumberFormat("es-CL", { style: "currency", currency: "CLP", maximumFractionDigits: 0 }).format(Number(v));
  const etiquetaEstado = v => (v || "Sin estado").replaceAll("_", " ");
  const estiloEstado = v => {
    const t = (v || "").toLocaleLowerCase("es");
    if (t.includes("cancel")) return "cancelado";
    if (t.includes("confirm")) return "confirmado";
    if (t.includes("complet") || t.includes("finaliz")) return "completado";
    if (t.includes("prepar")) return "preparacion";
    return "pendiente";
  };
  return <>
    <div className="w03-heading w05-heading">
      <div className="w02-intro"><div className="w02-breadcrumb">Inicio / Pedidos</div>
        <h1>W05 - Pedidos</h1><p>Listado, búsqueda y seguimiento de pedidos.</p></div>
      <button className="w03-primary" type="button" onClick={onNuevo}>+ Nuevo pedido</button>
    </div>
    {error && <div className="w02-message w02-error" role="alert">{error}</div>}
    <section className="w02-card w05-filtros" aria-label="Filtros de pedidos">
      <label><span>Buscar pedido</span><input value={consulta} onChange={e => setConsulta(e.target.value)} placeholder="Pedido, cliente, evento o responsable…" /></label>
      <label><span>Estado</span><select value={estado} onChange={e => setEstado(e.target.value)}><option value="todos">Todos los estados</option>{estados.map(v => <option key={v} value={v}>{etiquetaEstado(v)}</option>)}</select></label>
      <label><span>Responsable</span><select value={responsable} onChange={e => setResponsable(e.target.value)}><option value="todos">Todos los responsables</option>{responsables.map(v => <option key={v} value={v}>{v}</option>)}</select></label>
    </section>
    <section className="w02-card w05-listado">
      <div className="w05-listado-cabecera"><h2>Lista de pedidos ({filtrados.length})</h2><span>Datos reales · PostgreSQL</span></div>
      <div className="w02-table-scroll w05-table-scroll"><table className="w05-table"><colgroup><col className="w05-col-id"/><col className="w05-col-cliente"/><col className="w05-col-fecha"/><col className="w05-col-responsable"/><col className="w05-col-estado"/><col className="w05-col-acciones"/></colgroup><thead><tr><th scope="col">ID</th><th scope="col">Cliente / Evento</th><th scope="col">Fecha evento</th><th scope="col">Responsable</th><th scope="col">Estado</th><th scope="col">Acciones</th></tr></thead>
        <tbody>{filtrados.map(p => <tr key={p.id_pedido}>
          <td><strong>{p.numero_pedido || `#${p.id_pedido}`}</strong></td>
          <td><strong>{p.nombre_cliente || "Cliente no disponible"}</strong><small className="w05-evento">{p.nombre_evento || "Evento no disponible"}</small></td>
          <td>{fechaLegible(p.fecha_entrega || p.fecha_compromiso)}</td>
          <td>{p.nombre_responsable || "—"}</td>
          <td><span className={`w05-estado ${estiloEstado(p.nombre_estado)}`}>{etiquetaEstado(p.nombre_estado)}</span></td>
          <td><div className="w05-table-actions"><button className="w05-icon-button" type="button" onClick={() => setSeleccionado(p)} aria-label={`Consultar ${p.numero_pedido || p.id_pedido}`} title="Consultar pedido"><svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/></svg></button><button className="w05-icon-button" type="button" onClick={() => onEditar(p)} aria-label={`Editar ${p.numero_pedido || p.id_pedido}`} title="Editar pedido"><svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9"/><path d="m16 4 4 4L9 19l-5 1 1-5L16 4Z"/></svg></button></div></td>
        </tr>)}
        {cargando && <tr><td colSpan="6">Cargando pedidos…</td></tr>}
        {!cargando && !error && filtrados.length === 0 && <tr><td colSpan="6">No se encontraron pedidos.</td></tr>}
        </tbody></table></div>
      {total != null && total > registros.length && <p className="w02-note">Mostrando {registros.length} de {total} pedidos. La búsqueda y los filtros abarcan solo los registros recibidos; falta paginación.</p>}
      <p className="w02-note">Creación y edición protegidas mediante sesión Django.</p>
    </section>
    {seleccionado && <section className="w02-card w05-detalle" aria-label="Detalle del pedido">
      <div className="w05-listado-cabecera"><h2>Detalle de {seleccionado.numero_pedido || `#${seleccionado.id_pedido}`}</h2><button type="button" className="w03-action" onClick={() => setSeleccionado(null)}>Cerrar</button></div>
      <dl>{[
        ["Cliente", seleccionado.nombre_cliente], ["Evento", seleccionado.nombre_evento],
        ["Responsable", seleccionado.nombre_responsable], ["Estado", etiquetaEstado(seleccionado.nombre_estado)],
        ["Fecha compromiso", fechaLegible(seleccionado.fecha_compromiso)], ["Fecha entrega", fechaLegible(seleccionado.fecha_entrega)],
        ["Costo estimado", formatoDinero(seleccionado.costo_estimado)], ["Precio estimado", formatoDinero(seleccionado.precio_estimado)],
        ["Margen objetivo (%)", seleccionado.margen_objetivo], ["Observaciones", seleccionado.observaciones]
      ].map(([titulo, valor]) => <div key={titulo}><dt>{titulo}</dt><dd>{valor === null || valor === undefined || valor === "" ? "—" : valor}</dd></div>)}</dl>
    </section>}
  </>;
}

function App() {
  const [vista, setVista] = useState("Dashboard");
  const [sesion, setSesion] = useState(null);
  const [csrfToken, setCsrfToken] = useState("");
  const [usuario, setUsuario] = useState("");
  const [clave, setClave] = useState("");
  const [loginError, setLoginError] = useState("");
  const [mostrarClave, setMostrarClave] = useState(false);
  const [iniciando, setIniciando] = useState(false);
  const leerCsrf = () => decodeURIComponent(document.cookie.split("; ").find(v => v.startsWith("csrftoken="))?.split("=")[1] || "");
  useEffect(() => {
    fetch("/api/auth/session/", { credentials: "same-origin" })
      .then(r => r.json()).then(data => { setSesion(data); setCsrfToken(leerCsrf()); })
      .catch(() => setSesion({ authenticated: false, can_write: false }));
  }, []);
  const iniciarSesion = async (e) => {
    e.preventDefault(); setLoginError(""); setIniciando(true);
    try {
      const r = await fetch("/api/auth/login/", { method: "POST", credentials: "same-origin",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
        body: JSON.stringify({ username: usuario, password: clave }) });
      const data = await r.json();
      if (!r.ok) { setLoginError(data.detail || "Acceso denegado"); return; }
      if (!data.can_write) { setLoginError("La cuenta no tiene permiso administrativo."); return; }
      setSesion(data); setCsrfToken(leerCsrf()); setClave("");
    } catch { setLoginError("No fue posible contactar con Django."); }
    finally { setIniciando(false); }
  };
  const cerrarSesion = async () => {
    await fetch("/api/auth/logout/", { method: "POST", credentials: "same-origin", headers: { "X-CSRFToken": csrfToken } });
    setSesion({ authenticated: false, can_write: false });
  };

  const [modoFormulario, setModoFormulario] = useState("nuevo");
  const [clienteEdicion, setClienteEdicion] = useState(null);
  const [clientes, setClientes] = useState(null);
  const [filasClientes, setFilasClientes] = useState([]);
  const [busqueda, setBusqueda] = useState("");
  const [filtroEstado, setFiltroEstado] = useState("todos");
  const [clienteSeleccionado, setClienteSeleccionado] = useState(null);
  const [pedidos, setPedidos] = useState(null);
  const [filasPedidos, setFilasPedidos] = useState([]);
  const [todosPedidos, setTodosPedidos] = useState([]);
  const [pedidoEdicion, setPedidoEdicion] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");

  const cargarDatos = async () => {
    const respuestas = await Promise.all([fetch("/api/clientes/"), fetch("/api/pedidos/")]);
    if (respuestas.some(r => !r.ok)) throw new Error("API no disponible");
    const [c, p] = await Promise.all(respuestas.map(r => r.json()));
    const clientesNormalizados = normalizarLista(c), pedidosNormalizados = normalizarLista(p);
    setClientes(clientesNormalizados.total); setFilasClientes(clientesNormalizados.items);
    setPedidos(pedidosNormalizados.total); setFilasPedidos(pedidosNormalizados.items.slice(0,5)); setTodosPedidos(pedidosNormalizados.items);
    setError("");
  };
  useEffect(() => {
    if (!sesion?.can_write) return;
    const controller = new AbortController();
    async function cargar() {
      try {
        setCargando(true);
        const respuestas = await Promise.all([
          fetch("/api/clientes/", { signal: controller.signal }),
          fetch("/api/pedidos/", { signal: controller.signal }),
        ]);
        if (respuestas.some((r) => !r.ok)) throw new Error("No se pudo consultar la API.");
        const [clientesData, pedidosData] = await Promise.all(respuestas.map((r) => r.json()));
        const c = normalizarLista(clientesData);
        const p = normalizarLista(pedidosData);
        setClientes(c.total);
        setFilasClientes(c.items);
        setPedidos(p.total);
        setFilasPedidos(p.items.slice(0, 5));
        setTodosPedidos(p.items);
        setError("");
      } catch (e) {
        if (e.name !== "AbortError") setError("No fue posible obtener los datos de Django. Revisa el servidor y el proxy de Vite.");
      } finally {
        if (!controller.signal.aborted) setCargando(false);
      }
    }
    cargar();
    return () => controller.abort();
  }, [sesion?.can_write]);

  const indicador = (valor) => cargando ? "…" : valor ?? "—";
  const clientesFiltrados = useMemo(() => filasClientes.filter((c) => {
    const texto = [c.nombre, c.apellido, c.nombre_fantasia, c.rut, c.email, c.telefono]
      .filter(Boolean).join(" ").toLocaleLowerCase("es");
    return texto.includes(busqueda.trim().toLocaleLowerCase("es")) &&
      (filtroEstado === "todos" || String(c.estado || "").toLowerCase() === filtroEstado);
  }), [filasClientes, busqueda, filtroEstado]);
  const nombreCliente = (c) => c.tipo_cliente === "empresa"
    ? (c.nombre || "Sin razón social")
    : ([c.nombre, c.apellido].filter(Boolean).join(" ") || "Sin nombre");
  const iniciales = (c) => nombreCliente(c).split(" ").slice(0, 2).map(x => x[0]).join("").toUpperCase();

  if (sesion === null) return <div className="w01-loading" role="status">Comprobando sesión…</div>;
  if (!sesion.can_write) return (
    <main className="w01-page">
      <section className="w01-left" aria-label="Presentación del sistema">
        <div className="w01-brand"><span className="w01-logo" aria-hidden="true">☕</span>
          <div><strong>Banquetería Maya</strong><small>Sistema Integral de Gestión</small></div>
        </div>
        <div className="w01-hero">
          <h1>Gestión de banquetería en un solo lugar.</h1>
          <p>Administra clientes, pedidos, inventario y la operación de tus eventos desde una plataforma centralizada.</p>
        </div>
        <div className="w01-features"><span>✓ Gestión centralizada</span><span>✓ Control por roles</span><span>✓ Información segura</span></div>
      </section>
      <section className="w01-right" aria-label="Acceso al sistema">
        <div className="w01-box">
          <div className="w01-intro"><span>W01 · Acceso al sistema</span><h2>Iniciar sesión</h2>
            <p>Ingresa tus credenciales para acceder al sistema.</p></div>
          <form className="w01-card" onSubmit={iniciarSesion}>
            <label htmlFor="w01-usuario">Usuario</label>
            <div className="w01-input-wrap"><span aria-hidden="true">♙</span>
              <input id="w01-usuario" required autoComplete="username" placeholder="Nombre de usuario"
                value={usuario} onChange={e=>setUsuario(e.target.value)} /></div>
            <label htmlFor="w01-clave">Contraseña</label>
            <div className="w01-input-wrap"><span aria-hidden="true">🔒</span>
              <input id="w01-clave" required type={mostrarClave ? "text" : "password"}
                autoComplete="current-password" placeholder="Ingresa tu contraseña"
                value={clave} onChange={e=>setClave(e.target.value)} />
              <button className="w01-toggle" type="button" onClick={()=>setMostrarClave(v=>!v)}
                aria-label={mostrarClave ? "Ocultar contraseña" : "Mostrar contraseña"}
                aria-pressed={mostrarClave}>{mostrarClave ? "Ocultar" : "Mostrar"}</button></div>
            <p className="w01-help">¿Olvidaste tu contraseña? Contacta al administrador del sistema.</p>
            {loginError && <p className="w01-error" role="alert">{loginError}</p>}
            <button className="w01-submit" type="submit" disabled={iniciando}>{iniciando ? "Ingresando…" : "➜  Iniciar sesión"}</button>
            <div className="w01-note">🔐 Acceso protegido mediante autenticación Django y sesiones seguras.</div>
          </form>
          <p className="w01-footnote">Acceso exclusivo para usuarios autorizados.</p>
        </div>
      </section>
    </main>
  );
  return (
    <div className="w02-layout">
      <aside className="w02-sidebar">
        <div className="w02-brand">
          <span className="w02-brand-icon" aria-hidden="true">☕</span>
          <div><strong>Banquetería Maya</strong><small>Sistema Integral de Gestión</small></div>
        </div>
        <nav aria-label="Módulos del sistema">
          {MENU.map(([nombre, icono]) => (
            <button key={nombre} type="button"
              className={`w02-nav-item ${nombre === vista ? "active" : ""}`}
              aria-current={nombre === vista ? "page" : undefined}
              onClick={() => { if (["Dashboard", "Clientes", "Pedidos", "Eventos"].includes(nombre)) {  setVista(nombre);  setAviso("");} else {  setAviso(`${nombre}: módulo pendiente de integración.`);} }}	>      
              <span aria-hidden="true">{icono}</span>{nombre}
            </button>
          ))}
        </nav>
        <div className="w02-sidebar-footer">
          
          {vista === "Dashboard"
          ? "W02 · Dashboard"
          : vista === "FormularioCliente"
          ? "W04 · Formulario Cliente"
          : vista === "Pedidos" || vista === "FormularioPedido"
          ? "W05 · Pedidos"
          : vista === "Eventos"
          ? "Eventos · Gestión de eventos"
          : "W03 · Clientes"}
      </div>
      </aside>

      <div className="w02-main">
        <header className="w02-top">
          <span className="w02-top-title">Panel administrativo</span>
          <span className="w02-user"><span className="w02-avatar">BM</span><span>{sesion.username}<small>Administrador autenticado</small></span><button type="button" className="w04-secondary" onClick={cerrarSesion}>Salir</button></span>
        </header>

        <main className="w02-content">
          {vista === "Dashboard" ? <>
          <div className="w02-intro">
            <div className="w02-breadcrumb">Inicio / Dashboard</div>
            <h1>Dashboard</h1>
            <p>Resumen general de la operación de banquetería.</p>
          </div>

          {error && <div className="w02-message w02-error" role="alert">{error}</div>}
          {aviso && <div className="w02-message" role="status">{aviso} <button type="button" onClick={() => setAviso("")}>Cerrar</button></div>}

          <section className="w02-metrics" aria-label="Indicadores generales">
            <div className="w02-card w02-metric"><div><span>Clientes registrados</span><strong>{indicador(clientes)}</strong><small>Datos reales · PostgreSQL</small></div><div className="w02-metric-icon">♙</div></div>
            <div className="w02-card w02-metric"><div><span>Pedidos registrados</span><strong>{indicador(pedidos)}</strong><small>Total de pedidos · PostgreSQL</small></div><div className="w02-metric-icon">▤</div></div>
            <div className="w02-card w02-metric"><div><span>Ventas del período</span><strong>—</strong><small>Pendiente de API de ventas</small></div><div className="w02-metric-icon">＄</div></div>
            <div className="w02-card w02-metric"><div><span>Rentabilidad</span><strong>—</strong><small>Pendiente de cálculo real</small></div><div className="w02-metric-icon">↗</div></div>
          </section>

          <div className="w02-grid-primary">
            <section className="w02-card w02-section">
              <div className="w02-section-head"><h2>Pedidos registrados</h2><span>Últimos registros recibidos de la API</span></div>
              <div className="w02-table-scroll">
                <table><thead><tr><th>Pedido</th><th>Fecha compromiso</th><th>Cliente (ID)</th><th>Estado (ID)</th></tr></thead>
                  <tbody>
                    {filasPedidos.map((p, i) => (
                      <tr key={p.id_pedido ?? i}>
                        <td><strong>{p.numero_pedido || `#${p.id_pedido ?? "—"}`}</strong></td>
                        <td>{fechaLegible(p.fecha_compromiso)}</td>
                        <td>{p.id_cliente ?? "—"}</td>
                        <td>{p.id_estado_pedido ?? "—"}</td>
                      </tr>
                    ))}
                    {!cargando && !error && filasPedidos.length === 0 && <tr><td colSpan="4">No hay pedidos para mostrar.</td></tr>}
                    {cargando && <tr><td colSpan="4">Cargando pedidos…</td></tr>}
                  </tbody>
                </table>
              </div>
              <p className="w02-note">Los nombres de clientes y estados se incorporarán cuando el backend exponga esas relaciones. Esta tabla no inventa datos.</p>
            </section>

            <section className="w02-card w02-section">
              <h2>Alertas operativas</h2>
              <div className="w02-alert"><span>▣</span><div><strong>Stock crítico</strong><p>Pendiente de integración con inventario.</p></div></div>
              <div className="w02-alert"><span>◷</span><div><strong>Pedidos próximos</strong><p>Pendiente de reglas de fechas y estados.</p></div></div>
              <div className="w02-alert"><span>＄</span><div><strong>Pagos pendientes</strong><p>Pendiente de integración con facturación.</p></div></div>
            </section>
          </div>

          <div className="w02-grid-secondary">
            <section className="w02-card w02-section">
              <h2>Ventas y costos</h2>
              <div className="w02-empty">Las métricas de ventas, costos y margen estarán disponibles al crear un endpoint de resumen financiero.</div>
              <p className="w02-note">Se retiraron las cifras ficticias del prototipo W02.</p>
            </section>
            <section className="w02-card w02-section">
              <h2>Indicadores operativos</h2>
              <div className="w02-line"><span>Clientes registrados</span><strong>{indicador(clientes)}</strong></div>
              <div className="w02-line"><span>Pedidos registrados</span><strong>{indicador(pedidos)}</strong></div>
              <div className="w02-line"><span>Pedidos pendientes</span><strong>—</strong></div>
              <div className="w02-line"><span>Insumos con stock crítico</span><strong>—</strong></div>
              <div className="w02-line"><span>Incidencias abiertas</span><strong>—</strong></div>
            </section>
          </div>
          </> : vista === "FormularioCliente" ? (
            <ClienteFormulario key={`${modoFormulario}-${clienteEdicion?.id_cliente ?? "nuevo"}`}
              inicial={clienteEdicion} modo={modoFormulario}
              onCancelar={() => setVista("Clientes")}
              csrfToken={csrfToken}
              onGuardado={async () => { await cargarDatos(); setVista("Clientes"); setAviso("Cliente guardado correctamente."); }} />
          ) : vista === "FormularioPedido" ? (
            <PedidoFormulario key={pedidoEdicion?.id_pedido ?? "nuevo"} inicial={pedidoEdicion}
              clientes={filasClientes} pedidos={todosPedidos} csrfToken={csrfToken}
              onCancelar={() => setVista("Pedidos")}
              onGuardado={async () => { await cargarDatos(); setVista("Pedidos"); setAviso("Pedido guardado correctamente."); }} />
          
) : vista === "Pedidos" ? (
  <>
    <PedidosVista
      registros={todosPedidos}
      total={pedidos}
      cargando={cargando}
      error={error}
      onNuevo={() => {
        setPedidoEdicion(null);
        setVista("FormularioPedido");
      }}
      onEditar={p => {
        setPedidoEdicion(p);
        setVista("FormularioPedido");
      }}
    />
    {aviso && (
      <div className="w04-success" role="status">
        {aviso}
      </div>
    )}
  </>
  ) : vista === "Eventos" ? (
  <Eventos csrfToken={csrfToken} />
  ) : <>

            <div className="w03-heading">
              <div className="w02-intro"><div className="w02-breadcrumb">Inicio / Clientes</div><h1>Clientes</h1><p>Listado, búsqueda y consulta de clientes registrados.</p></div>
              <button className="w03-primary" type="button" onClick={() => { setModoFormulario("nuevo"); setClienteEdicion(null); setVista("FormularioCliente"); }}>+ Nuevo cliente</button>
            </div>
            <section className="w02-card w03-filters" aria-label="Filtros de clientes">
              <label><span>Buscar clientes</span><input value={busqueda} onChange={(e) => setBusqueda(e.target.value)} placeholder="Nombre, RUT, email o teléfono…" /></label>
              <label><span>Estado</span><select value={filtroEstado} onChange={(e) => setFiltroEstado(e.target.value)}><option value="todos">Todos los estados</option><option value="activo">Activos</option><option value="inactivo">Inactivos</option></select></label>
            </section>
            <div className="w03-columns">
              <section className="w02-card w02-section">
                <div className="w03-section-title"><h2>Lista de clientes ({clientesFiltrados.length})</h2><span>Consulta y actualización protegidas</span></div>
                <div className="w02-table-scroll"><table><thead><tr><th>Cliente</th><th>RUT</th><th>Teléfono</th><th>Email</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>
                  {clientesFiltrados.map((c) => <tr key={c.id_cliente}>
                    <td><div className="w03-name"><span className="w03-initials">{iniciales(c)}</span><div><strong>{nombreCliente(c)}</strong>{c.nombre_fantasia && <small className="w04-alias">Nombre de fantasía: {c.nombre_fantasia}</small>}</div></div></td>
                    <td>{c.rut || "—"}</td><td>{c.telefono || "—"}</td><td>{c.email || "—"}</td>
                    <td><span className={`w03-status ${String(c.estado).toLowerCase() === "activo" ? "on" : "off"}`}>{c.estado || "Sin estado"}</span></td>
                    <td><div className="w04-table-actions"><button className="w03-action" type="button" onClick={() => setClienteSeleccionado(c)} aria-label={`Consultar ${nombreCliente(c)}`}>Consultar</button>
                    <button className="w03-action" type="button" onClick={() => { setModoFormulario("editar"); setClienteEdicion(c); setVista("FormularioCliente"); }} aria-label={`Abrir formulario de ${nombreCliente(c)}`}>Formulario</button></div></td>
                  </tr>)}
                  {cargando && <tr><td colSpan="6">Cargando clientes…</td></tr>}
                  {!cargando && !error && clientesFiltrados.length === 0 && <tr><td colSpan="6">No se encontraron clientes.</td></tr>}
                </tbody></table></div>
                {clientes !== null && clientes > filasClientes.length && <p className="w02-note">La API entrega {filasClientes.length} de {clientes} clientes. Falta implementar paginación para consultar todos los registros.</p>}
              </section>
              <aside className="w02-card w02-section w03-detail"><h2>Detalle del cliente</h2>
                {clienteSeleccionado ? <><div className="w03-detail-heading"><span className="w03-initials large">{iniciales(clienteSeleccionado)}</span><div><strong>{nombreCliente(clienteSeleccionado)}</strong>{clienteSeleccionado.nombre_fantasia && <small className="w04-alias">Nombre de fantasía: {clienteSeleccionado.nombre_fantasia}</small>}<p>{clienteSeleccionado.estado || "Sin estado"}</p></div></div>
                  <dl>{[["RUT",clienteSeleccionado.rut],["Tipo de cliente",clienteSeleccionado.tipo_cliente],["Teléfono",clienteSeleccionado.telefono],["Email",clienteSeleccionado.email],["Dirección",clienteSeleccionado.direccion],["Giro",clienteSeleccionado.giro]].map(([k,v]) => <div key={k}><dt>{k}</dt><dd>{v || "—"}</dd></div>)}</dl>
                </> : <p className="w03-hint">Selecciona «Consultar» en la lista para ver el detalle de un cliente.</p>}
              </aside>
            </div>
          </>}
          <p className="w02-dev-warning">Entorno de desarrollo: las API actuales deben protegerse con autenticación y permisos antes de publicar el sistema.</p>
        </main>
      </div>
    </div>
  );
}
export default App;
