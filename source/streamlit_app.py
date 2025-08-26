import pandas as pd
import geopandas as gpd
import pydeck as pdk
import streamlit as st
import altair as alt


class BPAVisualizer:
    def __init__(self):
        self.departamentos_objetivo = ['TOTORAL', 'COLÓN', 'ISCHILÍN', 'TULUMBA']
        self.colores_departamento = {
            'TOTORAL': [255, 0, 0, 12],
            'COLÓN': [0, 255, 0, 12],
            'ISCHILÍN': [0, 0, 255, 12],
            'TULUMBA': [255, 165, 0, 12]
        }


    def stream_data(self):
        import time

        texto_datos = """
        Si necesitas trabajar con datos especificos, podes comunicarte conmigo a traves de:
        - Email: reynarenzo.88@gmail.com 
        - telefono: +54 3525 62-0842
        - dirección: INDEPENDENCIA 0, SARMIENTO, CORDOBA, ARGENTINA
        """

        for word in texto_datos.split(" "):
            yield word + " "
            time.sleep(0.03)

      

    def run(self):
        st.set_page_config(layout="wide",
                           page_title="Visualización Territorial del BPA en Córdoba",
                           page_icon="📍")
        
        st.header("📍 Visualización Territorial de BPA (2019–2024)")

        # Cargar datos
        df_bpa = pd.read_csv("source/assets/bpa/bpa_zona_norte_2019_2024.csv")
        df_bpa['Año'] = pd.to_datetime(df_bpa['Año'], format='%Y-%m-%d', errors='coerce')
        self.df_bpa = df_bpa  # Guardar como atributo

        # Cargar shapefile
        gdf_departamentos = gpd.read_file("source/assets/shapefile-zip/departamentos.zip")
        gdf_departamentos = gdf_departamentos.to_crs("EPSG:4326")
        gdf_departamentos['coordinates'] = gdf_departamentos['geometry'].apply(lambda geom: geom.__geo_interface__['coordinates'])
        gdf_departamentos['fill_color'] = gdf_departamentos['nombre'].map(self.colores_departamento)
        df_departamentos = gdf_departamentos[gdf_departamentos['nombre'].isin(self.departamentos_objetivo)].copy()


        # Ranking
        ranking = df_bpa.groupby('localidad').agg({'bpa_total': 'sum'}).reset_index().sort_values(by='bpa_total', ascending=False)
        st.subheader("🏆Ranking de localidades por BPA total")
        chart_ranking = alt.Chart(ranking.head(10)).mark_bar().encode(
            x='bpa_total:Q',
            y=alt.Y('localidad:N', sort='-x'),
            color=alt.value('#1f77b4'),
            tooltip=['localidad', 'bpa_total']
        ).properties(title='Top 10 localidades por BPA total')
        st.altair_chart(chart_ranking, use_container_width=True)


        df_icono = pd.DataFrame([{
            "nombre": "Sarmiento",
            "lon": -64.105187,
            "lat": -30.772768,
            "icon_data": {
                "url": "https://img.icons8.com/color/48/000000/marker.png",  # url del icono
                "width": 128,
                "height": 128,
                "anchorY": 128
            }
        }])


        # Mapa
        st.subheader("🗺️ Distribución geográfica BPA")

        layer_departamentos = pdk.Layer(
            "PolygonLayer",
            data=df_departamentos,
            get_polygon="coordinates",
            get_fill_color="fill_color",
            get_line_color="[80, 80, 80, 200]",
            line_width_min_pixels=2,
            pickable=False,
            auto_highlight=True,
            extruded=False,
        )

        layer_icono = pdk.Layer(
            type="IconLayer",
            data=df_icono,
            get_icon="icon_data",
            get_position='[lon, lat]',
            size_scale=21,
            pickable=True
        )


        layer_etiquetas = pdk.Layer(
            "TextLayer",
            data=df_departamentos,
            get_position='[lon, lat]',
            get_text='nombre',
            get_size=16,
            get_color=[0, 0, 0],
            get_alignment_baseline="bottom",
        )

        layer_puntos = pdk.Layer(
            "ScatterplotLayer",
            data=df_bpa,
            stroked=True,
            get_position='[lon, lat]',
            get_radius='bpa_total * 30',
            get_fill_color='[0, 0, 255, 140]',
            pickable=True,
            auto_highlight=True,
            border_width=1,
            get_line_color=[0, 0, 0],
            tooltip=True,
            radius_scale=3.6,  
        )

        
        view_state = pdk.ViewState(
            latitude=-30.7472872,
            longitude=-64.1455681,
            zoom=7.5,
            pitch=0
        )

        r = pdk.Deck(
            layers=[layer_puntos, layer_departamentos, layer_etiquetas, layer_icono],
            initial_view_state=view_state,
            tooltip={
                "text": "🌱 BPA aplicadas: {bpa_total}\n"
                        "📐 Superficie BPA: {superficie_bpa} ha\n"
                        "📊 Superficie total: {superficie} ha\n"
                        "🧪 Bioinsumos: {bioinsumos}\n"
                        "🔄 Economía circular: {economia_circular}\n"
                        "⚡ Energía renovable: {efic_energ_y_energia_renov}"
                    }            
        )

        st.pydeck_chart(r)


        # Filtros
        zonas_foco = sorted(df_bpa['localidad'].dropna().unique())
        loc_seleccionada = st.selectbox("Seleccionar localidad", zonas_foco)


        df_filtrado = df_bpa[
                            (df_bpa['localidad'] == loc_seleccionada) 
                            ]

        # Paneles de resumen
        st.subheader(f"📊 Indicadores para: {loc_seleccionada.title()}")

        col1, col2 = st.columns(2)

        with col1:
            chart = alt.Chart(df_bpa).mark_line(point=False,
                                                 color='steelblue', strokeWidth=1).encode(
                x='Año:T',
                y='bpa_total:Q',
                tooltip=['Año', 'bpa_total']
            ).properties(title='Evolución de BPA total')
            st.altair_chart(chart, use_container_width=True)

        with col2:
            scatter = alt.Chart(df_filtrado).mark_circle(size=60, opacity=0.6).encode(
                x=alt.X('superficie:Q', title='Superficie total (ha)'),
                y=alt.Y('superficie_bpa:Q', title='Superficie BPA (ha)'),
                tooltip=['superficie', 'superficie_bpa']
            ).properties(title='Relación entre superficie total y superficie dónde se implementan BPA')
            st.altair_chart(scatter, use_container_width=True)

        # Narrativa territorial
        st.markdown(f"""
        ### 🧠 Narrativa territorial: {loc_seleccionada.title()}
        Esta localidad presenta un total de **{len(df_filtrado)} registros BPA** entre 2019 y 2024.

        - Superficie BPA promedio: **{df_filtrado['superficie_bpa'].mean():.2f} ha**
        - Superficie total promedio: **{df_filtrado['superficie'].mean():.2f} ha**
        - BPA aplicadas promedio: **{df_filtrado['bpa_total'].mean():.2f}**
        """)

        # Streaming descriptivo
        st.markdown("""
                    ### 📜Descripción del Programa de Buenas Prácticas Agropecuarias (BPA)
                    El Programa de Buenas Prácticas Agropecuarias (BPAs) de Córdoba fue establecido por la Ley N° 10.663 en octubre de 2019. 
                    Su objetivo es promover prácticas agrícolas sostenibles que mejoren la productividad y protejan el medio ambiente.

                    #### Beneficios clave:
                    Uso eficiente del suelo: Incentiva técnicas como la rotación de cultivos y la siembra directa, que conservan la estructura y fertilidad del suelo.
                    Beneficios económicos: Los productores que implementan BPAs pueden acceder a aportes económicos no reintegrables como incentivo por cada práctica validada.
                    Para participar, los productores deben registrarse en la Plataforma de Servicios Ciudadano Digital (CiDi) del Gobierno de Córdoba. 
                    Más información está disponible en bpa.cba.gov.ar.
                    """)
       
        st.markdown("---")
        # Streaming narrativo
        if st.button("📡 Contactos"):
            st.write_stream(self.stream_data)

        st.markdown("© 2025 Renzo Gerardo Reyna — Todos los derechos reservados. Visualización desarrollada para democratizar el acceso a datos agroindustriales.")


if __name__ == "__main__":
    visualizer = BPAVisualizer()
    visualizer.run()