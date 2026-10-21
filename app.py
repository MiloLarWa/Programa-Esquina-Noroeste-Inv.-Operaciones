import tkinter as tk
from tkinter import ttk, messagebox

class TransporteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Solucionador de Transporte: Esquina Noroeste + Optimización MODI")
        self.root.geometry("950x720")
        
        # Contenedor superior: Configuración de dimensiones
        frame_top = ttk.LabelFrame(root, text="1. Dimensiones del Problema", padding=10)
        frame_top.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame_top, text="Orígenes (Filas):").grid(row=0, column=0, padx=5)
        self.spin_filas = ttk.Spinbox(frame_top, from_=2, to=8, width=5)
        self.spin_filas.set(3)
        self.spin_filas.grid(row=0, column=1, padx=5)
        
        ttk.Label(frame_top, text="Destinos (Columnas):").grid(row=0, column=2, padx=5)
        self.spin_cols = ttk.Spinbox(frame_top, from_=2, to=8, width=5)
        self.spin_cols.set(3)
        self.spin_cols.grid(row=0, column=3, padx=5)
        
        btn_generar = ttk.Button(frame_top, text="Generar Matriz", command=self.generar_cuadricula)
        btn_generar.grid(row=0, column=4, padx=10)
        
        btn_ejemplo = ttk.Button(frame_top, text="Cargar Ejemplo", command=self.cargar_ejemplo)
        btn_ejemplo.grid(row=0, column=5, padx=5)
        
        # Contenedor central: Matriz de entrada
        self.frame_matriz = ttk.LabelFrame(root, text="2. Costos Unitarios, Oferta y Demanda", padding=10)
        self.frame_matriz.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Botón de resolución
        btn_resolver = ttk.Button(root, text="Resolver (Esquina Noroeste + Resultado Óptimo)", command=self.resolver)
        btn_resolver.pack(pady=5)
        
        # Contenedor inferior: Resultados
        frame_res = ttk.LabelFrame(root, text="3. Resultados", padding=10)
        frame_res.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.txt_resultados = tk.Text(frame_res, height=15, font=("Consolas", 10))
        scroll = ttk.Scrollbar(frame_res, command=self.txt_resultados.yview)
        self.txt_resultados.configure(yscrollcommand=scroll.set)
        self.txt_resultados.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        
        self.entries_costos = []
        self.entries_oferta = []
        self.entries_demanda = []
        
        self.generar_cuadricula()

    def generar_cuadricula(self):
        for widget in self.frame_matriz.winfo_children():
            widget.destroy()
            
        try:
            filas = int(self.spin_filas.get())
            cols = int(self.spin_cols.get())
        except ValueError:
            messagebox.showerror("Error", "Ingrese dimensiones válidas.")
            return
            
        self.entries_costos = []
        self.entries_oferta = []
        self.entries_demanda = []
        
        # Encabezados de Destinos
        for j in range(cols):
            ttk.Label(self.frame_matriz, text=f"Destino {j+1}", font=("Arial", 9, "bold")).grid(row=0, column=j+1, padx=5, pady=2)
        ttk.Label(self.frame_matriz, text="OFERTA", font=("Arial", 9, "bold"), foreground="blue").grid(row=0, column=cols+1, padx=5, pady=2)
        
        # Celdas de Costos y Oferta
        for i in range(filas):
            ttk.Label(self.frame_matriz, text=f"Origen {i+1}", font=("Arial", 9, "bold")).grid(row=i+1, column=0, padx=5, pady=2)
            fila_entries = []
            for j in range(cols):
                e = ttk.Entry(self.frame_matriz, width=8, justify="center")
                e.grid(row=i+1, column=j+1, padx=3, pady=3)
                e.insert(0, "0")
                fila_entries.append(e)
            self.entries_costos.append(fila_entries)
            
            e_of = ttk.Entry(self.frame_matriz, width=10, justify="center")
            e_of.grid(row=i+1, column=cols+1, padx=8, pady=3)
            e_of.insert(0, "0")
            self.entries_oferta.append(e_of)
            
        # Fila de Demanda
        ttk.Label(self.frame_matriz, text="DEMANDA", font=("Arial", 9, "bold"), foreground="green").grid(row=filas+1, column=0, padx=5, pady=5)
        for j in range(cols):
            e_dem = ttk.Entry(self.frame_matriz, width=8, justify="center")
            e_dem.grid(row=filas+1, column=j+1, padx=3, pady=5)
            e_dem.insert(0, "0")
            self.entries_demanda.append(e_dem)

    def cargar_ejemplo(self):
        """Carga un caso de prueba no balanceado para demostración rápida."""
        self.spin_filas.set(3)
        self.spin_cols.set(3)
        self.generar_cuadricula()
        
        costos_ej = [[10, 2, 20], [12, 7, 9], [4, 14, 16]]
        oferta_ej = [15, 25, 10]  # Suma = 50
        demanda_ej = [5, 15, 15]  # Suma = 35 (No balanceado)
        
        for i in range(3):
            self.entries_oferta[i].delete(0, tk.END)
            self.entries_oferta[i].insert(0, str(oferta_ej[i]))
            for j in range(3):
                self.entries_costos[i][j].delete(0, tk.END)
                self.entries_costos[i][j].insert(0, str(costos_ej[i][j]))
        for j in range(3):
            self.entries_demanda[j].delete(0, tk.END)
            self.entries_demanda[j].insert(0, str(demanda_ej[j]))

    def resolver(self):
        try:
            oferta = [float(e.get()) for e in self.entries_oferta]
            demanda = [float(e.get()) for e in self.entries_demanda]
            costos = [[float(e.get()) for e in fila] for fila in self.entries_costos]
            if any(x < 0 for x in oferta) or any(x < 0 for x in demanda):
                raise ValueError
        except ValueError:
            messagebox.showerror("Error de entrada", "Todos los campos deben contener números válidos y no negativos.")
            return

        self.txt_resultados.delete(1.0, tk.END)
        
        # --- 1. BALANCEO DEL MODELO ---
        of = list(oferta)
        dem = list(demanda)
        c_mat = [list(fila) for fila in costos]
        
        nombres_filas = [f"Origen {i+1}" for i in range(len(of))]
        nombres_cols = [f"Destino {j+1}" for j in range(len(dem))]
        
        sum_of, sum_dem = sum(of), sum(dem)
        
        if abs(sum_of - sum_dem) > 1e-6:
            if sum_of > sum_dem:
                diff = sum_of - sum_dem
                self.txt_resultados.insert(tk.END, f"[!] PROBLEMA NO BALANCEADO: Oferta ({sum_of:g}) > Demanda ({sum_dem:g}).\n")
                self.txt_resultados.insert(tk.END, f" -> Se agregó 'Destino Ficticio' con demanda = {diff:g} y costos = 0.\n\n")
                dem.append(diff)
                nombres_cols.append("Dest. Ficticio")
                for fila in c_mat:
                    fila.append(0.0)
            else:
                diff = sum_dem - sum_of
                self.txt_resultados.insert(tk.END, f"[!] PROBLEMA NO BALANCEADO: Demanda ({sum_dem:g}) > Oferta ({sum_of:g}).\n")
                self.txt_resultados.insert(tk.END, f" -> Se agregó 'Origen Ficticio' con oferta = {diff:g} y costos = 0.\n\n")
                of.append(diff)
                nombres_filas.append("Orig. Ficticio")
                c_mat.append([0.0] * len(dem))
        else:
            self.txt_resultados.insert(tk.END, f"[✓] PROBLEMA BALANCEADO (Oferta = Demanda = {sum_of:g}).\n\n")

        # --- 2. FASE 1: ESQUINA NOROESTE ---
        asig_nw, basicas_nw, costo_nw = self.esquina_noroeste(of, dem, c_mat)
        
        self.txt_resultados.insert(tk.END, "=== FASE 1: SOLUCIÓN INICIAL (MÉTODO ESQUINA NOROESTE) ===\n")
        self.imprimir_matriz(asig_nw, c_mat, nombres_filas, nombres_cols)
        self.txt_resultados.insert(tk.END, f"Costo Inicial (Esquina Noroeste): Z = ${costo_nw:,.2f}\n\n")
        
        # --- 3. FASE 2: OPTIMIZACIÓN (MÉTODO MODI / STEPPING STONE) ---
        asig_opt, costo_opt, iteraciones = self.optimizar_modi(asig_nw, basicas_nw, c_mat)
        
        self.txt_resultados.insert(tk.END, f"=== FASE 2: SOLUCIÓN ÓPTIMA (MÉTODO MODI - {iteraciones} iteraciones) ===\n")
        self.imprimir_matriz(asig_opt, c_mat, nombres_filas, nombres_cols)
        self.txt_resultados.insert(tk.END, f"COSTO MÍNIMO ÓPTIMO: Z = ${costo_opt:,.2f}\n")
        ahorro = costo_nw - costo_opt
        if ahorro > 0:
            self.txt_resultados.insert(tk.END, f"Ahorro respecto a Esquina Noroeste: ${ahorro:,.2f}\n")

    def esquina_noroeste(self, oferta, demanda, costos):
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
            
            # Manejo de degeneración cuando oferta y demanda se agotan simultáneamente
            if abs(of[i]) < 1e-9 and abs(dem[j]) < 1e-9:
                if i < m - 1:
                    basicas.add((i + 1, j)) # Variable básica con valor 0
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

    def optimizar_modi(self, asignacion_ini, basicas_ini, costos):
        m, n = len(costos), len(costos[0])
        asig = [list(fila) for fila in asignacion_ini]
        basicas = set(basicas_ini)
        
        iteracion = 0
        while iteracion < 100:
            # Asegurar m + n - 1 variables básicas (caso degenerado)
            while len(basicas) < m + n - 1:
                agregado = False
                for r in range(m):
                    for c in range(n):
                        if (r, c) not in basicas and not self.encuentra_ciclo(basicas, (r, c)):
                            basicas.add((r, c))
                            agregado = True
                            break
                    if agregado:
                        break
                        
            # 1. Calcular multiplicadores u y v (u_i + v_j = c_ij para celdas básicas)
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
            
            # 2. Calcular costos marginales para celdas no básicas (d_ij = c_ij - u_i - v_j)
            min_d = 0.0
            celda_entrante = None
            for r in range(m):
                for c in range(n):
                    if (r, c) not in basicas:
                        d = costos[r][c] - u[r] - v[c]
                        if d < min_d - 1e-6:
                            min_d = d
                            celda_entrante = (r, c)
                            
            # Si todos los d_ij >= 0, hemos llegado al óptimo
            if celda_entrante is None:
                break
                
            # 3. Encontrar el ciclo cerrado (Stepping-Stone) para la celda entrante
            ciclo = self.encuentra_ciclo(basicas, celda_entrante)
            if not ciclo:
                break
                
            # Las posiciones impares en el ciclo son las celdas donantes (-)
            celdas_menos = [ciclo[k] for k in range(1, len(ciclo), 2)]
            theta = min(asig[r][c] for (r, c) in celdas_menos)
            
            # Seleccionar la celda que sale de la base
            celda_saliente = next((r, c) for (r, c) in celdas_menos if abs(asig[r][c] - theta) < 1e-9)
            
            # Actualizar asignaciones a lo largo del ciclo
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

    def encuentra_ciclo(self, basicas, inicio):
        """Busca un ciclo ortogonal cerrado que alterne entre filas y columnas."""
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

    def imprimir_matriz(self, asig, costos, nom_filas, nom_cols):
        m, n = len(asig), len(asig[0])
        header = f"{'':15}" + "".join(f"{col:>16}" for col in nom_cols)
        self.txt_resultados.insert(tk.END, header + "\n" + "-" * len(header) + "\n")
        
        for i in range(m):
            linea = f"{nom_filas[i]:15}"
            for j in range(n):
                cant = asig[i][j]
                costo = costos[i][j]
                if cant > 1e-6:
                    celda_str = f"{cant:g} (${costo:g})"
                else:
                    celda_str = f"- (${costo:g})"
                linea += f"{celda_str:>16}"
            self.txt_resultados.insert(tk.END, linea + "\n")
        self.txt_resultados.insert(tk.END, "-" * len(header) + "\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = TransporteApp(root)
    root.mainloop()