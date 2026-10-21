import streamlit as st
import pandas as pd

st.set_page_config(page_title="Solucionador de Transporte", layout="wide")

# ==========================================
# FUNCIONES ALGORÍTMICAS (NOROESTE + MODI)
# ==========================================

def esquina_noroeste(oferta, demanda, costos):
    of = list(oferta)
    dem = list(demanda)
    m, n = len(of), len(dem)
    
    asignacion = [[0.0] * n for _ in range(m)]
    basicas = set()
    
    i, j = 0, 0
    while i < m and j < n:
        cant = min(of[i], dem[j])
        asignacion[i][j] = cant
        basicas.add((i, j))
        of[i] -= cant
        dem[j] -= cant
        
        if abs(of[i]) < 1e-9 and abs(dem[j]) < 1e-9:
            if i < m - 1:
                basicas.add((i + 1, j))
            elif j < n - 1:
                basicas.add((i, j + 1))
            i += 1
            j += 1
        elif abs(of[i]) < 1e-9:
            i += 1
        else:
            j += 1
            
    costo_total = sum(asignacion[r][c] * costos[r][c] for r in range(m) for c in range(n))
    return asignacion, basicas, costo_total

def encuentra_ciclo(basicas, inicio):
    nodos = set(basicas) | {inicio}
    
    def dfs(camino, buscar_en_fila):
        actual = camino[-1]
        if len(camino) >= 4:
            if buscar_en_fila and actual[0] == inicio[0]:
                return camino
            if not buscar_en_fila and actual[1] == inicio[1]:
                return camino
        
        for sig in nodos:
            if sig == actual or sig in camino:
                continue
            if buscar_en_fila and sig[0] == actual[0]:
                res = dfs(camino + [sig], False)
                if res: return res
            elif not buscar_en_fila and sig[1] == actual[1]:
                res = dfs(camino + [sig], True)
                if res: return res
        return None

    return dfs([inicio], True) or dfs([inicio], False)

def optimizar_modi(asignacion_ini, basicas_ini, costos):
    m, n = len(costos), len(costos[0])
    asig = [list(fila) for fila in asignacion_ini]
    basicas = set(basicas_ini)
    
    iteracion = 0
    while iteracion < 100:
        while len(basicas) < m + n - 1:
            agregado = False
            for r in range(m):
                for c in range(n):
                    if (r, c) not in basicas and not encuentra_ciclo(basicas, (r, c)):
                        basicas.add((r, c))
                        agregado = True
                        break
                if agregado:
                    break
                    
        u = [None] * m
        v = [None] * n
        u[0] = 0.0
        
        for _ in range(m + n):
            for (r, c) in basicas:
                if u[r] is not None and v[c] is None:
                    v[c] = costos[r][c] - u[r]
                elif v[c] is not None and u[r] is None:
                    u[r] = costos[r][c] - v[c]
        
        u = [0.0 if val is None else val for val in u]
        v = [0.0 if val is None else val for val in v]
        
        min_d = 0.0
        celda_entrante = None
        for r in range(m):
            for c in range(n):
                if (r, c) not in basicas:
                    d = costos[r][c] - u[r] - v[c]
                    if d < min_d - 1e-6:
                        min_d = d
                        celda_entrante = (r, c)
                        
        if celda_entrante is None:
            break
            
        ciclo = encuentra_ciclo(basicas, celda_entrante)
        if not ciclo:
            break
            
        celdas_menos = [ciclo[k] for k in range(1, len(ciclo), 2)]
        theta = min(asig[r][c] for (r, c) in celdas_menos)
        celda_saliente = next((r, c) for (r, c) in celdas_menos if abs(asig[r][c] - theta) < 1e-9)
        
        for k, (r, c) in enumerate(ciclo):
            if k % 2 == 0:
                asig[r][c] += theta
            else:
                asig[r][c] -= theta
                if abs(asig[r][c]) < 1e-9:
                    asig[r][c] = 0.0
                    
        basicas.add(celda_entrante)
        basicas.remove(celda_saliente)
        iteracion += 1
        
    costo_opt = sum(asig[r][c] * costos[r][c] for r in range(m) for c in range(n))
    return asig, costo_opt, iteracion

def formatear_tabla(asig, costos, nom_filas, nom_cols):
    datos = []
    for i in range(len(asig)):
        fila_dict = {}
        for j in range(len(asig[0])):
            cant = asig[i][j]
            costo = costos[i][j]
            if cant > 1e-6:
                fila_dict[nom_cols[j]] = f"{cant:g}  (${costo:g})"
            else:
                fila_dict[nom_cols[j]] = f"—  (${costo:g})"
        datos.append(fila_dict)
    return pd.DataFrame(datos, index=nom_filas)

# ==========================================
# INTERFAZ WEB (STREAMLIT)
# ==========================================

st.title("🚚 Solucionador de Transporte: Esquina Noroeste + Óptimo (MODI)")
st.markdown("Ingresa los costos unitarios, la oferta y la demanda directamente en las tablas. El sistema balancea automáticamente el modelo si es necesario.")

