import math
from collections import deque

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Solucionador de Transporte", layout="wide")

TOL = 1e-9
EDITOR_KEYS = ("editor_costos", "editor_oferta", "editor_demanda")


# ============================================================
# 1. MÉTODOS DE TRANSPORTE
# ============================================================

def calcular_costo(asignacion, costos):
    return sum(
        asignacion[i][j] * costos[i][j]
        for i in range(len(costos))
        for j in range(len(costos[0]))
    )


def completar_basicas(basicas, m, n):
    """Forma un árbol de m+n-1 básicas, agregando ceros si hace falta."""
    padre = list(range(m + n))

    def buscar(x):
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    def unir(a, b):
        ra, rb = buscar(a), buscar(b)
        if ra == rb:
            return False
        padre[rb] = ra
        return True

    resultado = set()
    for i, j in sorted(basicas):
        if not unir(i, m + j):
            raise ValueError("La base contiene un ciclo; no puede aplicarse MODI.")
        resultado.add((i, j))

    for i in range(m):
        for j in range(n):
            if len(resultado) == m + n - 1:
                return resultado
            if (i, j) not in resultado and unir(i, m + j):
                resultado.add((i, j))

    if len(resultado) != m + n - 1:
        raise ValueError("No se pudo construir una base válida.")
    return resultado


def esquina_noroeste(oferta, demanda, costos):
    of, dem = list(map(float, oferta)), list(map(float, demanda))
    m, n = len(of), len(dem)
    asignacion = [[0.0] * n for _ in range(m)]
    basicas = set()
    i = j = 0

    while i < m and j < n:
        cantidad = min(of[i], dem[j])
        asignacion[i][j] = cantidad
        basicas.add((i, j))
        of[i] -= cantidad
        dem[j] -= cantidad

        if abs(of[i]) <= TOL:
            of[i] = 0.0
        if abs(dem[j]) <= TOL:
            dem[j] = 0.0

        if of[i] == 0 and dem[j] == 0:
            i += 1
            j += 1
        elif of[i] == 0:
            i += 1
        else:
            j += 1

    basicas = completar_basicas(basicas, m, n)
    return asignacion, basicas, calcular_costo(asignacion, costos)


def encontrar_ciclo(basicas, entrante, m, n):
    """Encuentra el ciclo de ajuste usando la ruta del árbol básico."""
    grafo = {('r', i): [] for i in range(m)}
    grafo.update({('c', j): [] for j in range(n)})

    for i, j in basicas:
        fila, columna = ('r', i), ('c', j)
        grafo[fila].append((columna, (i, j)))
        grafo[columna].append((fila, (i, j)))

    inicio = ('r', entrante[0])
    fin = ('c', entrante[1])
    cola = deque([inicio])
    anterior = {inicio: None}

    while cola and fin not in anterior:
        actual = cola.popleft()
        for siguiente, celda in sorted(grafo[actual]):
            if siguiente not in anterior:
                anterior[siguiente] = (actual, celda)
                cola.append(siguiente)

    if fin not in anterior:
        raise ValueError("No se encontró el ciclo de MODI.")

    ruta = []
    nodo = fin
    while nodo != inicio:
        previo, celda = anterior[nodo]
        ruta.append(celda)
        nodo = previo
    ruta.reverse()
    return [entrante] + ruta


def optimizar_modi(asignacion_inicial, basicas_iniciales, costos):
    m, n = len(costos), len(costos[0])
    asignacion = [fila.copy() for fila in asignacion_inicial]
    basicas = completar_basicas(set(basicas_iniciales), m, n)

    for iteracion in range(1000):
        u, v = [None] * m, [None] * n
        u[0] = 0.0

        for _ in range(m + n):
            hubo_cambio = False
            for i, j in sorted(basicas):
                if u[i] is not None and v[j] is None:
                    v[j] = costos[i][j] - u[i]
                    hubo_cambio = True
                elif v[j] is not None and u[i] is None:
                    u[i] = costos[i][j] - v[j]
                    hubo_cambio = True
            if not hubo_cambio:
                break

        if any(x is None for x in u + v):
            raise ValueError("No fue posible calcular los potenciales MODI.")

        # Regla de Bland: tomar la primera celda con costo reducido negativo.
        entrante = None
        for i in range(m):
            for j in range(n):
                if (i, j) not in basicas:
                    reducido = costos[i][j] - u[i] - v[j]
                    if reducido < -TOL:
                        entrante = (i, j)
                        break
            if entrante is not None:
                break

        if entrante is None:
            return asignacion, calcular_costo(asignacion, costos), iteracion

        ciclo = encontrar_ciclo(basicas, entrante, m, n)
        celdas_menos = ciclo[1::2]
        theta = min(asignacion[i][j] for i, j in celdas_menos)
        saliente = min(
            (i, j) for i, j in celdas_menos
            if abs(asignacion[i][j] - theta) <= TOL
        )

        for k, (i, j) in enumerate(ciclo):
            asignacion[i][j] += theta if k % 2 == 0 else -theta
            if abs(asignacion[i][j]) <= TOL:
                asignacion[i][j] = 0.0

        basicas.add(entrante)
        basicas.remove(saliente)

    raise RuntimeError("MODI superó el límite de iteraciones sin converger.")


