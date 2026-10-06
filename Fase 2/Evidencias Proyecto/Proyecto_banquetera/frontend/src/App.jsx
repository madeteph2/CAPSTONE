import "./App.css";

function App() {
  return (
    <div className="app">
      <aside className="sidebar">
        <h2>Banquetería Maya</h2>
        <p>Sistema de gestión</p>

        <nav>
          <button>Dashboard</button>
          <button>Clientes</button>
          <button>Pedidos</button>
          <button>Cotizador</button>
          <button>Inventario</button>
        </nav>
      </aside>

      <main className="contenido">
        <header className="header">
          <div>
            <h1>Sistema Integral de Gestión para Banquetería</h1>
            <p>Prototipo inicial del backoffice web</p>
          </div>

          <span className="rol">Administrador</span>
        </header>

        <section className="cards">
          <div className="card">
            <p>Clientes registrados</p>
            <strong>2</strong>
          </div>

          <div className="card">
            <p>Pedidos activos</p>
            <strong>3</strong>
          </div>

          <div className="card">
            <p>Ventas estimadas</p>
            <strong>$850.000</strong>
          </div>

          <div className="card alerta">
            <p>Stock crítico</p>
            <strong>1</strong>
          </div>
        </section>

        <section className="panel">
          <h2>Flujo principal del sistema</h2>
          <p>
            Cliente → Cotización → Pedido → Preparación → Inventario → Evento →
            Cierre → Rentabilidad
          </p>
        </section>

        <section className="panel">
          <h2>Primer avance del proyecto</h2>
          <ul>
            <li>Frontend creado con React y Vite.</li>
            <li>Vista inicial del backoffice administrativo.</li>
            <li>Estructura preparada para conectar API REST y base de datos.</li>
          </ul>
        </section>
      </main>
    </div>
  );
}

export default App;