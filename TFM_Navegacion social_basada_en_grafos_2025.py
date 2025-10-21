# -*- coding: utf-8 -*-
""" Created on Tue May 6 08:29:07 2025 @author: Fran Campos """
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, PhotoImage
from tkVideoPlayer import TkinterVideo
from datetime import timedelta, datetime
import os
import webbrowser
from PIL import Image, ImageTk
import numpy as np
import math 
from navground.sim.ui.video import record_video_from_run
import yaml
import threading
from navground import sim, core
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tqdm import tqdm
sim.load_plugins()

def real_deadlocks_v2(run,steps_for_be_considered,modulation):
    """
   Calcula los agentes en estado deadlock de una simulacion y la devuelve en un np.array.

    Parameters:
        run sim.run(): Simulacion a la que se le calcula los agentes en estado deadlock.
        steps_for_be_considered (float): Numero de interaciones que el agente deba estar en estado deadlock para considerarlo finalmente.
        modulation(bool): Si se le aplica modulación o no

    Returns:
       deadlocks_agents (np.array): Array con valores de 1 y 0, si el agente esta o no en estado deadlock .
    """
    agents_poses = run.poses
    deadlocks_agents = []
    if modulation == True: # Si el conjunto de simulaciones tiene activada la modulacion es necesario tener encuenta el atributo state para saber si esta detenido porque esta esperando a otros agentes
        states = [agent.behavior.state for agent in run.world.agents]
    for agent in range(0,len(run.world.agents)):
        deadlock=0
        agent_poses_before = [0, 0, 0]
        steps_without_move=0
        for step in range(0,len(agents_poses)):
            distX = (agents_poses[step][agent][0] - agent_poses_before[0])**2 
            distY = (agents_poses[step][agent][1] - agent_poses_before[1])**2
            dist = math.sqrt(distX+distY) #Calculo de la distancia entre la posicion actual y la anterior
            actual_speed = dist/run.time_step #Calculo de la velocidad
            speed_considered = 1/100 #Velocidad maxima de un agente para considerarlo en estado deadlock
            if actual_speed < speed_considered: # Si la velocidad es menor a la considerada, determinamos que esta en estado deadlock una interación más 
                steps_without_move=steps_without_move+1 
            else:
                steps_without_move=0 # Si la velocidad NO es menor a la considerada, determinamos que YA NO esta en estado deadlock
            agent_poses_before = agents_poses[step][agent] # La posicion actual se convierte en la anterior
        if steps_without_move > steps_for_be_considered: # Si tiene mas interaciones en estado deadlock que lo considerado, se determina en estado deadlock permanente
            deadlock = 1
        if modulation == True: 
            if states[agent] == 1: # Si el agente esta esperadno a otros agentes no debe considerarse en estado deadlock
                deadlock = 0
        deadlocks_agents.append(deadlock)           
    return np.array(deadlocks_agents)   

def run_simulations(ventana,label,barra, yaml_data, num_runs):
    runs = {}
    for num_run in tqdm(range(num_runs), desc="Progress: "):
        label.config(text=f"Ejecutando simulación {num_run}/{num_runs}")
        barra["value"] = num_run  * 100 / num_runs
        ventana.update()
        experiment = sim.load_experiment(yaml_data)
        experiment.run(start_index=num_run)
        runs[num_run] = experiment.runs[num_run]
    barra["value"] = 100
    label.config(text="✅ Las simulaciones han sido ejecutadas con éxito")
    return runs

def get_data_from_yalm(yaml_data):
    data = {}
    data['num_runs'] = int(yaml_data.get('num_rums'))
    data['steps'] = int(yaml_data.get("steps"))
    data['time_step'] = float(yaml_data.get("time_step"))
    data['scenario'] = yaml_data.get("scenario", {}).get("type", [])
    data['num_agents'] = int(yaml_data.get("scenario", {}).get("groups", [])[0].get("number", 0))
    data['radio_agents'] = float(yaml_data.get("scenario", {}).get("groups", [])[0].get("radius", 0))
    data['max_speed'] = float(yaml_data.get("scenario", {}).get("groups", [])[0].get("kinematics", {}).get("max_speed"))
    data['behavior'] = yaml_data.get("scenario", {}).get("groups", [])[0].get("behavior", {}).get("type")
    data['optimal_speed'] = float(yaml_data.get("scenario", {}).get("groups", [])[0].get("behavior", {}).get("optimal_speed"))
    data['safety_margin'] = float(yaml_data.get("scenario", {}).get("groups", [])[0].get("behavior", {}).get("safety_margin"))
    data['modulation'] = yaml_data.get("scenario", {}).get("groups", [])[0].get("behavior", {}).get("modulations", [])[0].get("enabled", False)
    
    return data


window_width = 1024
window_height = 800

#Cargar las imagenes del fondo y el logo
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

background_path = resource_path("fondo.png")
background_image = Image.open(background_path)
background_photo = background_image.resize((window_width, window_height))

logo_path = resource_path("rexasi.png")
logo_image = Image.open(logo_path)
logo_photo = logo_image.resize((round(window_width), round(window_height*0.152)))


icon_path = resource_path("icon.png")

boton_path = resource_path("boton_sim.png")
boton_path2 = resource_path("boton_sim_2.png")

# Crear la ventana principal
root = tk.Tk()