def formatear_tabla(asignacion, costos, nombres_filas, nombres_columnas):
    filas = []
    for i in range(len(asignacion)):
        fila = {}
        for j, nombre in enumerate(nombres_columnas):
            cantidad = asignacion[i][j]
            costo = costos[i][j]
            fila[nombre] = (
                f"{cantidad:g}  (${costo:g})" if cantidad > TOL
                else f"—  (${costo:g})"
            )
        filas.append(fila)
    return pd.DataFrame(filas, index=nombres_filas)


# ============================================================
# 2. ESTADO PERSISTENTE DE LA INTERFAZ
# ============================================================

def crear_tablas_vacias(m, n):
    nombres_filas = [f"Origen {i + 1}" for i in range(m)]
    nombres_columnas = [f"Destino {j + 1}" for j in range(n)]
    costos = pd.DataFrame(0.0, index=nombres_filas, columns=nombres_columnas)
    oferta = pd.DataFrame({"Oferta": [10.0] * m}, index=nombres_filas)
    demanda = pd.DataFrame([[10.0] * n], index=["Demanda"], columns=nombres_columnas)
    return costos, oferta, demanda


def reiniciar_editores():
    # Es obligatorio hacerlo ANTES de crear los widgets data_editor.
    for clave in EDITOR_KEYS:
        st.session_state.pop(clave, None)


def establecer_tablas(costos, oferta, demanda):
    st.session_state["tabla_costos"] = costos
    st.session_state["tabla_oferta"] = oferta
    st.session_state["tabla_demanda"] = demanda
    reiniciar_editores()


def ejemplo():
    filas = ["Origen 1", "Origen 2", "Origen 3"]
    columnas = ["Destino 1", "Destino 2", "Destino 3"]
    costos = pd.DataFrame(
        [[10.0, 2.0, 20.0], [12.0, 7.0, 9.0], [4.0, 14.0, 16.0]],
        index=filas, columns=columnas,
    )
    oferta = pd.DataFrame({"Oferta": [15.0, 25.0, 10.0]}, index=filas)
    demanda = pd.DataFrame([[5.0, 15.0, 15.0]], index=["Demanda"], columns=columnas)
    return costos, oferta, demanda


def validar_datos(costos, oferta, demanda):
    for nombre, valores in (
        ("costos", [x for fila in costos for x in fila]),
        ("oferta", oferta),
        ("demanda", demanda),
    ):
        for x in valores:
            if not math.isfinite(float(x)):
                raise ValueError(f"Hay un valor vacío o no válido en {nombre}.")
            if float(x) < 0:
                raise ValueError(f"Todos los valores de {nombre} deben ser no negativos.")


# ============================================================
# 3. INTERFAZ STREAMLIT
# ============================================================

st.title("🚚 Solucionador de Transporte: Esquina Noroeste + MODI")
st.write(
    "Edita los costos unitarios, la oferta y la demanda. "
    "Si el problema no está balanceado, se agrega automáticamente "
    "un origen o destino ficticio."
)

with st.sidebar:
    st.header("⚙️ Dimensiones")
    num_origenes = int(st.number_input("Número de Orígenes", 2, 10, 3))
    num_destinos = int(st.number_input("Número de Destinos", 2, 10, 3))
    cargar_ejemplo = st.button("📋 Cargar Ejemplo No Balanceado")

# Se inicializa SOLO si es la primera ejecución o cambiaron dimensiones.
dimensiones = (num_origenes, num_destinos)
if st.session_state.get("dimensiones") != dimensiones:
    st.session_state["dimensiones"] = dimensiones
    establecer_tablas(*crear_tablas_vacias(*dimensiones))

