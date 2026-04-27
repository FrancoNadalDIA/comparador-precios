import pandas as pd
import streamlit as st

st.set_page_config(page_title="Monitor de Precios SEPA", layout="wide")


@st.cache_data
def cargar_datos():
    # Cargamos el histórico
    df = pd.read_csv('base_optimizada.csv')
    # Nos aseguramos de que la fecha sea tratada correctamente
    return df


st.title("📊 Inteligencia de Precios: Seguimiento por Producto")

df = cargar_datos()

# Pestañas
tab1, tab2 = st.tabs(["🔍 Comparador Actual", "📈 Evolución por Producto Único"])

with tab1:
    ultima_fecha = df['fecha'].unique()[-1]
    st.info(f"Datos del día: **{ultima_fecha}**")

    df_hoy = df[df['fecha'] == ultima_fecha]

    c1, c2 = st.columns(2)
    with c1:
        b_nom = st.text_input("🔍 Buscar Producto", placeholder="Ej: ACEITE GIRASOL", key="bus1")
    with c2:
        b_mar = st.text_input("🏷️ Buscar Marca", placeholder="Ej: NATURA", key="bus2")

    df_f = df_hoy.copy()
    if b_nom:
        df_f = df_f[df_f['productos_descripcion'].str.contains(b_nom.upper(), na=False)]
    if b_mar:
        df_f = df_f[df_f['productos_marca'].str.contains(b_mar.upper(), na=False)]

    st.dataframe(df_f, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Historial de Precios por Código de Barras (EAN)")
    st.markdown("Seleccioná un producto específico para ver cómo varió su precio en cada cadena.")

    # 1. Buscador para encontrar el producto específico
    col_a, col_b = st.columns(2)
    with col_a:
        search_term = st.text_input("1️⃣ Buscá el producto para trackear:", placeholder="Ej: COCA COLA 1.5")

    # Filtramos la lista de productos únicos para el selector
    productos_unicos = df[['id_producto', 'productos_descripcion', 'productos_marca']].drop_duplicates()

    if search_term:
        productos_unicos = productos_unicos[
            productos_unicos['productos_descripcion'].str.contains(search_term.upper(), na=False) |
            productos_unicos['productos_marca'].str.contains(search_term.upper(), na=False)
            ]

    # 2. Selector del producto final (mostramos descripción + marca)
    if not productos_unicos.empty:
        opciones = productos_unicos.apply(
            lambda x: f"{x['id_producto']} - {x['productos_descripcion']} ({x['productos_marca']})", axis=1).tolist()
        seleccion = st.selectbox("2️⃣ Seleccioná el producto exacto:", options=opciones)

        # Extraemos el EAN de la selección
        ean_seleccionado = seleccion.split(" - ")[0]

        # 3. Filtramos TODO el historial para ese EAN
        df_track = df[df['id_producto'].astype(str) == ean_seleccionado].sort_values('fecha')

        if not df_track.empty:
            st.write(f"### Evolución de: {seleccion}")

            # Preparamos los datos para el gráfico
            chart_data = df_track.set_index('fecha')[['Carrefour', 'Coto', 'Día']]

            # Dibujamos el gráfico
            st.line_chart(chart_data)

            # Tabla de detalles
            st.write("### Tabla de variaciones")
            st.dataframe(
                chart_data.style.format("$ {:.2f}"),
                use_container_width=True
            )

            # Cálculo de aumento porcentual desde la primera fecha a la última
            if len(df_track) > 1:
                st.write("#### Variación total por cadena (desde el inicio del trackeo):")
                c1, c2, c3 = st.columns(3)
                for i, super_name in enumerate(['Carrefour', 'Coto', 'Día']):
                    precios = df_track[super_name].values
                    variacion = ((precios[-1] - precios[0]) / precios[0] * 100)
                    with [c1, c2, c3][i]:
                        st.metric(label=f"Suba en {super_name}", value=f"{variacion:.1f}%",
                                  delta=f"$ {precios[-1] - precios[0]:.2f}")
    else:
        st.warning("No se encontraron productos con ese nombre. Intentá con otro.")