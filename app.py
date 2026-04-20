import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- DATOS DEL DOCENTE ---
DOCENTE_INFO = "MSc. Ing. Josué Loayza Díaz - CIP: 169617"

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Examen de Minas Pro", page_icon="⛏️")

# --- CLASE PARA EL FOLIO DEL PDF ---
class PDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(100)
        self.cell(0, 10, f'Página {self.page_no()} | {{nb}}', 0, 0, 'C')

# --- MEMORIA DEL SISTEMA ---
if 'enviado' not in st.session_state:
    st.session_state.enviado = False

# --- CARGAR PREGUNTAS DESDE EXCEL ---
@st.cache_data
def cargar_preguntas():
    return pd.read_excel("preguntas.xlsx")

try:
    df_todo = cargar_preguntas()
except:
    st.error("⚠️ Error: No se encontró 'preguntas.xlsx' en la carpeta.")
    st.stop()

# --- INTERFAZ PRINCIPAL ---
st.title("📝 Ingeniería de Minas UCSM - Mecánica de Rocas I")
st.caption(f"Docente: {DOCENTE_INFO}")

# Seguridad
CLAVE_CORRECTA = "123456789"
if not st.session_state.enviado:
    password = st.text_input("Ingrese la clave del examen para comenzar:", type="password")
else:
    password = CLAVE_CORRECTA

