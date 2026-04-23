import pandas as pd
import streamlit as st

st.set_page_config(page_title="Comparador SEPA", layout="wide")

@st.cache_data
def cargar_datos():
    # Ahora cargamos el archivo liviano que ya tiene todo procesado
    return pd.read_csv('base_optimizada.csv')

st.title("⚖️ Comparador de Precios: Coto vs Día vs Carrefour")

df = cargar_datos()

col1, col2 = st.columns(2)
with col1:
    buscar_nombre = st.text_input("🔍 Producto", placeholder="Ej: PRESERVATIVOS")
with col2:
    buscar_marca = st.text_input("🏷️ Marca", placeholder="Ej: PRIME")

df_f = df.copy()
if buscar_nombre:
    df_f = df_f[df_f['productos_descripcion'].str.contains(buscar_nombre.upper(), na=False)]
if buscar_marca:
    df_f = df_f[df_f['productos_marca'].str.contains(buscar_marca.upper(), na=False)]

st.subheader(f"Mostrando {len(df_f)} resultados")

st.dataframe(
    df_f,
    column_config={
        "id_producto": "EAN",
        "productos_descripcion": "Producto",
        "productos_marca": "Marca",
        "Carrefour": st.column_config.NumberColumn("Carrefour", format="$ %.2f"),
        "Coto": st.column_config.NumberColumn("Coto", format="$ %.2f"),
        "Día": st.column_config.NumberColumn("Día", format="$ %.2f"),
        "Mejor_Precio": st.column_config.NumberColumn("Min", format="$ %.2f"),
        "Dispersion_Porcentaje": st.column_config.NumberColumn("Dispersión %", format="%.1f%%")
    },
    use_container_width=True,
    hide_index=True
)