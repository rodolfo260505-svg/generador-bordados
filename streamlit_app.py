import streamlit as st
import pyembroidery
from PIL import Image
import tempfile
import os

# --- Configuración de la página ---
st.set_page_config(page_title="Auto-Digitizing Web App", page_icon="🧵", layout="wide")

st.title("🧵 Generador Automático de Bordados")
st.write("Sube una imagen (idealmente en blanco y negro o siluetas), ajusta el tamaño, previsualiza la ruta de las puntadas y descarga tu archivo `.pes`.")

# --- Interfaz en Columnas ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Configuración")
    uploaded_file = st.file_uploader("Sube tu imagen (PNG, JPG)", type=["png", "jpg", "jpeg"])
    width_mm = st.slider("Ancho final del bordado (mm)", min_value=10, max_value=200, value=50)

if uploaded_file is not None:
    with col1:
        # Mostrar la imagen original que subió el usuario
        image = Image.open(uploaded_file)
        st.image(image, caption="Imagen Original", use_container_width=True)

    # Botón de acción
    if st.button("Generar Puntadas y Previsualización", type="primary"):
        with st.spinner("Procesando imagen y calculando puntadas..."):
            try:
                # --- 1. PROCESAMIENTO DE IMAGEN ---
                img = image.convert('L') # Escala de grises
                scale = width_mm / img.width
                new_width = int(img.width * scale * 10)
                new_height = int(img.height * scale * 10)
                
                img = img.resize((new_width, new_height), Image.Resampling.NEAREST)
                pixels = img.load()

                # --- 2. GENERACIÓN DEL PATRÓN ---
                pattern = pyembroidery.EmbPattern()
                pattern.add_thread({"color": 0x000000, "description": "Black"})

                stitch_length = 20 # Longitud de puntada
                
                for y in range(new_height):
                    for x in range(new_width):
                        # Detectar píxeles oscuros
                        if pixels[x, y] < 128:
                            pattern.add_stitch_absolute(pyembroidery.STITCH, x * stitch_length, y * stitch_length)
                    # Salto al cambiar de fila
                    pattern.add_command(pyembroidery.TRIM)

                # --- 3. ARCHIVOS TEMPORALES (MEMORIA) ---
                # Usamos archivos temporales para que pyembroidery los escriba sin saturar el disco
                
                # Crear SVG para Previsualización
                with tempfile.NamedTemporaryFile(delete=False, suffix=".svg") as tmp_svg:
                    pyembroidery.write_svg(pattern, tmp_svg.name)
                    with open(tmp_svg.name, "r") as f:
                        svg_content = f.read()
                
                # Crear PES para Descarga
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pes") as tmp_pes:
                    pyembroidery.write_pes(pattern, tmp_pes.name)
                    with open(tmp_pes.name, "rb") as f:
                        pes_data = f.read()

                # Limpieza de temporales
                os.remove(tmp_svg.name)
                os.remove(tmp_pes.name)

                # --- 4. MOSTRAR RESULTADOS ---
                with col2:
                    st.subheader("2. Previsualización del Hilo")
                    # Renderizar el SVG directamente en Streamlit
                    st.components.v1.html(f"<div style='text-align:center;'>{svg_content}</div>", height=400, scrolling=True)
                    
                    st.success("¡Procesamiento completado con éxito!")
                    
                    # Botón para descargar el PES
                    st.download_button(
                        label="⬇️ Descargar archivo para bordadora (.PES)",
                        data=pes_data,
                        file_name="mi_bordado.pes",
                        mime="application/octet-stream"
                    )

            except Exception as e:
                st.error(f"Ocurrió un error al procesar la imagen: {e}")
