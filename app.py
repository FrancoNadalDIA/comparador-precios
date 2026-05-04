import pandas as pd
import streamlit as st

st.set_page_config(page_title="Monitor de Precios SEPA", layout="wide")


@st.cache_data
def cargar_datos():
    df = pd.read_csv('base_optimizada.csv')
    return df


st.title("📊 Inteligencia de Precios: Panel Ejecutivo")

df = cargar_datos()

# Agregamos la tercera pestaña
tab1, tab2, tab3 = st.tabs(["🔍 Comparador Actual", "📈 Evolución por Producto", "🏆 Tops de Variación"])

with tab1:
    fechas_historial = df['fecha'].drop_duplicates().tolist()
    ultima_fecha = fechas_historial[-1]
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

    col_a, col_b = st.columns(2)
    with col_a:
        search_term = st.text_input("1️⃣ Buscá el producto para trackear:", placeholder="Ej: COCA COLA")

    productos_unicos = df[['id_producto', 'productos_descripcion', 'productos_marca']].drop_duplicates()

    if search_term:
        productos_unicos = productos_unicos[
            productos_unicos['productos_descripcion'].str.contains(search_term.upper(), na=False) |
            productos_unicos['productos_marca'].str.contains(search_term.upper(), na=False)
            ]

    if not productos_unicos.empty:
        opciones = productos_unicos.apply(
            lambda x: f"{x['id_producto']} - {x['productos_descripcion']} ({x['productos_marca']})", axis=1).tolist()
        seleccion = st.selectbox("2️⃣ Seleccioná el producto exacto:", options=opciones)

        ean_seleccionado = seleccion.split(" - ")[0]
        df_track = df[df['id_producto'].astype(str) == ean_seleccionado].copy()

        # Respetamos el orden original de las fechas
        df_track['fecha_orden'] = pd.Categorical(df_track['fecha'], categories=fechas_historial, ordered=True)
        df_track = df_track.sort_values('fecha_orden')

        if not df_track.empty:
            st.write(f"### Evolución de: {seleccion}")
            chart_data = df_track.set_index('fecha')[['Carrefour', 'Coto', 'Día']]
            st.line_chart(chart_data)

            if len(df_track) > 1:
                st.write("#### Variación total por cadena (desde la primera carga):")
                c1, c2, c3 = st.columns(3)
                for i, super_name in enumerate(['Carrefour', 'Coto', 'Día']):
                    precios = df_track[super_name].dropna().values
                    if len(precios) > 1:
                        variacion = ((precios[-1] - precios[0]) / precios[0] * 100)
                        with [c1, c2, c3][i]:
                            st.metric(label=f"Variación en {super_name}", value=f"{variacion:.1f}%",
                                      delta=f"$ {precios[-1] - precios[0]:.2f}")
    else:
        st.warning("No se encontraron productos con ese nombre. Intentá con otro.")

# --- NUEVA SECCIÓN DE TOPS ---
with tab3:
    st.subheader("🏆 Movimientos Bruscos de la Semana")

    fechas_historial = df['fecha'].drop_duplicates().tolist()

    if len(fechas_historial) < 2:
        st.warning(
            "Necesitamos al menos 2 semanas de datos para calcular los Tops. ¡La próxima semana estará disponible!")
    else:
        fecha_actual = fechas_historial[-1]
        fecha_anterior = fechas_historial[-2]

        st.markdown(
            f"Comparando precios de la última carga (**{fecha_actual}**) respecto a la anterior (**{fecha_anterior}**).")

        # 1. Separamos los datos de las dos semanas
        df_actual = df[df['fecha'] == fecha_actual][
            ['id_producto', 'productos_descripcion', 'productos_marca', 'Carrefour', 'Coto', 'Día']]
        df_anterior = df[df['fecha'] == fecha_anterior][['id_producto', 'Carrefour', 'Coto', 'Día']]

        # 2. Renombramos las columnas del pasado para poder cruzarlas
        df_anterior.columns = ['id_producto', 'Carrefour_ant', 'Coto_ant', 'Día_ant']

        # 3. Cruzamos por código de barras
        df_tops = pd.merge(df_actual, df_anterior, on='id_producto', how='inner')

        # Selector de supermercado para enfocar el análisis
        super_top = st.selectbox("🏬 Seleccioná la cadena para ver sus Tops:", ['Carrefour', 'Coto', 'Día'])

        # 4. Calculamos la variación porcentual y filtramos errores (divisiones por cero)
        col_actual = super_top
        col_anterior = f'{super_top}_ant'

        df_tops['Variación %'] = ((df_tops[col_actual] - df_tops[col_anterior]) / df_tops[col_anterior] * 100)
        df_tops = df_tops.dropna(subset=['Variación %', col_actual, col_anterior])

        # Eliminamos los productos que no cambiaron de precio (Variación = 0)
        df_movimientos = df_tops[df_tops['Variación %'] != 0]

        col_subas, col_bajas = st.columns(2)

        with col_subas:
            st.error("📈 Top 10 Mayores Aumentos")
            top_aumentos = df_movimientos.sort_values('Variación %', ascending=False).head(10)

            if not top_aumentos.empty:
                st.dataframe(
                    top_aumentos[['productos_descripcion', 'productos_marca', col_anterior, col_actual, 'Variación %']],
                    column_config={
                        "productos_descripcion": "Producto",
                        "productos_marca": "Marca",
                        col_anterior: st.column_config.NumberColumn(fecha_anterior, format="$ %.2f"),
                        col_actual: st.column_config.NumberColumn(fecha_actual, format="$ %.2f"),
                        "Variación %": st.column_config.NumberColumn("%", format="%.1f%%")
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("No se registraron aumentos.")

        with col_bajas:
            st.success("📉 Top 10 Mayores Bajas (Ofertas/Descuentos)")
            top_bajas = df_movimientos.sort_values('Variación %', ascending=True).head(10)

            if not top_bajas.empty:
                st.dataframe(
                    top_bajas[['productos_descripcion', 'productos_marca', col_anterior, col_actual, 'Variación %']],
                    column_config={
                        "productos_descripcion": "Producto",
                        "productos_marca": "Marca",
                        col_anterior: st.column_config.NumberColumn(fecha_anterior, format="$ %.2f"),
                        col_actual: st.column_config.NumberColumn(fecha_actual, format="$ %.2f"),
                        "Variación %": st.column_config.NumberColumn("%", format="%.1f%%")
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("No se registraron bajas de precio.")