# Cargar el ejemplo reemplaza los datos guardados y limpia ediciones antiguas.
if cargar_ejemplo:
    if dimensiones == (3, 3):
        establecer_tablas(*ejemplo())
        st.sidebar.success("Ejemplo cargado. Puedes resolverlo directamente.")
    else:
        st.sidebar.warning("Para cargar el ejemplo, elige 3 orígenes y 3 destinos.")

col_izq, col_der = st.columns([3, 1])
with col_izq:
    st.subheader("1. Matriz de Costos Unitarios ($)")
    costos_editados = st.data_editor(
        st.session_state["tabla_costos"],
        use_container_width=True,
        num_rows="fixed",
        key="editor_costos",
    )
with col_der:
    st.subheader("2. Oferta")
    oferta_editada = st.data_editor(
        st.session_state["tabla_oferta"],
        use_container_width=True,
        num_rows="fixed",
        key="editor_oferta",
    )

st.subheader("3. Demanda por Destino")
demanda_editada = st.data_editor(
    st.session_state["tabla_demanda"],
    use_container_width=True,
    num_rows="fixed",
    key="editor_demanda",
)

# Conservar las tablas editadas entre todas las ejecuciones de Streamlit.
st.session_state["tabla_costos"] = costos_editados.copy()
st.session_state["tabla_oferta"] = oferta_editada.copy()
st.session_state["tabla_demanda"] = demanda_editada.copy()

if st.button("🚀 Resolver Problema", type="primary", use_container_width=True):
    try:
        oferta = oferta_editada["Oferta"].astype(float).tolist()
        demanda = demanda_editada.iloc[0].astype(float).tolist()
        costos = costos_editados.astype(float).values.tolist()
        validar_datos(costos, oferta, demanda)

        nombres_filas = list(costos_editados.index)
        nombres_columnas = list(costos_editados.columns)
        total_oferta = sum(oferta)
        total_demanda = sum(demanda)

        if total_oferta > total_demanda + TOL:
            diferencia = total_oferta - total_demanda
            demanda.append(diferencia)
            nombres_columnas.append("Destino Ficticio")
            for fila in costos:
                fila.append(0.0)
            st.warning(
                f"Modelo no balanceado: oferta {total_oferta:g}, "
                f"demanda {total_demanda:g}. Se agrega un destino ficticio "
                f"con demanda {diferencia:g} y costo unitario $0."
            )
        elif total_demanda > total_oferta + TOL:
            diferencia = total_demanda - total_oferta
            oferta.append(diferencia)
            nombres_filas.append("Origen Ficticio")
            costos.append([0.0] * len(demanda))
            st.warning(
                f"Modelo no balanceado: oferta {total_oferta:g}, "
                f"demanda {total_demanda:g}. Se agrega un origen ficticio "
                f"con oferta {diferencia:g} y costo unitario $0."
            )
        else:
            st.success(f"Modelo balanceado: {total_oferta:g} unidades.")

        asig_nw, basicas_nw, costo_nw = esquina_noroeste(oferta, demanda, costos)
        asig_opt, costo_opt, iteraciones = optimizar_modi(asig_nw, basicas_nw, costos)

        st.divider()
        col_resultado_1, col_resultado_2 = st.columns(2)
        with col_resultado_1:
            st.markdown("### Fase 1: Esquina Noroeste")
            st.caption("Formato: unidades asignadas ($costo unitario)")
            st.dataframe(
                formatear_tabla(asig_nw, costos, nombres_filas, nombres_columnas),
                use_container_width=True,
            )
            st.metric("Costo Inicial (Z)", f"${costo_nw:,.2f}")

        with col_resultado_2:
            st.markdown(f"### Fase 2: Solución Óptima ({iteraciones} iteraciones)")
            st.caption("Optimización con método MODI (u-v)")
            st.dataframe(
                formatear_tabla(asig_opt, costos, nombres_filas, nombres_columnas),
                use_container_width=True,
            )
            ahorro = max(0.0, costo_nw - costo_opt)
            st.metric(
                "Costo Mínimo Óptimo (Z*)",
                f"${costo_opt:,.2f}",
                delta=f"-${ahorro:,.2f} de ahorro" if ahorro > TOL else "Ya era óptima",
                delta_color="normal" if ahorro <= TOL else "inverse",
            )
    except (ValueError, TypeError, RuntimeError) as error:
        st.error(f"No se pudo resolver el problema: {error}")