def crear_ventana(window):
    window.title("Navground Program")  # Establecer el título de la ventana
    window.configure(bg="white")  # Establecer el fondo blanco
    # Definir el tamaño de la ventana

    # Obtener el tamaño de la pantalla
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window.resizable(False, False)
    # Calcular las coordenadas para centrar la ventana
    if window ==root:        
        x_position = (screen_width // 2) - (window_width // 2)
        y_position = (screen_height // 2) - (window_height // 2)
    else:
        x_position = root.winfo_x()
        y_position = root.winfo_y()
    # Establecer la geometría de la ventana con la posición centrada respecto de la ventana anterior
    window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
    # Establecer el fondo de la ventana   
    window.background_photo = ImageTk.PhotoImage(background_photo)
    background_label = tk.Label(window, image=window.background_photo)# Crear un Label para mostrar la imagen
    background_label.place(x=0, y=window_height*0.14)  # Posiciona la imagen en la esquina superior izquierda
    # Establecer el logo de la ventana    
    window.logo_photo = ImageTk.PhotoImage(logo_photo)
    logo_label = tk.Label(window, image=window.logo_photo)# Crear un Label para mostrar la imagen
    logo_label.pack(expand=True)
    logo_label.place(x=0, y=0)  # Posiciona la imagen en la esquina superior izquierda
    # Establecer el icono de la ventana
    window.tk.call('wm', 'iconphoto', window._w, PhotoImage(file=icon_path))

def volver(window):
    window.destroy()  # Cierra la nueva ventana
    root.deiconify()  # Muestra la ventana anterior

crear_ventana(root)
# Crear un frame centrado horizontalmente
frame = tk.Frame(root, bg="white")
frame.pack(expand=True)

# Función para cambiar el color al pasar el ratón y Función para volver al color original cuando el ratón sale
def resaltar(event):
    event.widget.config(bg="white", font=("Arial", 12, "bold"))  # Cambia el fondo y la fuente    
def quitar_resalto(event):
    event.widget.config(bg="white", font=("Arial", 12, "normal"))
    
def resaltar2(event):
    event.widget.config(bg="blue", font=("Arial", 18, "bold"))  # Cambia el fondo y la fuente
def quitar_resalto2(event):
    event.widget.config(bg="black", font=("Arial", 18, "normal")) 
    
def resaltar3(event):
    event.widget.config(bg="blue", font=("Arial", 12, "bold"))  # Cambia el fondo y la fuente
def quitar_resalto3(event):
    event.widget.config(bg="black", font=("Arial", 12, "normal")) 

#Opcion 1------------------------------------------------------------------------------------------------------------------------------------
def crear_yaml():
    root.iconify()
    crear_yaml_ventana = tk.Toplevel(root)
    crear_ventana(crear_yaml_ventana)
    
    btn_volver = tk.Button(crear_yaml_ventana, text="⬅ Volver", font=("Arial", 12), command=lambda: volver(crear_yaml_ventana))
    btn_volver.pack(anchor="nw", padx=50, pady=(130, 0)) # Ubicación en esquina superior izquierda
       
    frame_entradas = tk.Frame(crear_yaml_ventana, bg="#f0f0f0",width=30, bd=2, relief="solid")
    frame_entradas.pack(padx=0, pady=0)
    tk.Label(frame_entradas, text="Introduce los siguientes datos:", font=("Arial", 14, "bold")).pack(pady=(0,0))

    # Definir los nombres de los campos
    campos = ["Nº Simulaciones", "Nº Iteraciones", "time_step","Nº Agentes", "Max. Velocidad Agente", "Velocidad Optima Agente", "Radio Agente", "Margen de seguridad de los agentes", "Tipo de Behavior", "Escenario", "Modulacion"]   
    # Diccionario para almacenar entradas
    entradas = {}
    # Crear labels y entradas dentro del Frame
    for campo in campos:
        tk.Label(frame_entradas, text=campo, font=("Arial", 10, "bold"), bg="white",fg="blue", width=30).pack(pady=2)
        if(campo in ["Tipo de Behavior", "Escenario", "Modulacion"]):
            if (campo == "Tipo de Behavior"):
                opciones = ["HL","ORCA","SocialForce"]
            elif (campo == "Escenario"):
                opciones = ["Home","Bowtie","CrowdedCorridor", "MaltaCross"]
            else:
                opciones = ["NO", "SI"]
            combo = ttk.Combobox(frame_entradas, values=opciones, font=("Arial", 10), width=12)
            combo.pack(pady=1)
            combo.set(opciones[0])  # Establecer valor inicial
            entradas[campo] = combo  # Guardar referencia de cada campo
        else:
            entry = tk.Entry(frame_entradas, font=("Arial", 10), width=18)
            entry.pack(pady=1)
            entradas[campo] = entry  # Guardar referencia de cada campo
    
    # Función para obtener los datos ingresados
    def obtener_datos_yaml():
        datos = {campo: entrada.get() for campo, entrada in entradas.items()}
        args={}
        try:
            # Convertir y asignar valores con validación
            args['Nº Sim'] = int(datos['Nº Simulaciones']) if datos['Nº Simulaciones'] else 100
            args['Nº Ite'] = int(datos['Nº Iteraciones']) if datos['Nº Iteraciones'] else 1000
            args['t_step'] = float(datos['time_step']) if datos['time_step'] else 0.1
            args['Nº Agentes'] = int(datos['Nº Agentes']) if datos['Nº Agentes'] else 2
            args['Max. Vel. Agente'] = float(datos['Max. Velocidad Agente']) if datos['Max. Velocidad Agente'] else 1.0
            args['Vel. Opt. Agente'] = float(datos['Velocidad Optima Agente']) if datos['Velocidad Optima Agente'] else 1.0
            args['R. Agente'] = float(datos['Radio Agente']) if datos['Radio Agente'] else 0.25
            args['Margen seg'] = float(datos['Margen de seguridad de los agentes']) if datos['Margen de seguridad de los agentes'] else 0.1
            args['Behavior'] = datos['Tipo de Behavior']
            args['Escenario'] = datos['Escenario']
            args['Modulacion'] = False if datos['Modulacion'] in ["", "NO"] else True
        except ValueError:
            campo_error = next((campo for campo in datos if datos[campo] and not datos[campo].replace('.', '', 1).isdigit()), None)
            messagebox.showerror("Error de tipo", f" El valor ingresado en '{campo_error}' no es válido. Revisa el tipo de dato.")
            crear_yaml_ventana.deiconify()
            return  # Detiene la ejecución si hay error de conversión
       
        yaml= f"""num_runs: {args['Nº Sim']}
runs: 1
steps: {args['Nº Ite']}
time_step: {args['t_step']}
save_directory: ''
record_pose: true
record_twist: true
record_collisions: true
record_deadlocks: true
record_efficacy: true
scenario:
  type: {args['Escenario']}
  groups:
    -
      type: thymio
      number: {args['Nº Agentes']}
      radius: {args['R. Agente']}
      control_period: 0.1
      speed_tolerance: 0.01
      kinematics:
        type: 2WDiff
        wheel_axis: 0.6
        max_speed: {args['Max. Vel. Agente']}
      behavior:
        type: {args['Behavior']}
        optimal_speed: {args['Vel. Opt. Agente']}
        horizon: 5.0
        safety_margin: {args['Margen seg']}
        modulations:
        - type: Graphs
          enabled: {args['Modulacion']}
      state_estimation:
        type: Bounded
        range: 5.0
"""
        # Aquí puedes generar el archivo YAML con estos datos
        archivo_path = filedialog.asksaveasfilename(title="Guardar archivo YAML",
                                            defaultextension=".yaml",
                                            filetypes=[("Archivos YAML", "*.yaml"), ("Todos los archivos", "*.*")],
                                            parent=crear_yaml_ventana)
        if archivo_path:  # Si el usuario no cancela
            with open(archivo_path, "w", encoding="utf-8") as file:
                file.write(yaml)
            volver(crear_yaml_ventana)
            guardar_label = tk.Label(root, text=f"✅ Archivo guardado exitosamente.", font=("Arial", 12))
            guardar_label.pack(pady=20)
            root.after(8000, guardar_label.destroy)
    
     
    # Botón para capturar los datos
    imagen_2 = tk.PhotoImage(file=boton_path2)
    btn_datos = tk.Button(crear_yaml_ventana, text="Crear YAML", image=imagen_2, bg="black", compound="center", width=150, font=("Arial", 12), command=obtener_datos_yaml)
    btn_datos.bind("<Enter>", resaltar3)  # Cuando el ratón entra
    btn_datos.bind("<Leave>", quitar_resalto3)  # Cuando el ratón sale 
    btn_datos.place(relx=0.5, rely=0.96, anchor="center")  # Centrado respecto al eje X
    crear_yaml_ventana.mainloop()

#Opcion 2------------------------------------------------------------------------------------------------------------------------------------
def modificar_yaml():
    yalm_path2 = filedialog.askopenfilename(title="Selecciona un archivo YAML",
                                              filetypes=[("Archivos YAML", "*.yml;*.yaml"), ("Todos los archivos", "*.*")])
    if yalm_path2:  # Verificar si el usuario seleccionó un archivo
        with open( yalm_path2, "r", encoding="utf-8") as file:
            yaml_data2 = file.read()           
            data2 = yaml.safe_load(yaml_data2)

        #Obtener los datos del anterior yalm para mantener aquellos datos que no se cambiarán          
        modificar_yaml_ventana = tk.Toplevel(root)
        crear_ventana(modificar_yaml_ventana)
        
        btn_volver2 = tk.Button(modificar_yaml_ventana, text="⬅ Volver", font=("Arial", 12), command=lambda: volver(modificar_yaml_ventana))
        btn_volver2.pack(anchor="nw", padx=50, pady=(130, 0)) # Ubicación en esquina superior izquierda
        
        frame_entradas2 = tk.Frame(modificar_yaml_ventana, bg="#f0f0f0",width=30, bd=2, relief="solid")
        frame_entradas2.pack(padx=0, pady=0)
        tk.Label(frame_entradas2, text="Introduce los siguientes datos:", font=("Arial", 14, "bold")).pack(pady=(0,0))
    
        # Definir los nombres de los campos
        campos2 = ["Nº Simulaciones", "Nº Iteraciones", "time_step", "Nº Agentes", "Max. Velocidad Agente", "Velocidad Optima Agente", "Radio Agente", "Margen de seguridad de los agentes", "Behavior", "Escenario", "Modulacion"]
        
        # Diccionario para almacenar entradas
        entradas2 = {}
        
        # Crear labels y entradas dentro del Frame manteniendo en los desplegable el valor del anterior yalm
        for campo in campos2:
            tk.Label(frame_entradas2, text=campo, font=("Arial", 10, "bold"), bg="white",fg="blue", width=30).pack(pady=2)
            if(campo in ["Behavior", "Escenario", "Modulacion"]):
                if (campo == "Behavior"):
                    actual = data2['scenario']['groups'][0]['behavior']
                    opciones = ["ORCA","SocialForce"]                   
                elif (campo == "Escenario"):
                    actual = data2['scenario']['type']
                    opciones = ["Home","Bowtie","CrowdedCorridor", "MaltaCross"]
                else:
                    if data2['scenario']['groups'][0]['behavior']['modulations'][0]['enabled'] == True:
                        modulacion2 = "SI"
                    else: 
                        modulacion2 = "NO"
                    actual = modulacion2
                    opciones = ["NO", "SI"] 
                    
                if actual in opciones:
                    opciones.remove(actual)
                    opciones.insert(0, actual)  
                    
                combo = ttk.Combobox(frame_entradas2, values=opciones, font=("Arial", 10), width=12)
                combo.pack(pady=1)
                combo.set(opciones[0])  # Establecer valor inicial
                entradas2[campo] = combo  # Guardar referencia de cada campo
            else:
                entry = tk.Entry(frame_entradas2, font=("Arial", 10), width=18)
                entry.pack(pady=1)
                entradas2[campo] = entry  # Guardar referencia de cada campo
        
        # Función para obtener los datos ingresados
        def obtener_datos_yaml2():
            datos2 = {campo: entrada.get() for campo, entrada in entradas2.items()}
            try:             
                # Convertir y asignar valores con validación
                data2['num_runs'] = int(datos2['Nº Simulaciones']) if datos2['Nº Simulaciones'] else data2['num_runs']
                data2['steps']= int(datos2['Nº Iteraciones']) if datos2['Nº Iteraciones'] else data2["steps"]
                data2['time_step'] = float(datos2['time_step']) if datos2['time_step'] else data2["time_step"]
                data2['scenario']['groups'][0]['number'] = int(datos2['Nº Agentes']) if datos2['Nº Agentes'] else data2['scenario']['groups'][0]['number']               
                data2['scenario']['groups'][0]['kinematics']['max_speed'] = float(datos2['Max. Velocidad Agente']) if datos2['Max. Velocidad Agente'] else data2['scenario']['groups'][0]['kinematics']['max_speed']
                data2['scenario']['groups'][0]['behavior']['optimal_speed'] = float(datos2['Velocidad Optima Agente']) if datos2['Velocidad Optima Agente'] else data2['scenario']['groups'][0]['behavior']['optimal_speed']
                data2['scenario']['groups'][0]['radius'] = float(datos2['Radio Agente']) if datos2['Radio Agente'] else data2['scenario']['groups'][0]['radius']
                data2['scenario']['groups'][0]['behavior']['safety_margin'] = float(datos2['Margen de seguridad de los agentes']) if datos2['Margen de seguridad de los agentes'] else data2['scenario']['groups'][0]['behavior']['safety_margin']
                data2['scenario']['groups'][0]['behavior']['type'] = datos2["Behavior"]
                data2['scenario']['type'] = datos2["Escenario"]
                data2['scenario']['groups'][0]['behavior']['modulations'][0]['enabled'] = False if datos2['Modulacion'] == "NO" else True   
            except ValueError:
                campo_error = next((campo for campo in datos2 if datos2[campo] and not datos2[campo].replace('.', '', 1).isdigit()), None)
                messagebox.showerror("Error de tipo", f" El valor ingresado en '{campo_error}' no es válido. Revisa el tipo de dato.")
                root.iconify()
                modificar_yaml_ventana.deiconify()
                return  # Detiene la ejecución si hay error de conversión
              
            # Aquí puedes generar el archivo YAML con estos datos
            archivo_path = filedialog.asksaveasfilename(title="Guardar archivo YAML",
                                                defaultextension=".yaml",
                                                filetypes=[("Archivos YAML", "*.yaml"), ("Todos los archivos", "*.*")],
                                                parent=modificar_yaml_ventana)
            if archivo_path:  # Si el usuario no cancela
                with open(archivo_path, "w", encoding="utf-8") as file:
                    yaml.dump(data2, file, default_flow_style=False, allow_unicode=True)
                volver(modificar_yaml_ventana)
                guardar_label = tk.Label(root, text=f"✅ Archivo modificado guardado exitosamente.", font=("Arial", 12))
                guardar_label.pack(pady=20)
                root.after(8000, guardar_label.destroy)
                  
        # Botón para capturar los datos
        imagen_2 = tk.PhotoImage(file="boton_sim_2.png")
        btn_datos2 = tk.Button(modificar_yaml_ventana, text="Modificar YAML", image=imagen_2, bg="black", compound="center", width=150, font=("Arial", 12), command=obtener_datos_yaml2)
        btn_datos2.bind("<Enter>", resaltar3)  # Cuando el ratón entra
        btn_datos2.bind("<Leave>", quitar_resalto3)  # Cuando el ratón sale 
        btn_datos2.place(relx=0.5, rely=0.96, anchor="center")  # Centrado respecto al eje X
        modificar_yaml_ventana.mainloop()        

#Opcion 3------------------------------------------------------------------------------------------------------------------------------------
def simulacion_con_yaml():
    yalm_path = filedialog.askopenfilename(title="Selecciona un archivo YAML",
                                              filetypes=[("Archivos YAML", "*.yml;*.yaml"), ("Todos los archivos", "*.*")])
    if yalm_path:  # Verificar si el usuario seleccionó un archivo
        with open( yalm_path, "r", encoding="utf-8") as file:
            yaml_data = file.read()           #print (yaml_data[10:13])
            data = yaml.safe_load(yaml_data)
        num_runs = int(data.get("num_runs"))
        
        x_position = root.winfo_x()
        y_position = root.winfo_y()
        # Crear una nueva ventana en la misma posición
        ventana_progreso = tk.Toplevel(root)
        ventana_progreso.resizable(False, False)
        ventana_progreso.title("Progreso de Simulación")
        ventana_progreso.geometry(f"400x200+{x_position+312}+{y_position+300}")  # Mismo tamaño y posición
        ventana_progreso.tk.call('wm', 'iconphoto', ventana_progreso._w, PhotoImage(file="icon.png"))
        # Label para mostrar el progreso
        progreso_label = tk.Label(ventana_progreso, text="Iniciando simulaciones...", font=("Arial", 12))
        progreso_label.pack(pady=20)    
        # Barra de progreso
        barra = ttk.Progressbar(ventana_progreso, length=150, mode="determinate")
        barra.pack(pady=20)
        
        runs = run_simulations(ventana_progreso,progreso_label, barra, yaml_data, num_runs)
                 
       
        def ver_simulaciones():  
            ventana_progreso.destroy()
            reproductor = tk.Toplevel(root)
            crear_ventana(reproductor)
            
            btn_volver = tk.Button(reproductor, text="⬅ Volver", font=("Arial", 12), command=lambda: volver(reproductor))
            btn_volver.pack(anchor="nw", padx=50, pady=(130, 0)) # Ubicación en esquina superior izquierda
                        
            # Contenedor derecho para el reproductor de video
            reproductor.frame_grafica = tk.Frame(reproductor, width=380, height=650, bg="black", bd=2, relief="solid")
            reproductor.frame_grafica.place(x=600, y=140, width=380, height=650)
                           
            # Datos necesarios del archivo yaml       
            modulacion = data.get("scenario", {}).get("groups", [])[0].get("behavior", {}).get("modulations", [])[0].get("enabled", False)
            numeros_agentes = data.get("scenario", {}).get("groups", [])[0].get("number", 0)
            rango_agentes = range(int(numeros_agentes)+1)
            
            #Calcular los agentes en estado de deadlook
            deadlocks_2 = [sum(real_deadlocks_v2(run,(2/100)*len(run.poses),bool(modulacion))>0) for run in runs.values()]           
            collisions = [len(run.collisions) for run in runs.values()]
            
            # Crear la figura de matplotlib
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 12), dpi=90)  # Dos gráficos en una columna
            fig.subplots_adjust(top=0.95)
            fig.subplots_adjust(hspace=0.4) 
            # Primera gráfica: Deadlocks comparison
            freq = [deadlocks_2.count(a) for a in rango_agentes]
            x = np.arange(len(rango_agentes))
            ax1.bar(x - 0.1/numeros_agentes, freq, 1/numeros_agentes*2.25, color='blue', alpha=0.7) 
            ax1.set_xlabel('Agents stuck')
            ax1.set_ylabel('Frecuencia')
            ax1.set_title('Deadlocks v2')
            ax1.set_xticks(x)
            ax1.set_xticklabels(rango_agentes)  # Etiquetas de los valores            
            # Segunda gráfica: Boxplot de colisiones
            ax2.boxplot([collisions], labels=['ORCA'], patch_artist=True)
            ax2.set_title('Collisions')
            ax2.set_ylabel('Nº of collisions')
            ax2.grid(True)
            # Agregar la figura de Matplotlib al Frame de Tkinter
            canvas = FigureCanvasTkAgg(fig, master=reproductor.frame_grafica)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                        
            # Crear el nombre de la carpeta
            fecha_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            nombre_archivo = os.path.basename(yalm_path)
            nombre_sin_extension = os.path.splitext(nombre_archivo)[0]
            nombre_carpeta = f"{nombre_sin_extension}_{fecha_hora}"             
            ruta_carpeta = os.path.join(os.getcwd(), nombre_carpeta)  # Carpeta en la ubicación actual
            # Crear la carpeta si no existe
            os.makedirs(ruta_carpeta, exist_ok=True)    
            video_actual = 0    
            video_path = os.path.join(ruta_carpeta, f"video[{video_actual}].mp4")
            
            reproductor.frame_video = tk.Frame(reproductor, width=500, height=580, bg="black")
            reproductor.frame_video.place(x=50, y=200, width=500, height=580)
            
            reproductor.video_label = tk.Label(
                reproductor.frame_video,
                text="Video: Cargando ...",
                font=("Arial", 12, "bold"),
                fg="white",
                bg="black"
            )
            reproductor.video_label.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
                  
            # Contenedor para los controles debajo del video
            reproductor.frame_controls = tk.Frame(reproductor.frame_video, bg="#f0f0f0")
            reproductor.frame_controls.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
            
            # Crear el Label debajo de los controles
            reproductor.label_info = tk.Label(
                reproductor.frame_video,
                text=f"Agentes en Dead lock: {deadlocks_2[video_actual]} / Colisiones: {collisions[video_actual]}",
                font=("Arial", 12),
                fg="black",
                bg="#f0f0f0"
            )
            
            # Ubicarlo debajo de frame_controls
            reproductor.label_info.pack(fill=tk.X, pady=5)
        
            # Reproductor de Video en la izquierda
            scenario = data.get("scenario", {}).get("type", [])
            if (scenario=="Home"):
                reproductor.video_player = TkinterVideo(master=reproductor.frame_video, scaled=True)
                reproductor.video_player.pack(fill="both", expand=True)
                print("hola")
            else:
                reproductor.video_player = TkinterVideo(master=reproductor.frame_video, scaled=True, keep_aspect=True)
                reproductor.video_player.pack(fill="both", expand=True)
            reproductor.video_player.config(width=500, height=500)
                     

            def toggle_play_pause():
                """ Alternar entre Play y Pause """
                if reproductor.video_player.is_paused():
                    reproductor.video_player.play()
                    reproductor.play_pause_button.config(text="Pause ⏸", bg="#FF9800")
                else:
                    reproductor.video_player.pause()
                    reproductor.play_pause_button.config(text="Play ▶", bg="#4CAF50")
            
            def set_video_position(value):
                """ Ajustar la posición del video con la barra de progreso """
                #total_duration = reproductor.video_player.video_info()["duration"]
                #position = int((float(value) / 100) * total_duration)
                #reproductor.video_player.seek(position)
            
            def update_video_progress():
                """ Actualizar la barra de progreso mientras el video avanza """
                current_time = reproductor.video_player.current_duration()
                total_duration = reproductor.video_player.video_info()["duration"]           
                if total_duration > 0:
                    progress_percentage = (current_time / total_duration) * 100
                    reproductor.progress_bar.set(progress_percentage)          
                # Actualizar el tiempo mostrado
                current_time_str = str(timedelta(seconds=current_time))[:-3]
                total_duration_str = str(timedelta(seconds=total_duration))[:-3]
                reproductor.time_label.config(text=f"{current_time_str} / {total_duration_str}")
            
                # Llamar a la función cada segundo para actualizar la barra de desplazamiento
                reproductor.after(5, update_video_progress)
                               
            def cambiar_video(direccion):
                global video_actual, video_path
                # Reiniciar la barra de progreso
                reproductor.after_cancel(update_video_progress)
                reproductor.progress_bar.set(0)  
                reproductor.time_label.config(text="00:00:00 / 00:00:00")   
                # Mostrar mensaje de carga antes de cambiar el video
                reproductor.video_label.config(text="Cargando video...")                
                
                # Determinar el nuevo índice del video
                if direccion == "anterior":
                    video_actual = max(video_actual - 1, 0)
                elif direccion == "siguiente":
                    video_actual += 1
                else:
                    video_actual = 0
                # Mostrar datos antes de cambiar el video               
                reproductor.label_info.config(text=f"Agentes en Dead lock: {deadlocks_2[video_actual]} / Colisiones: {collisions[video_actual]}")
                video_path = os.path.join(ruta_carpeta, f"video[{video_actual}].mp4")
                # Si el archivo no existe, generarlo en un hilo separado
                if not os.path.exists(video_path):
                    def cargar_video():
                        record_video_from_run(path=video_path, run=runs[video_actual], factor=6.0, fps=30)
                        reproductor.video_player.load(video_path)
                        reproductor.video_player.play()
                        update_video_progress()
                        reproductor.play_pause_button.config(text="Pause ⏸", bg="#FF9800")
                        reproductor.video_label.config(text=f"video[{video_actual}].mp4")
                        
                        update_video_progress()
                    threading.Thread(target=cargar_video, daemon=True).start()
                else:
                    def cargar_video2():
                        reproductor.video_player.load(video_path)
                        reproductor.video_player.play()
                        update_video_progress()
                        reproductor.play_pause_button.config(text="Pause ⏸", bg="#FF9800")
                        reproductor.video_label.config(text=f"video[{video_actual}].mp4")                        
                        update_video_progress()
                    threading.Thread(target=cargar_video2, daemon=True).start()

            # Barra de progreso
            reproductor.progress_bar = tk.Scale(
            reproductor.frame_controls,
                from_=0,
                to=100,
                orient=tk.HORIZONTAL,
                length=300,
                showvalue=False,
                command=set_video_position,
            )
            reproductor.progress_bar.pack(fill=tk.X, padx=10, pady=5)

            # Etiqueta de tiempo
            reproductor.time_label = tk.Label(
                reproductor.frame_controls,
                text="00:00:00 / 00:00:00",
                font=("Arial", 12, "bold"),
                fg="#555555",
                bg="#f0f0f0",
            )
            reproductor.time_label.pack(pady=5)
                                    
            # Botón "Anterior"
            btn_anterior = tk.Button(reproductor.frame_controls, text="⏮ Anterior", font=("Arial", 12), command=lambda: cambiar_video("anterior"))
            btn_anterior.pack(side=tk.LEFT, padx=10)            
              
            # Botón "Siguiente"
            btn_siguiente = tk.Button(reproductor.frame_controls, text="⏭ Siguiente", font=("Arial", 12), command=lambda: cambiar_video("siguiente"))
            btn_siguiente.pack(side=tk.LEFT, padx=10)
                
            # Botón "Play/Pause"
            reproductor.play_pause_button = tk.Button(reproductor.frame_controls, text="Play ▶", font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", command=toggle_play_pause)
            reproductor.play_pause_button.pack(side=tk.LEFT, padx=10)

            cambiar_video(video_actual)  # Carga el primer video
            reproductor.mainloop()
            
        # Crear un frame para colocar los botones "Ver Simulaciones" y "Cancelar"
        botones_frame = tk.Frame(ventana_progreso)
        botones_frame.pack(pady=10)
        btn_ver = tk.Button(botones_frame, text="Ver simulaciones", font=("Arial", 12), command=ver_simulaciones)
        btn_ver.pack(side="left", padx=10)
        btn_cancelar = tk.Button(botones_frame, text="Cancelar", font=("Arial", 12), command=ventana_progreso.destroy)
        btn_cancelar.pack(side="left", padx=10)
        
        # Vincular eventos de hover
        btn_ver.bind("<Enter>", resaltar)  # Cuando el ratón entra
        btn_ver.bind("<Leave>", quitar_resalto)  # Cuando el ratón sale 
        btn_cancelar.bind("<Enter>", resaltar)  # Cuando el ratón entra
        btn_cancelar.bind("<Leave>", quitar_resalto)  # Cuando el ratón sale

#Opcion 4------------------------------------------------------------------------------------------------------------------------------------        
def comparacion_con_yamls():
    yalm_path = filedialog.askopenfilename(title="Selecciona un archivo YAML",
                                              filetypes=[("Archivos YAML", "*.yml;*.yaml"), ("Todos los archivos", "*.*")])
    if yalm_path:  # Verificar si el usuario seleccionó un archivo
        with open( yalm_path, "r", encoding="utf-8") as file:
            yaml_data = file.read()           
            data = yaml.safe_load(yaml_data)
        datos = get_data_from_yalm(data)

        x_position = root.winfo_x()
        y_position = root.winfo_y()
        # Crear una nueva ventana en la misma posición
        ventana_progreso = tk.Toplevel(root)
        ventana_progreso.resizable(False, False)
        ventana_progreso.title("Progreso de Simulación")
        ventana_progreso.geometry(f"400x200+{x_position+312}+{y_position+300}")  # Mismo tamaño y posición
        ventana_progreso.tk.call('wm', 'iconphoto', ventana_progreso._w, PhotoImage(file="icon.png"))
        # Label para mostrar el progreso
        progreso_label = tk.Label(ventana_progreso, text="Iniciando simulaciones...", font=("Arial", 12))
        progreso_label.pack(pady=20)    
        # Barra de progreso
        barra = ttk.Progressbar(ventana_progreso, length=150, mode="determinate")
        barra.pack(pady=20)
        
        runs = run_simulations(ventana_progreso,progreso_label,barra, yaml_data, datos['num_runs'])
          
        # Crear un frame para colocar los botones juntos
        botones_frame = tk.Frame(ventana_progreso)
        botones_frame.pack(pady=10)
             
        def comparacion_con_yamls2():        
            yalm_path2 = filedialog.askopenfilename(title="Selecciona un archivo YAML",
                                                      filetypes=[("Archivos YAML", "*.yml;*.yaml"), ("Todos los archivos", "*.*")])
            if yalm_path2:  # Verificar si el usuario seleccionó un archivo
                with open( yalm_path2, "r", encoding="utf-8") as file2:
                    yaml_data2 = file2.read()           #print (yaml_data[10:13])
                    data2 = yaml.safe_load(yaml_data2)
                datos2 = get_data_from_yalm(data2)
                
                # Crear una nueva ventana en la misma posición
                x_position2 = root.winfo_x()
                y_position2 = root.winfo_y()               
                ventana_progreso.destroy()
                ventana_progreso2 = tk.Toplevel(root)
                ventana_progreso2.resizable(False, False)
                ventana_progreso2.title("Progreso de Simulación")
                ventana_progreso2.geometry(f"400x200+{x_position2+312}+{y_position2+300}")  # Mismo tamaño y posición
                ventana_progreso2.tk.call('wm', 'iconphoto', ventana_progreso2._w, PhotoImage(file="icon.png"))
                # Label para mostrar el progreso
                progreso_label2 = tk.Label(ventana_progreso2, text="Iniciando simulaciones...", font=("Arial", 12))
                progreso_label2.pack(pady=20)    
                # Barra de progreso
                barra2 = ttk.Progressbar(ventana_progreso2, length=150, mode="determinate")
                barra2.pack(pady=20)
                
                runs2 = run_simulations(ventana_progreso2, progreso_label2, barra2, yaml_data2, datos2['num_runs'])
                
                # Crear un frame para colocar los botones juntos
                botones_frame2 = tk.Frame(ventana_progreso2)
                botones_frame2.pack(pady=10) 
                
                def comparar_simulaciones():                    
                    ventana_progreso2.destroy()
                    comparar_ventana = tk.Toplevel(root)
                    crear_ventana(comparar_ventana)
                
                    # Botón de volver
                    btn_volver = tk.Button(comparar_ventana, text="⬅ Volver", font=("Arial", 12), command=lambda: volver(comparar_ventana))
                    btn_volver.pack(anchor="nw", padx=50, pady=(130, 0))  # Ubicación en esquina superior izquierda
                    
                    # Calcular los los agentes en estado deadlock y las colisiones
                    deadlocks_v2 = [sum(real_deadlocks_v2(run, (2/100)*len(run.poses), bool(datos['modulation'])) > 0) for run in runs.values()]
                    collisions = [len(run.collisions) for run in runs.values()]
                                                    
                    deadlocks2_v2 = [sum(real_deadlocks_v2(run, (2/100)*len(run.poses), bool(datos2['modulation'])) > 0) for run in runs2.values()]
                    collisions2 = [len(run.collisions) for run in runs2.values()]
                    
                    nombre_archivo = os.path.basename(yalm_path)
                    nombre_sin_extension = os.path.splitext(nombre_archivo)[0]
                    nombre_archivo2 = os.path.basename(yalm_path2)
                    nombre_sin_extension2 = os.path.splitext(nombre_archivo2)[0]
                    
                    #Contenedor izquierdo para la gráfica de Deadlocks
                    comparar_ventana.frame_grafica_izquierda = tk.Frame(comparar_ventana, width=450, height=450, bg="black", bd=2, relief="solid")
                    comparar_ventana.frame_grafica_izquierda.place(x=40, y=180, width=450, height=450)
                    
                    #Contenedor derecho para la gráfica de colisiones
                    comparar_ventana.frame_grafica_derecha = tk.Frame(comparar_ventana, width=450, height=450, bg="black", bd=2, relief="solid")
                    comparar_ventana.frame_grafica_derecha.place(x=550, y=180, width=450, height=450)
                    
                    #Gráfica de Deadlocks (Izquierda)
                    fig_izquierda, ax1_izquierda = plt.subplots(figsize=(8, 8), dpi=90)
                    fig_izquierda.subplots_adjust(top=0.90)
                                        
                    rango_agentes = range(int(datos['num_agents'])+1)                
                    rango_agentes2 = range(int(datos2['num_agents'])+1)               
                    freq1 = [deadlocks_v2.count(a) for a in rango_agentes]
                    freq2 = [deadlocks2_v2.count(a) for a in rango_agentes2]
                    x1 = np.arange(len(rango_agentes))
                    x2 = np.arange(len(rango_agentes2))
                                     
                    ax1_izquierda.bar(x1 - 0.2, freq1, 0.4, label=nombre_sin_extension, color='blue', alpha=0.7)
                    ax1_izquierda.bar(x2 + 0.2, freq2, 0.4, label=nombre_sin_extension2, color='red', alpha=0.7)
                    ax1_izquierda.set_xlabel('Agents stuck')
                    ax1_izquierda.set_ylabel('Frecuencia')
                    ax1_izquierda.set_title('Deadlocks v2 - Comparación')
                    ax1_izquierda.set_xticks(x1)
                    ax1_izquierda.set_xticklabels(rango_agentes)
                    ax1_izquierda.legend()
                    
                    #Gráfica de Colisiones (Derecha)
                    fig_derecha, ax2_derecha = plt.subplots(figsize=(8, 8), dpi=90)
                    fig_derecha.subplots_adjust(top=0.90)
                    
                    ax2_derecha.boxplot([collisions, collisions2], labels=[nombre_sin_extension, nombre_sin_extension2], patch_artist=True)
                    ax2_derecha.set_title('Collisions Comparison')
                    ax2_derecha.set_ylabel('Nº of collisions')
                    ax2_derecha.grid(True)
                    
                    #Agregar las figuras a los Frames en Tkinter
                    canvas_izquierda = FigureCanvasTkAgg(fig_izquierda, master=comparar_ventana.frame_grafica_izquierda)
                    canvas_izquierda.draw()
                    canvas_izquierda.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                    
                    canvas_derecha = FigureCanvasTkAgg(fig_derecha, master=comparar_ventana.frame_grafica_derecha)
                    canvas_derecha.draw()
                    canvas_derecha.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                    
                    frame_label = tk.Frame(comparar_ventana, bg="#f0f0f0")
                    frame_label.place(x=120, y=650, width=800, height=120)  # Ajusta la posición y tamaño según necesites
                    #Crear el Label con información en dos líneas
                    label_info = tk.Label(
                        frame_label,
                        text=f"{nombre_sin_extension}: Iteraciones: {datos['steps']}, time_step: {datos['time_step']}, Nº Agentes: {datos['num_agents']}, Rad.Agent: {datos['radio_agents']}, Esce.: {datos['scenario']} \n                    Vel. Opt: {datos['max_speed']}, Behavior: {datos['behavior']}, Vel. Opt: {datos['optimal_speed']}, Margen de seg: {datos['safety_margin']}, Mod.: {datos['modulation']} \n\n{nombre_sin_extension2}: Iteraciones: {datos2['steps']}, time_step: {datos2['time_step']}, Nº Agentes: {datos2['num_agents']}, Rad.Agent: {datos2['radio_agents']}, Esce.: {datos2['scenario']} \n                    Vel. Opt: {datos2['max_speed']}, Behavior: {datos2['behavior']}, Vel. Opt: {datos2['optimal_speed']}, Margen de seg: {datos2['safety_margin']}, Mod.: {datos2['modulation']}",
                        font=("Arial", 12,"bold"),
                        fg="black",
                        bg="#f0f0f0",
                        justify="left"
                    )
                    label_info.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

                    
                # Botones "Ver comparación" y "Cancelar"
                btn_ver2 = tk.Button(botones_frame2, text="Ver comparación", font=("Arial", 12), command=comparar_simulaciones)
                btn_ver2.pack(side="left", padx=10)
                btn_cancelar2 = tk.Button(botones_frame2, text="Cancelar", font=("Arial", 12), command=ventana_progreso2.destroy)
                btn_cancelar2.pack(side="left", padx=10)    
                
                # Vincular eventos de hover
                btn_ver2.bind("<Enter>", resaltar)  # Cuando el ratón entra
                btn_ver2.bind("<Leave>", quitar_resalto)  # Cuando el ratón sale 
                btn_cancelar2.bind("<Enter>", resaltar)  # Cuando el ratón entra
                btn_cancelar2.bind("<Leave>", quitar_resalto)  # Cuando el ratón sale  
            
            
        # Botones "Elegir el otro archivo" y "Cancelar"
        btn_ver = tk.Button(botones_frame, text="Elegir el otro archivo", font=("Arial", 12), command=comparacion_con_yamls2)
        btn_ver.pack(side="left", padx=10)
        btn_cancelar = tk.Button(botones_frame, text="Cancelar", font=("Arial", 12), command=ventana_progreso.destroy)
        btn_cancelar.pack(side="left", padx=10)
        
        # Vincular eventos de hover
        btn_ver.bind("<Enter>", resaltar)  # Cuando el ratón entra
        btn_ver.bind("<Leave>", quitar_resalto)  # Cuando el ratón sale 
        btn_cancelar.bind("<Enter>", resaltar)  # Cuando el ratón entra
        btn_cancelar.bind("<Leave>", quitar_resalto)  # Cuando el ratón sale    
        
#Opcion 5------------------------------------------------------------------------------------------------------------------------------------
def abrir_pagina():
    url = "https://idsia-robotics.github.io/navground/0.5/introduction.html"
    webbrowser.open(url)
#--------------------------------------------------------------------------------------------------------------------------------------------

    
# Crear los botones y centrarlos
imagen = tk.PhotoImage(file=boton_path)
btn1 = tk.Button(root, text="Crear archivo yaml", image=imagen, bg="black", compound="center", width=355, font=("Arial", 18), command=crear_yaml)
btn2 = tk.Button(root, text="Modificar archivo yaml", image=imagen, bg="black", compound="center", width=355, font=("Arial", 18), command=modificar_yaml)
btn3 = tk.Button(root, text="Simulacion mediante yaml", image=imagen, bg="black", compound="center", width=355, font=("Arial", 18), command=simulacion_con_yaml)
btn4 = tk.Button(root, text="Comparar simulaciones", image=imagen, bg="black", compound="center", width=355, font=("Arial", 18), command=comparacion_con_yamls)
btn5 = tk.Button(root, text="Ayuda", image=imagen, bg="black", compound="center", width=355, font=("Arial", 18),command=abrir_pagina)

# Vincular eventos de hover
r=0.4
for btn in [btn1,btn2,btn3,btn4,btn5]:
    btn.bind("<Enter>", resaltar2)  # Cuando el ratón entra
    btn.bind("<Leave>", quitar_resalto2)  # Cuando el ratón sale 
    btn.place(relx=0.5, rely=r, anchor="center")  # Centrado respecto al eje X
    r=r+0.1


# Ejecutar el bucle principal de la aplicación
root.mainloop()