if password == CLAVE_CORRECTA:
    # Datos del Alumno
    apellidos = st.text_input("1. Apellidos Completos:", disabled=st.session_state.enviado).upper()
    nombres = st.text_input("2. Nombres Completos:", disabled=st.session_state.enviado).upper()
    id_alumno = st.text_input("3. ID del Alumno (Código):", disabled=st.session_state.enviado)
    
    fila_sel = st.selectbox("4. Seleccione su Fila (Ubicación):", 
                             [1, 2, 3, 4, 5, 6], 
                             index=None, 
                             placeholder="Elija una fila...",
                             disabled=st.session_state.enviado)

    st.divider()

    if fila_sel:
        # Filtrar preguntas por fila
        df_preguntas = df_todo[df_todo['fila'] == fila_sel].reset_index(drop=True)
        
        if df_preguntas.empty:
            st.warning(f"No hay preguntas configuradas para la Fila {fila_sel} en el Excel.")
        else:
            st.subheader(f"Cuestionario - Fila {fila_sel}")
            respuestas_usuario = []
            
            for i, fila in df_preguntas.iterrows():
                opciones = [f"a) {fila['a']}", f"b) {fila['b']}", f"c) {fila['c']}", f"d) {fila['d']}"]
                r = st.radio(f"{i+1}. {fila['pregunta']} ({fila['puntos']} pts)", 
                             opciones, index=None, key=f"p{i}", disabled=st.session_state.enviado)
                respuestas_usuario.append(r)

            # Botón de Finalizar
            if not st.session_state.enviado:
                if st.button("Finalizar Examen"):
                    if not apellidos or not nombres or not id_alumno or None in respuestas_usuario:
                        st.error("⚠️ Por favor, complete todos sus datos y responda todas las preguntas.")
                    else:
                        # Cálculo de puntos
                        puntos_obtenidos = 0
                        for i, r_u in enumerate(respuestas_usuario):
                            letra_corr = str(df_preguntas.iloc[i]['correcta']).strip().lower()
                            if r_u.startswith(letra_corr):
                                puntos_obtenidos += df_preguntas.iloc[i]['puntos']
                        
                        # --- GUARDAR EN GOOGLE SHEETS ---
                        try:
                            conn = st.connection("gsheets", type=GSheetsConnection)
                            url_hoja = st.secrets["connections"]["gsheets"]["spreadsheet"]
                            existentes = conn.read(spreadsheet=url_hoja)
                            
                            nueva_fila = pd.DataFrame([{
                                "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "ID": id_alumno,
                                "Apellidos": apellidos,
                                "Nombres": nombres,
                                "Fila": fila_sel,
                                "Nota": puntos_obtenidos
                            }])
                            
                            actualizada = pd.concat([existentes, nueva_fila], ignore_index=True)
                            conn.update(spreadsheet=url_hoja, data=actualizada)
                            st.toast("✅ Nota registrada en base de datos")
                        except Exception as e:
                            st.warning(f"Nota procesada localmente (Sin conexión a nube)")

                        st.session_state.enviado = True
                        st.rerun()

            # --- VISTA POST-EXAMEN (PDF) ---
            if st.session_state.enviado:
                puntos_max = df_preguntas['puntos'].sum()
                pts_final = 0
                
                # Crear PDF
                pdf = PDF(unit='mm', format='A4')
                pdf.alias_nb_pages()
                pdf.set_margins(left=25, top=25, right=25)
                pdf.add_page()
                
                # Encabezado
                pdf.set_font("Arial", 'B', 14)
                pdf.cell(0, 10, txt="EXAMEN DE INGENIERIA DE MINAS", ln=True, align='C')
                pdf.set_font("Arial", 'I', 10)
                pdf.cell(0, 5, txt=f"Docente: {DOCENTE_INFO}", ln=True, align='C')
                pdf.set_draw_color(180, 180, 180)
                pdf.line(25, 48, 185, 48)
                pdf.ln(12)
                
                # Datos Alumno
                pdf.set_font("Arial", 'B', 11)
                pdf.cell(35, 7, txt="ALUMNO:", ln=0)
                pdf.set_font("Arial", '', 11)
                pdf.cell(0, 7, txt=f"{apellidos}, {nombres}", ln=True)
                pdf.set_font("Arial", 'B', 11)
                pdf.cell(35, 7, txt="ID / CODIGO:", ln=0)
                pdf.set_font("Arial", '', 11)
                pdf.cell(0, 7, txt=f"{id_alumno}", ln=True)
                pdf.set_font("Arial", 'B', 11)
                pdf.cell(35, 7, txt="FILA:", ln=0)
                pdf.set_font("Arial", '', 11)
                pdf.cell(0, 7, txt=f"{fila_sel}", ln=True)
                
                pdf.ln(2)
                pdf.line(25, pdf.get_y(), 185, pdf.get_y())
                pdf.ln(8)

                # Detalle de Preguntas
                for i, fila in df_preguntas.iterrows():
                    l_corr = str(fila['correcta']).strip().lower()
                    r_u = respuestas_usuario[i]
                    es_ok = r_u.startswith(l_corr)
                    
                    pdf.set_font("Arial", 'B', 10)
                    pdf.set_text_color(0)
                    pdf.multi_cell(0, 7, txt=f"{i+1}. {fila['pregunta']} ({fila['puntos']} pts)")
                    
                    pdf.set_font("Arial", '', 10)
                    if es_ok:
                        pts_final += fila['puntos']
                        pdf.set_text_color(0, 0, 255) # Azul
                        pdf.cell(0, 6, txt=f"   Respuesta: {r_u} [CORRECTO]", ln=True)
                    else:
                        pdf.set_text_color(220, 0, 0) # Rojo
                        pdf.cell(0, 6, txt=f"   Respuesta: {r_u} [INCORRECTO]", ln=True)
                        pdf.set_text_color(0, 120, 0) # Verde
                        pdf.cell(0, 6, txt=f"   Respuesta Correcta: {l_corr}) {fila[l_corr]}", ln=True)
                    pdf.ln(2)

                # Recuadro de Nota
                pdf.ln(5)
                pdf.set_font("Arial", 'B', 12)
                pdf.set_text_color(0)
                pdf.cell(0, 12, txt="", border=1, ln=0)
                pdf.set_x(25)
                pdf.cell(95, 12, txt="PUNTAJE TOTAL OBTENIDO: ", ln=0, align='R')
                pdf.set_text_color(0, 0, 255) if pts_final >= 12 else pdf.set_text_color(220, 0, 0)
                pdf.cell(15, 12, txt=f"{pts_final}", ln=0, align='C')
                pdf.set_text_color(0)
                pdf.cell(20, 12, txt=f" / {puntos_max}", ln=True, align='L')
                
                # Firma
                pdf.ln(20)
                try:
                    pdf.image("firma.png", x=85, y=pdf.get_y() - 14, w=40)
                except:
                    pdf.ln(5)
                pdf.set_font("Arial", 'I', 8)
                pdf.cell(0, 5, txt="_______________________________________", ln=True, align='C')
                pdf.cell(0, 5, txt=f"{DOCENTE_INFO}", ln=True, align='C')

                st.warning("🔒 EXAMEN FINALIZADO")
                st.markdown(f"### Nota Final: {pts_final} / {puntos_max}")
                
                pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
                st.download_button("📥 Descargar Examen Oficial (PDF)", 
                                   data=pdf_bytes, 
                                   file_name=f"Examen_F{fila_sel}_{id_alumno}.pdf")

elif password != "":
    st.error("❌ Clave incorrecta. Solicite el acceso al docente.")
