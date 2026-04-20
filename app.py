import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --- DATOS DEL DOCENTE ---
DOCENTE_INFO = "MSc. Ing. Josué Loayza Díaz - CIP: 169617"
URL_HOJA = st.secrets["connections"]["spreadsheet"]["gsheets"]

class PDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(100)
        self.cell(0, 10, f'Página {self.page_no()} | {{nb}}', 0, 0, 'C')

st.set_page_config(page_title="Examen de Minas Pro", page_icon="⛏️")

if 'enviado' not in st.session_state:
    st.session_state.enviado = False

@st.cache_data
def cargar_preguntas():
    return pd.read_excel("preguntas.xlsx")

try:
    df_todo = cargar_preguntas()
except:
    st.error("No se encontró 'preguntas.xlsx'")
    st.stop()

# --- SEGURIDAD ---
CLAVE_CORRECTA = "123456789"
st.title("📝 Sistema de Evaluación de Ingeniería")
st.caption(f"Docente: {DOCENTE_INFO}")

password = st.text_input("Ingrese la clave del examen:", type="password")

if password == CLAVE_CORRECTA:
    apellidos = st.text_input("1. Apellidos Completos:", disabled=st.session_state.enviado)
    nombres = st.text_input("2. Nombres Completos:", disabled=st.session_state.enviado)
    id_alumno = st.text_input("3. ID del Alumno:", disabled=st.session_state.enviado)
    
    # NUEVO: Selección de Fila
    fila_seleccionada = st.selectbox("4. Seleccione su Fila (Según ubicación):", 
                                     [1, 2, 3, 4, 5, 6], 
                                     index=None,
                                     placeholder="Elija una opción...",
                                     disabled=st.session_state.enviado)

    st.divider()

    if fila_seleccionada:
        # Filtrar preguntas por fila
        df_preguntas = df_todo[df_todo['fila'] == fila_seleccionada].reset_index(drop=True)
        
        if df_preguntas.empty:
            st.warning(f"No hay preguntas cargadas para la Fila {fila_seleccionada} en el Excel.")
        else:
            st.subheader(f"Cuestionario - Fila {fila_seleccionada}")
            respuestas_usuario = []
            for i, fila in df_preguntas.iterrows():
                opciones = [f"a) {fila['a']}", f"b) {fila['b']}", f"c) {fila['c']}", f"d) {fila['d']}"]
                r = st.radio(f"{i+1}. {fila['pregunta']} ({fila['puntos']} pts)", opciones, index=None, key=f"p{i}", 
                             disabled=st.session_state.enviado)
                respuestas_usuario.append(r)

            if not st.session_state.enviado:
                if st.button("Finalizar Examen"):
                    if not apellidos or not nombres or not id_alumno or None in respuestas_usuario:
                        st.error("⚠️ Complete todos los datos y preguntas.")
                    else:
                        st.session_state.enviado = True
                        st.rerun()

            if st.session_state.enviado:
                puntos_obtenidos = 0
                puntos_maximos = df_preguntas['puntos'].sum()
                
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
                
                # Datos alumno e indicación de FILA
                pdf.set_text_color(0)
                pdf.set_font("Arial", 'B', 11)
                pdf.cell(35, 7, txt="ALUMNO:", ln=0)
                pdf.set_font("Arial", '', 11)
                pdf.cell(0, 7, txt=f"{apellidos.upper()}, {nombres.upper()}", ln=True)
                
                pdf.set_font("Arial", 'B', 11)
                pdf.cell(35, 7, txt="ID / CODIGO:", ln=0)
                pdf.set_font("Arial", '', 11)
                pdf.cell(0, 7, txt=f"{id_alumno}", ln=True)
                
                pdf.set_font("Arial", 'B', 11)
                pdf.cell(35, 7, txt="FILA ASIGNADA:", ln=0)
                pdf.set_font("Arial", '', 11)
                pdf.cell(0, 7, txt=f"{fila_seleccionada}", ln=True)
                
                pdf.ln(2)
                pdf.set_draw_color(200, 200, 200)
                pdf.line(25, pdf.get_y(), 185, pdf.get_y())
                pdf.ln(8)

                # Preguntas filtradas en PDF
                for i, fila in df_preguntas.iterrows():
                    letra_corr = str(fila['correcta']).strip().lower()
                    pts_pregunta = fila['puntos']
                    r_u = respuestas_usuario[i]
                    es_correcta = r_u.startswith(letra_corr)
                    
                    pdf.set_font("Arial", 'B', 10)
                    pdf.set_text_color(0)
                    pdf.multi_cell(0, 7, txt=f"{i+1}. {fila['pregunta']} ({pts_pregunta} pts)")
                    
                    pdf.set_font("Arial", '', 10)
                    if es_correcta:
                        puntos_obtenidos += pts_pregunta
                        pdf.set_text_color(0, 0, 255)
                        pdf.cell(0, 6, txt=f"   Respuesta: {r_u} [CORRECTO]", ln=True)
                    else:
                        pdf.set_text_color(220, 0, 0)
                        pdf.cell(0, 6, txt=f"   Respuesta: {r_u} [INCORRECTO]", ln=True)
                        pdf.set_text_color(0, 120, 0)
                        pdf.cell(0, 6, txt=f"   Correcta: {letra_corr}) {fila[letra_corr]}", ln=True)
                    pdf.ln(2)

                nota_final = round(puntos_obtenidos, 2)
                pdf.ln(5)
                
                # Recuadro Nota
                pdf.set_font("Arial", 'B', 12)
                pdf.set_text_color(0)
                pdf.cell(0, 12, txt="", border=1, ln=0)
                pdf.set_x(25)
                pdf.cell(95, 12, txt="PUNTAJE TOTAL OBTENIDO: ", ln=0, align='R')
                pdf.set_text_color(0,0,255) if nota_final >= 12 else pdf.set_text_color(220,0,0)
                pdf.cell(15, 12, txt=f"{nota_final}", ln=0, align='C')
                pdf.set_text_color(0)
                pdf.cell(20, 12, txt=f" / {puntos_maximos}", ln=True, align='L')
                
                pdf.ln(25)
                try: pdf.image("firma.png", x=85, y=pdf.get_y() - 14, w=40)
                except: pdf.ln(5)
                pdf.set_font("Arial", 'I', 8)
                pdf.cell(0, 5, txt="_______________________________________", ln=True, align='C')
                pdf.cell(0, 5, txt=f"{DOCENTE_INFO}", ln=True, align='C')

                st.warning("🔒 EXAMEN FINALIZADO")
                pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
                st.download_button("📥 Descargar Examen Fila " + str(fila_seleccionada), data=pdf_bytes, file_name=f"Examen_F{fila_seleccionada}_{id_alumno}.pdf")

elif password != "":
    st.error("❌ Clave incorrecta.")