with st.sidebar:
    st.header("⚙️ Dimensiones")
    num_origenes = st.number_input("Número de Orígenes (Filas)", min_value=2, max_value=10, value=3)
    num_destinos = st.number_input("Número de Destinos (Columnas)", min_value=2, max_value=10, value=3)
    cargar_ej = st.button("📋 Cargar Ejemplo No Balanceado")

cols_destinos = [f"Destino {j+1}" for j in range(num_destinos)]
filas_origenes = [f"Origen {i+1}" for i in range(num_origenes)]

if cargar_ej and num_origenes == 3 and num_destinos == 3:
    df_costos_ini = pd.DataFrame([[10.0, 2.0, 20.0], [12.0, 7.0, 9.0], [4.0, 14.0, 16.0]], index=filas_origenes, columns=cols_destinos)
    df_oferta_ini = pd.DataFrame({"Oferta": [15.0, 25.0, 10.0]}, index=filas_origenes)
    df_demanda_ini = pd.DataFrame([[5.0, 15.0, 15.0]], index=["Demanda"], columns=cols_destinos)
else:
    df_costos_ini = pd.DataFrame(0.0, index=filas_origenes, columns=cols_destinos)
    df_oferta_ini = pd.DataFrame({"Oferta": [10.0] * num_origenes}, index=filas_origenes)
    df_demanda_ini = pd.DataFrame([[10.0] * num_destinos], index=["Demanda"], columns=cols_destinos)

col1, col2 = st.columns([3, 1])
with col1:
    st.subheader("1. Matriz de Costos Unitarios ($)")
    df_costos_edit = st.data_editor(df_costos_ini, use_container_width=True, key="editor_costos")
with col2:
    st.subheader("2. Oferta")
    df_oferta_edit = st.data_editor(df_oferta_ini, use_container_width=True, key="editor_oferta")

st.subheader("3. Demanda por Destino")
df_demanda_edit = st.data_editor(df_demanda_ini, use_container_width=True, key="editor_demanda")

if st.button("🚀 Resolver Problema", type="primary", use_container_width=True):
    oferta = df_oferta_edit["Oferta"].tolist()
    demanda = df_demanda_edit.iloc[0].tolist()
    costos = df_costos_edit.values.tolist()
    
    if any(x < 0 for x in oferta) or any(x < 0 for x in demanda) or any(c < 0 for fila in costos for c in fila):
        st.error("Error: Todos los costos, ofertas y demandas deben ser mayores o iguales a cero.")
    else:
        st.divider()
        of = list(oferta)
        dem = list(demanda)
        c_mat = [list(fila) for fila in costos]
        nom_f = list(filas_origenes)
        nom_c = list(cols_destinos)
        
        sum_of, sum_dem = sum(of), sum(dem)
        
        if abs(sum_of - sum_dem) > 1e-6:
            if sum_of > sum_dem:
                diff = sum_of - sum_dem
                st.warning(f"**Modelo No Balanceado:** Oferta total ({sum_of:g}) es mayor que la Demanda total ({sum_dem:g}). Se agregó un **Destino Ficticio** con demanda de **{diff:g}** y costos de $0.")
                dem.append(diff)
                nom_c.append("Dest. Ficticio")
                for fila in c_mat:
                    fila.append(0.0)
            else:
                diff = sum_dem - sum_of
                st.warning(f"**Modelo No Balanceado:** Demanda total ({sum_dem:g}) es mayor que la Oferta total ({sum_of:g}). Se agregó un **Origen Ficticio** con oferta de **{diff:g}** y costos de $0.")
                of.append(diff)
                nom_f.append("Orig. Ficticio")
                c_mat.append([0.0] * len(dem))
        else:
            st.success(f"**Modelo Balanceado:** La Oferta total es igual a la Demanda total ({sum_of:g} unidades).")
            
        asig_nw, basicas_nw, costo_nw = esquina_noroeste(of, dem, c_mat)
        asig_opt, costo_opt, iteraciones = optimizar_modi(asig_nw, basicas_nw, c_mat)
        
        res_col1, res_col2 = st.columns(2)
        
        with res_col1:
            st.markdown("### Fase 1: Esquina Noroeste")
            st.caption("Formato de celda: Unidades asignadas ($Costo unitario)")
            st.dataframe(formatear_tabla(asig_nw, c_mat, nom_f, nom_c), use_container_width=True)
            st.metric(label="Costo Inicial (Z)", value=f"${costo_nw:,.2f}")
            
        with res_col2:
            st.markdown(f"### Fase 2: Solución Óptima ({iteraciones} iteraciones)")
            st.caption("Optimizado mediante el Método MODI (u-v) y Stepping-Stone")
            st.dataframe(formatear_tabla(asig_opt, c_mat, nom_f, nom_c), use_container_width=True)
            ahorro = costo_nw - costo_opt
            st.metric(
                label="Costo Mínimo Óptimo (Z*)", 
                value=f"${costo_opt:,.2f}", 
                delta=f"-${ahorro:,.2f} de ahorro" if ahorro > 0 else "Ya era óptima",
                delta_color="normal" if ahorro == 0 else "inverse"
            )
