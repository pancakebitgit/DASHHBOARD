import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Page Configuration ---
st.set_page_config(
    page_title="Análisis Interactivo de Opciones",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Dark Theme (Streamlit's native dark theme is good, but can be customized further if needed) ---
# Streamlit uses its own theme detection, but we can force it or add custom CSS.
# For now, relying on Streamlit's default dark theme detection or user's OS setting.
# To force dark theme (example):
# st.markdown("""
# <style>
# body {
#     color: white;
#     background-color: #0E1117;
# }
# .stApp {
#     background-color: #0E1117;
# }
# </style>
# """, unsafe_allow_html=True)


# --- Load Data ---
@st.cache_data
def load_data(file_path, file_name):
    try:
        df = pd.read_csv(file_path)
        return df
    except FileNotFoundError:
        st.error(f"Error: El archivo {file_name} ({file_path}) no fue encontrado. Asegúrate de que esté en el directorio correcto.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al cargar {file_name}: {e}")
        return pd.DataFrame()

df_cadena = load_data("CADENA.csv", "CADENA.csv")
df_griegas = load_data("Griegas.csv", "Griegas.csv")
df_inusual = load_data("Inusual.csv", "Inusual.csv")

# --- Main Title ---
st.title("📊 Análisis Interactivo de Opciones")
st.markdown("Bienvenido al dashboard de análisis de opciones. Utiliza las pestañas a continuación para explorar diferentes aspectos del mercado.")

# --- Create Tabs ---
tab1, tab2, tab3 = st.tabs([
    "⛓️ Cadena de Opciones",
    "🏛️ Análisis de Griegas",
    "📈 Flujo Inusual de Opciones"
])

with tab1:
    st.header("⛓️ Cadena de Opciones")
    if not df_cadena.empty:
        st.subheader("Datos de la Cadena de Opciones")
        st.dataframe(df_cadena.style.format({"IV": "{:.2%}", "Delta": "{:.4f}", "Moneyness": "{:.2%}"}), use_container_width=True)

        # Clean data for cadena_df before plotting
        if 'IV' in df_cadena.columns:
            df_cadena['IV'] = df_cadena['IV'].replace(['unch', 'N/A', ''], np.nan)
            # Apply rstrip and division only to strings, then convert all to numeric
            # Ensure that we handle potential pd.NA by converting to string first ONLY for rstrip
            def clean_iv(val):
                if pd.isna(val):
                    return np.nan
                s_val = str(val)
                if s_val.endswith('%'):
                    return pd.to_numeric(s_val.rstrip('%'), errors='coerce') / 100.0
                return pd.to_numeric(s_val, errors='coerce') / 100.0 # Assuming it's already a pre-scaled percentage if no '%'
            df_cadena['IV'] = df_cadena['IV'].apply(clean_iv)
            df_cadena['IV'] = pd.to_numeric(df_cadena['IV'], errors='coerce')


        if 'Moneyness' in df_cadena.columns:
            df_cadena['Moneyness'] = df_cadena['Moneyness'].replace(['unch', 'N/A', ''], np.nan)
            def clean_moneyness(val):
                if pd.isna(val):
                    return np.nan
                s_val = str(val).replace('+', '')
                if s_val.endswith('%'):
                    return pd.to_numeric(s_val.rstrip('%'), errors='coerce') / 100.0
                # If not ending with %, try converting directly, assuming it might be a pre-scaled decimal
                # This case might need adjustment based on actual data variety
                return pd.to_numeric(s_val, errors='coerce')
            df_cadena['Moneyness'] = df_cadena['Moneyness'].apply(clean_moneyness)
            df_cadena['Moneyness'] = pd.to_numeric(df_cadena['Moneyness'], errors='coerce')

        plain_numeric_cols_cadena = ['Delta', 'Strike', 'Bid', 'Mid', 'Ask', 'Last', 'Volume', 'Open Int']
        for col in plain_numeric_cols_cadena:
            if col in df_cadena.columns:
                df_cadena[col] = df_cadena[col].replace(['unch', 'N/A', ''], np.nan)
                df_cadena[col] = pd.to_numeric(df_cadena[col], errors='coerce')

        # Define numeric columns explicitly for dropping NA after all conversions
        # These are the columns used in subsequent .style.format or plots that need to be numeric
        cols_for_style_and_plot_cadena = ['IV', 'Delta', 'Moneyness', 'Strike', 'Volume', 'Open Int']
        df_cadena.dropna(subset=[col for col in cols_for_style_and_plot_cadena if col in df_cadena.columns], inplace=True)

        st.subheader("Análisis Visual de la Cadena")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### Volumen por Strike")
            if 'Volume' in df_cadena.columns and 'Strike' in df_cadena.columns and not df_cadena.empty:
                fig_vol_strike = px.bar(df_cadena, x='Strike', y='Volume', color='Type',
                                        title="Volumen por Strike (Calls vs Puts)",
                                        labels={'Volume': 'Volumen Total', 'Strike': 'Precio de Ejercicio'},
                                        barmode='group')
                fig_vol_strike.update_layout(legend_title_text='Tipo')
                st.plotly_chart(fig_vol_strike, use_container_width=True)
            else:
                st.write("Datos de Volumen o Strike no disponibles o insuficientes para el gráfico.")

            st.markdown("##### Volatilidad Implícita (IV) por Strike")
            if 'IV' in df_cadena.columns and 'Strike' in df_cadena.columns and not df_cadena.empty:
                fig_iv_strike = px.line(df_cadena, x='Strike', y='IV', color='Type',
                                        title="IV por Strike (Calls vs Puts)",
                                        labels={'IV': 'Volatilidad Implícita (%)', 'Strike': 'Precio de Ejercicio'},
                                        markers=True)
                fig_iv_strike.update_layout(yaxis_tickformat=".2%", legend_title_text='Tipo')
                st.plotly_chart(fig_iv_strike, use_container_width=True)
            else:
                st.write("Datos de IV o Strike no disponibles o insuficientes para el gráfico.")

        with col2:
            st.markdown("##### Open Interest por Strike")
            if 'Open Int' in df_cadena.columns and 'Strike' in df_cadena.columns and not df_cadena.empty:
                fig_oi_strike = px.bar(df_cadena, x='Strike', y='Open Int', color='Type',
                                       title="Open Interest por Strike (Calls vs Puts)",
                                       labels={'Open Int': 'Interés Abierto', 'Strike': 'Precio de Ejercicio'},
                                       barmode='group')
                fig_oi_strike.update_layout(legend_title_text='Tipo')
                st.plotly_chart(fig_oi_strike, use_container_width=True)
            else:
                st.write("Datos de Open Interest o Strike no disponibles o insuficientes para el gráfico.")

            st.markdown("##### Moneyness vs. IV")
            if 'Moneyness' in df_cadena.columns and 'IV' in df_cadena.columns and 'Strike' in df_cadena.columns and not df_cadena.empty:
                fig_money_iv = px.scatter(df_cadena, x='Moneyness', y='IV', color='Type',
                                          title="Moneyness vs. Volatilidad Implícita",
                                          labels={'Moneyness': 'Moneyness (%)', 'IV': 'Volatilidad Implícita (%)'},
                                          hover_data=['Strike'])
                fig_money_iv.update_layout(xaxis_tickformat=".2%", yaxis_tickformat=".2%", legend_title_text='Tipo')
                st.plotly_chart(fig_money_iv, use_container_width=True)
            else:
                st.write("Datos de Moneyness, IV o Strike no disponibles o insuficientes para el gráfico.")

        st.subheader("Ratio Put/Call")
        if 'Volume' in df_cadena.columns and 'Open Int' in df_cadena.columns and 'Type' in df_cadena.columns and not df_cadena.empty:
            # Calculate Put/Call Ratios
            calls_df = df_cadena[df_cadena['Type'] == 'Call']
            puts_df = df_cadena[df_cadena['Type'] == 'Put']

            total_volume_calls = calls_df['Volume'].sum()
            total_volume_puts = puts_df['Volume'].sum()
            pc_ratio_volume = total_volume_puts / total_volume_calls if total_volume_calls > 0 else 0

            total_oi_calls = calls_df['Open Int'].sum()
            total_oi_puts = puts_df['Open Int'].sum()
            pc_ratio_oi = total_oi_puts / total_oi_calls if total_oi_calls > 0 else 0

            col_pc1, col_pc2 = st.columns(2)
            with col_pc1:
                st.metric(label="Put/Call Ratio (Volumen)", value=f"{pc_ratio_volume:.2f}")
            with col_pc2:
                st.metric(label="Put/Call Ratio (Open Interest)", value=f"{pc_ratio_oi:.2f}")

            st.markdown(
                """
                **Interpretación del Put/Call Ratio:**
                - **> 1:** Sentimiento bajista o mayor cobertura (más Puts que Calls).
                - **< 1:** Sentimiento alcista (más Calls que Puts).
                - **~ 1:** Sentimiento neutral.
                """
            )
        else:
            st.write("Datos necesarios para calcular el Put/Call Ratio no disponibles.")

    else:
        st.warning("No se pudieron cargar los datos de CADENA.csv para mostrar.")

with tab2:
    st.header("🏛️ Análisis de Griegas")
    if not df_griegas.empty:
        st.subheader("Datos de Griegas de Opciones")

        # Clean data for df_griegas before plotting
        cols_to_clean_griegas = {
            'IV': True, 'ITM Prob': True, 'Delta': False, 'Gamma': False,
            'Theta': False, 'Vega': False, 'Strike': False, 'Bid': False,
            'Ask': False, 'Volume': False, 'Open Int': False
        }

        for col, is_percent in cols_to_clean_griegas.items():
            if col in df_griegas.columns:
                df_griegas[col] = df_griegas[col].replace(['unch', 'N/A', ''], pd.NA)
                if is_percent:
                    df_griegas[col] = pd.to_numeric(df_griegas[col].astype(str).str.rstrip('%'), errors='coerce') / 100.0
                else:
                    df_griegas[col] = pd.to_numeric(df_griegas[col], errors='coerce')
            else:
                st.warning(f"Columna '{col}' no encontrada en Griegas.csv para la limpieza.")

        numeric_cols_for_na_drop_griegas = list(cols_to_clean_griegas.keys())
        df_griegas.dropna(subset=[col for col in numeric_cols_for_na_drop_griegas if col in df_griegas.columns], inplace=True)

        st.dataframe(df_griegas.style.format({
            "IV": "{:.2%}", "Delta": "{:.4f}", "Gamma": "{:.4f}",
            "Theta": "{:.4f}", "Vega": "{:.4f}", "ITM Prob": "{:.2%}"
        }), use_container_width=True)

        st.subheader("Visualización de Griegas")

        # Selector for Griegas
        greek_to_plot = st.selectbox(
            "Selecciona la Griega a Visualizar:",
            ('Delta', 'Gamma', 'Theta', 'Vega'),
            key='greek_selector'
        )

        if greek_to_plot and greek_to_plot in df_griegas.columns and 'Strike' in df_griegas.columns and 'Type' in df_griegas.columns and not df_griegas.empty:
            fig_greek_strike = px.bar(df_griegas, x='Strike', y=greek_to_plot, color='Type',
                                      title=f"{greek_to_plot} por Strike (Calls vs Puts)",
                                      labels={greek_to_plot: greek_to_plot, 'Strike': 'Precio de Ejercicio'},
                                      barmode='group')
            fig_greek_strike.update_layout(legend_title_text='Tipo')
            st.plotly_chart(fig_greek_strike, use_container_width=True)
        else:
            st.write(f"Datos de {greek_to_plot}, Strike o Type no disponibles o insuficientes para el gráfico.")

        st.subheader("Exposición Agregada (Ejemplo)")
        # Note: Proper GEX and other exposure calculations can be complex and require assumptions.
        # Here, we'll show simple sums of Vega and Theta weighted by Open Interest.

        if 'Vega' in df_griegas.columns and 'Open Int' in df_griegas.columns and 'Strike' in df_griegas.columns and not df_griegas.empty:
            df_griegas['Vega Exposure'] = df_griegas['Vega'] * df_griegas['Open Int'] * 100 # Contract multiplier

            # Group by Strike and sum Vega Exposure
            vega_exposure_summary = df_griegas.groupby('Strike', as_index=False)['Vega Exposure'].sum()

            fig_vega_exposure = px.bar(vega_exposure_summary,
                                       x='Strike', y='Vega Exposure', title="Exposición a Vega por Strike",
                                       labels={'Vega Exposure': 'Exposición Total a Vega', 'Strike': 'Precio de Ejercicio'})
            st.plotly_chart(fig_vega_exposure, use_container_width=True)
            st.markdown("""
            **Exposición a Vega:** Muestra cuánto dinero (en teoría) ganarían o perderían todas las posiciones abiertas en un strike
            si la Volatilidad Implícita (IV) cambia un 1%. Un valor positivo significa que las posiciones ganarían si la IV sube.
            """)
        else:
            st.write("Datos para Exposición a Vega no disponibles.")

        if 'Theta' in df_griegas.columns and 'Open Int' in df_griegas.columns and 'Strike' in df_griegas.columns:
            df_griegas['Theta Exposure'] = df_griegas['Theta'] * df_griegas['Open Int'] * 100 # Contract multiplier
            fig_theta_exposure = px.bar(df_griegas.groupby('Strike')['Theta Exposure'].sum().reset_index(),
                                        x='Strike', y='Theta Exposure', title="Exposición a Theta por Strike",
                                        labels={'Theta Exposure': 'Exposición Total a Theta (Decaimiento Diario)', 'Strike': 'Precio de Ejercicio'})
            st.plotly_chart(fig_theta_exposure, use_container_width=True)
            st.markdown("""
            **Exposición a Theta:** Muestra cuánto valor (en teoría) pierden todas las opciones abiertas en un strike por día debido al paso del tiempo.
            Valores negativos son típicos para compradores de opciones.
            """)
        else:
            st.write("Datos para Exposición a Theta no disponibles.")

        # Placeholder for GEX and Gamma Flip - these are more advanced.
        st.markdown("---")
        st.markdown("💡 **Nota sobre GEX y Gamma Flip Point:**")
        st.info("""
        El cálculo preciso de la Exposición a Gamma del Mercado (GEX) y el Gamma Flip Point es complejo.
        Requiere un modelo de las posiciones de los market makers y datos más granulares.

        - **GEX (Exposición a Gamma):** Mide cómo cambia el Delta total de los market makers. Un GEX positivo sugiere que los dealers comprarán en caídas y venderán en subidas (estabilizando el precio). Un GEX negativo sugiere lo contrario (acelerando movimientos).
        - **Gamma Flip Point:** El precio del subyacente donde el GEX neto cruza de positivo a negativo. Actúa como un nivel dinámico de soporte/resistencia.

        Para este dashboard, se muestra el Gamma por strike. Un análisis más profundo de GEX requeriría datos adicionales y modelado.
        """)

    else:
        st.warning("No se pudieron cargar los datos de Griegas.csv para mostrar.")

with tab3:
    st.header("📈 Flujo Inusual de Opciones")
    if not df_inusual.empty:
        st.subheader("Datos de Flujo Inusual de Opciones")

        # Clean data for df_inusual
        if 'Expires' in df_inusual.columns:
            df_inusual['Expires'] = pd.to_datetime(df_inusual['Expires'], errors='coerce')

        cols_to_clean_inusual = {
            'IV': True, 'Delta': False, # Delta can be float or percent string
            'Price~': False, 'Strike': False, 'DTE': False, 'Trade': False,
            'Size': False, 'Premium': False, 'Volume': False, 'Open Int': False
        }

        for col, is_strictly_percent in cols_to_clean_inusual.items():
            if col in df_inusual.columns:
                df_inusual[col] = df_inusual[col].replace(['unch', 'N/A', ''], pd.NA)
                if is_strictly_percent: # For IV
                    df_inusual[col] = pd.to_numeric(df_inusual[col].astype(str).str.rstrip('%'), errors='coerce') / 100.0
                elif col == 'Delta': # For Delta, which might be float or xx%
                    if df_inusual[col].dtype == 'object': # if it's a string that might have %
                         df_inusual[col] = pd.to_numeric(df_inusual[col].astype(str).str.rstrip('%'), errors='coerce')
                         # Heuristic: if values are large (e.g. > 5), assume they were percentages without % sign
                         if (df_inusual[col].abs() > 5).any():
                              df_inusual[col] = df_inusual[col] / 100.0
                    else: # if it's already numeric
                         df_inusual[col] = pd.to_numeric(df_inusual[col], errors='coerce')
                else: # For other numeric columns
                    df_inusual[col] = pd.to_numeric(df_inusual[col], errors='coerce')
            else:
                st.warning(f"Columna '{col}' no encontrada en Inusual.csv para la limpieza.")

        numeric_cols_for_na_drop_inusual = list(cols_to_clean_inusual.keys())
        # Critical columns for plotting/analysis that must be numeric
        critical_cols_inusual = ['Premium', 'Size', 'Volume', 'Open Int', 'Strike', 'IV', 'Delta']
        df_inusual.dropna(subset=[col for col in critical_cols_inusual if col in df_inusual.columns], inplace=True)

        display_format_inusual = {"IV": "{:.2%}", "Delta": "{:.4f}", "Premium": "${:,.0f}"}
        for col in df_inusual.columns:
            if "Price" in col and col not in display_format_inusual:
                display_format_inusual[col] = "${:,.2f}"

        st.dataframe(df_inusual.style.format(display_format_inusual), use_container_width=True)

        st.subheader("Análisis Visual del Flujo Inusual")

        col_flow1, col_flow2 = st.columns(2)

        with col_flow1:
            st.markdown("##### Premium Total por Tipo y Lado (Side)")
            if 'Premium' in df_inusual.columns and 'Type' in df_inusual.columns and 'Side' in df_inusual.columns and not df_inusual.empty:
                if not df_inusual['Side'].dropna().empty:
                    premium_summary = df_inusual.groupby(['Type', 'Side'])['Premium'].sum().reset_index()
                    fig_prem_type_side = px.bar(premium_summary, x='Type', y='Premium', color='Side',
                                                title="Premium Total por Tipo y Lado",
                                                labels={'Premium': 'Premium Total ($)', 'Type': 'Tipo de Opción', 'Side': 'Lado de la Operación'},
                                                barmode='group')
                    fig_prem_type_side.update_layout(legend_title_text='Lado')
                    st.plotly_chart(fig_prem_type_side, use_container_width=True)
                else:
                    st.write("Columna 'Side' está vacía o no disponible para el gráfico de Premium.")
            else:
                st.write("Datos de Premium, Type o Side no disponibles o insuficientes para el gráfico.")

            st.markdown("##### Volumen vs Open Interest (Flujo Inusual)")
            if 'Volume' in df_inusual.columns and 'Open Int' in df_inusual.columns and 'Premium' in df_inusual.columns and not df_inusual.empty:
                fig_vol_oi_scatter = px.scatter(df_inusual, x='Volume', y='Open Int',
                                                size='Premium', color='Type',
                                                title="Volumen vs OI (Tamaño por Premium)",
                                                labels={'Volume': 'Volumen de la Operación', 'Open Int': 'Interés Abierto del Strike'},
                                                hover_data=['Strike', 'Side', 'Expires'])
                fig_vol_oi_scatter.update_layout(legend_title_text='Tipo')
                st.plotly_chart(fig_vol_oi_scatter, use_container_width=True)
            else:
                st.write("Datos de Volumen, Open Int o Premium no disponibles o insuficientes para el gráfico de dispersión.")

        with col_flow2:
            st.markdown("##### Distribución de 'Premium' de Operaciones Inusuales")
            if 'Premium' in df_inusual.columns and not df_inusual['Premium'].dropna().empty:
                fig_premium_dist = px.histogram(df_inusual, x='Premium', color='Side',
                                                marginal="box",
                                                title="Distribución del Premium por Lado",
                                                labels={'Premium': 'Premium ($)'})
                fig_premium_dist.update_layout(legend_title_text='Lado')
                st.plotly_chart(fig_premium_dist, use_container_width=True)
            else:
                st.write("Datos de Premium no disponibles o insuficientes para el histograma.")

            st.markdown("##### Operaciones Inusuales por 'Code'")
            if 'Code' in df_inusual.columns and 'Premium' in df_inusual.columns and not df_inusual.empty:
                if not df_inusual['Code'].dropna().empty:
                    code_summary = df_inusual.groupby('Code')['Premium'].sum().reset_index().sort_values(by='Premium', ascending=False)
                    fig_code_prem = px.bar(code_summary, x='Code', y='Premium',
                                        title="Premium Total por Código de Operación",
                                        labels={'Premium': 'Premium Total ($)', 'Code': 'Código de Operación'})
                    st.plotly_chart(fig_code_prem, use_container_width=True)
                else:
                    st.write("Columna 'Code' está vacía o no disponible para el gráfico por código.")
            else:
                st.write("Datos de Code o Premium no disponibles o insuficientes para el gráfico por código.")

        st.subheader("Destacados del Flujo Inusual")
        if not df_inusual.empty and 'Volume' in df_inusual.columns and 'Open Int' in df_inusual.columns and 'Premium' in df_inusual.columns:
            df_inusual_copy = df_inusual.copy() # Work on a copy for calculations
            df_inusual_copy['Vol_OI_Ratio'] = df_inusual_copy['Volume'] / (df_inusual_copy['Open Int'] + 1)

            # Ensure Premium is numeric for quantile calculation
            if pd.api.types.is_numeric_dtype(df_inusual_copy['Premium']) and not df_inusual_copy['Premium'].dropna().empty:
                min_premium_highlight = df_inusual_copy['Premium'].quantile(0.75)
                min_vol_oi_ratio_highlight = 1.0

                highlighted_trades = df_inusual_copy[
                    (df_inusual_copy['Premium'] >= min_premium_highlight) &
                    (df_inusual_copy['Vol_OI_Ratio'] >= min_vol_oi_ratio_highlight)
                ].sort_values(by='Premium', ascending=False)

                st.markdown(f"Operaciones con Premium >= ${min_premium_highlight:,.0f} y Ratio Volumen/OI >= {min_vol_oi_ratio_highlight:.2f}")
                if not highlighted_trades.empty:
                    st.dataframe(
                        highlighted_trades[['Symbol', 'Type', 'Strike', 'Expires', 'Side', 'Premium', 'Volume', 'Open Int', 'Vol_OI_Ratio', 'Code', 'Time']],
                        use_container_width=True,
                        column_config={
                            "Premium": st.column_config.NumberColumn(format="$%d"),
                            "Vol_OI_Ratio": st.column_config.NumberColumn(format="%.2f"),
                            "Expires": st.column_config.DateTimeColumn(format="YYYY-MM-DD HH:mm") # Use DateTimeColumn for datetime
                        }
                    )
                else:
                    st.info("No se encontraron operaciones que cumplan los criterios de destaque actuales.")
            else:
                st.warning("La columna 'Premium' no es numérica o está vacía después de la limpieza, no se pueden calcular los destaques.")
        else:
            st.write("No hay datos suficientes de flujo inusual para analizar destaques.")

    else:
        st.warning("No se pudieron cargar los datos de Inusual.csv para mostrar.")

# --- Sidebar (Optional: for global filters or info) ---
st.sidebar.header("Controles Globales")
st.sidebar.info(
    "Este es un panel de ejemplo. En una aplicación real, "
    "aquí podrías tener filtros por símbolo (ticker), fecha, etc."
)
# Example: Symbol selector (if data supported multiple symbols)
# if not df_griegas.empty and 'Symbol' in df_griegas.columns:
#     available_symbols = df_griegas['Symbol'].unique()
#     selected_symbol = st.sidebar.selectbox("Seleccionar Símbolo:", available_symbols)
# else:
#     selected_symbol = "EQT" # Default or from sample

st.sidebar.markdown("---")
st.sidebar.markdown("Creado por Jules IA 🤖")


# To run this app:
# 1. Save the code as dashboard.py
# 2. Make sure CADENA.csv, Griegas.csv, Inusual.csv are in the same directory.
# 3. Open your terminal and run: streamlit run dashboard.py
# Placeholder for content of Step 4, 5, 6
# Make sure to clean up column names, handle percentages, etc.

if df_cadena.empty and df_griegas.empty and df_inusual.empty:
    st.error("No se pudo cargar ninguno de los archivos CSV. El dashboard no puede mostrar datos.")

# Basic check to see if the app runs
if __name__ == '__main__':
    # This block is not strictly necessary for streamlit but can be useful.
    # Streamlit apps are typically run via `streamlit run app.py`
    pass
