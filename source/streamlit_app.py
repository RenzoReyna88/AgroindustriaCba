import pandas as pd
import geopandas as gpd
import pydeck as pdk
import streamlit as st
import altair as alt


class BPAVisualizer:
    def __init__(self):
        self.departamentos_objetivo = ['TOTORAL', 'COLÓN', 'ISCHILÍN', 'TULUMBA']
        self.colores_departamento = {
            'TOTORAL': [255, 0, 0, 30],
            'COLÓN': [0, 255, 0, 30],
            'ISCHILÍN': [0, 0, 255, 30],
            'TULUMBA': [255, 165, 0, 30]
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
        
         
        import base64
        with open("source/assets/logo/MiLogoPersonal.png", "rb") as f:
            data = f.read()
            encoded = base64.b64encode(data).decode()

        st.markdown(
            f"""
            <div style='display: flex; align-items: center;'>
                <img src='data:image/png;base64,{encoded}' style='border-radius: 50%; hiegth:40; width: 100px;'/>
            </div>
            """,
            unsafe_allow_html=True
        )
            
        st.markdown(
                """
                <div style='text-align: center; margin-bottom: 40px;'>
                    <h2>Programa Buenas Prácticas Agropecuarias: Región Norte</h2>
                </div>
                """,
                unsafe_allow_html=True
            )



        # Cargar datos
        df_bpa = pd.read_csv("source/assets/bpa/bpa_zona_norte_2019_2024.csv")
        df_bpa['Año'] = pd.to_datetime(df_bpa['Año'], format='%Y-%m-%d', errors='coerce')
        self.df_bpa = df_bpa  # Guardar como atributo

        # Cargar shapefile
        gdf_departamentos = gpd.read_file("source/assets/shapefile-zip/departamentos/departamentos.shp")
        gdf_departamentos = gdf_departamentos.to_crs("EPSG:4326")
        gdf_departamentos['coordinates'] = gdf_departamentos['geometry'].apply(lambda geom: geom.__geo_interface__['coordinates'])
        gdf_departamentos['fill_color'] = gdf_departamentos['nombre'].map(self.colores_departamento)
        df_departamentos = gdf_departamentos[gdf_departamentos['nombre'].isin(self.departamentos_objetivo)].copy()


        # Cargar shapefile de rutas nacionales
        gdf_rutas = gpd.read_file("source/assets/red-vial/red_vial_nacional.zip")
        # Convertir a WGS84 si no está en ese sistema
        gdf_rutas = gdf_rutas.to_crs("EPSG:4326")
        # Crear una nueva columna 'coordinates' con las coordenadas de las geometrías
        gdf_rutas['coordinates'] = gdf_rutas['geometry'].apply(lambda geom: geom.__geo_interface__['coordinates'])
        # Crear DataFrame con estructura esperada
        df_rutas = gdf_rutas[["coordinates"]].copy()



        # Crear columnas para el ranking y el mapa
        colmap1, colmap2 = st.columns([1,1])

        # Ranking
        ranking = df_bpa.groupby('localidad').agg({'bpa_total': 'sum'}).reset_index().sort_values(by='bpa_total', ascending=False)
        
        chart_ranking = alt.Chart(ranking.head(18)).mark_bar().encode(
            x=alt.X('bpa_total:Q',
                axis=alt.Axis(
                    format=',.0f',  # formato con separador de miles
                    labelExpr="replace(datum.label, ',', '')"
                )
            ),
            y=alt.Y('localidad:N', sort='-x'),
            color=alt.value('#1f77b4'),
            tooltip=['localidad', 'bpa_total']
        ).properties(title='Top 18 localidades por BPA total')

        # Mostrar el ranking en la primera columna
        with colmap1:
            st.markdown(
                    """
                    <div style='text-align: start; margin-bottom: 40px;'>
                        <h3>🏆Ranking de localidades</h3>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            st.altair_chart(chart_ranking, use_container_width=True)



        # Configuración del mapa
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
            size_scale=21.6,
            pickable=True
        )

        layer_puntos = pdk.Layer(
            "ScatterplotLayer",
            data=df_bpa,
            stroked=True,
            get_position='[lon, lat]',
            get_radius='bpa_total * 30',
            get_fill_color='[70, 130, 180, 200]',
            pickable=True,
            auto_highlight=True,
            border_width=1,
            get_line_color=[0, 0, 0],
            tooltip=True,
            radius_scale=3.9,  
        )

        layer_rutas = pdk.Layer(
            "PathLayer",
            data=df_rutas,
            get_path="coordinates",
            get_color=[255, 215, 0, 60],  # color de las rutas
            width_scale=20,
            width_min_pixels=2,
            get_width=5,
            pickable=False
        )
        
        view_state = pdk.ViewState(
            latitude=-30.7472872,
            longitude=-64.1455681,
            zoom=6.9,
            pitch=0,
            bearing=0
        )

        r = pdk.Deck(
            layers=[layer_puntos, layer_departamentos, layer_icono, layer_rutas],
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

        # Mostrar el mapa en la segunda columna
        with colmap2:
            st.markdown(
                    """
                    <div style='text-align: start; margin-bottom: 40px;'>
                        <h3>🗺️ Distribución geográfica</h3>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            st.pydeck_chart(r)


        # Filtros
        # Paneles de resumen
        zonas_foco = sorted(df_bpa['localidad'].dropna().unique())
        loc_seleccionada = st.selectbox("Seleccionar localidad", zonas_foco)

        df_filtrado = df_bpa[
                            (df_bpa['localidad'] == loc_seleccionada) 
                            ]
        
        

        st.markdown(
                    f"""
                    <div style='text-align: center; margin-bottom: 40px; height: 40px;'>
                        <h3>📊 Indicadores de rendimiento para: {loc_seleccionada.title()}</h3>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

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

        st.markdown("---")


        # Streaming descriptivo
        st.markdown(
                    """
                    <div style='text-align: center; margin-bottom: 40px;'>
                        <h3>📜Descripción del Programa de Buenas Prácticas Agropecuarias (BPA)</h3>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        st.markdown("""
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