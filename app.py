import streamlit as st
import pandas as pd
import os
from datetime import date, timedelta
import hashlib
import plotly.express as px

# ===========================
# CONFIGURACIÓN DE LA APP
# ===========================
st.set_page_config(page_title="666 Rolling Hell", page_icon="📐", layout="centered")
st.title("666 Rolling Hell")
st.caption("Cálculo de planos de la MC 📐")
st.caption("Administra la producción de planos de la MC. Algunos datos son privados 🔒")

# ===========================
# CONTRASEÑA ENCRIPTADA
# ===========================
PASSWORD_HASH = "e2c569be17396eca2a2e3c11578123ed5c28b0a0c1e5e63f8c3f9b8a0d6b3b0b"

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

# ===========================
# CARGAR HISTORIAL
# ===========================
os.makedirs("data", exist_ok=True)
ruta_historial = os.path.join("data", "historial.csv")

try:
    historial = pd.read_csv(ruta_historial)
except (FileNotFoundError, pd.errors.EmptyDataError):
    historial = pd.DataFrame(columns=[
        "Fecha", "Semana", "Periodicidad", "Tipo de Plano", "Planos Hechos",
        "Precio por Plano", "Costo Total", "Ganancia Neta"
    ])

# Asegurar columna Semana
if "Semana" not in historial.columns:
    historial["Semana"] = pd.NA

# Convertir Fecha a datetime
historial["Fecha"] = pd.to_datetime(historial["Fecha"])

# Rellenar Semana para datos antiguos de periodicidad semanal
if "Periodicidad" in historial.columns:
    historial["Semana"] = historial.apply(
        lambda row: row["Fecha"] - pd.Timedelta(days=row["Fecha"].weekday()) 
        if row["Periodicidad"]=="Semanal" else pd.NA,
        axis=1
    )

# ===========================
# MODO ADMIN / VISTA PÚBLICA
# ===========================
modo = st.radio("Seleccionar modo de uso:", ["👁️ Solo ver historial", "🔑 Modo administrador"])

# ===========================
# FUNCION PARA AGREGAR MARCA DIAGONAL
# ===========================
def agregar_marca_diagonal(fig, texto="666 Rolling Hell 🔒", repeticiones=5):
    for i in range(repeticiones):
        x = 0.1 + i * (0.8 / repeticiones)
        y = 0.9 - i * (0.8 / repeticiones)
        fig.add_annotation(
            text=texto,
            xref="paper", yref="paper",
            x=x, y=y,
            showarrow=False,
            font=dict(size=40, color="rgba(200,200,200,0.15)"),
            xanchor='center',
            yanchor='middle',
            textangle=-45
        )
    return fig

# ===========================
# VISTA PÚBLICA
# ===========================
if modo == "👁️ Solo ver historial":
    st.header("📊 Historial de producción (vista pública)")
    if len(historial) > 0:
        publico = historial[["Fecha", "Semana", "Periodicidad", "Tipo de Plano", "Planos Hechos"]].copy()

        with st.expander("📋 Mostrar historial"):
            st.dataframe(publico, use_container_width=True, height=400)

        tipos_seleccionados = st.multiselect(
            "Seleccionar tipos de plano a mostrar:",
            options=publico["Tipo de Plano"].unique(),
            default=publico["Tipo de Plano"].unique()
        )

        fig_pub = px.line()
        for tipo in tipos_seleccionados:
            subset = publico[publico["Tipo de Plano"] == tipo].copy()
            if subset["Semana"].notna().any():
                df_plot = subset.groupby("Semana")["Planos Hechos"].sum().reset_index()
                fig_pub.add_scatter(x=pd.to_datetime(df_plot["Semana"]), y=df_plot["Planos Hechos"], mode='lines+markers', name=tipo)
            else:
                fig_pub.add_scatter(x=pd.to_datetime(subset["Fecha"]), y=subset["Planos Hechos"], mode='lines+markers', name=tipo)

        fig_pub.update_layout(title="Producción por tipo de plano", xaxis_title="Fecha", yaxis_title="Planos Hechos", hovermode="x unified")
        fig_pub = agregar_marca_diagonal(fig_pub)
        st.plotly_chart(fig_pub, use_container_width=True)

        st.subheader("📋 Total de planos por tipo (público)")
        resumen_publico = publico.groupby("Tipo de Plano")["Planos Hechos"].sum().reset_index()
        st.table(resumen_publico)
    else:
        st.info("Aún no hay registros cargados.")

# ===========================
# MODO ADMIN
# ===========================
else:
    if not st.session_state.autenticado:
        st.subheader("🔑 Iniciar sesión de administrador")
        password_input = st.text_input("Contraseña:", type="password")
        if st.button("Entrar"):
            if hashlib.sha256(password_input.encode()).hexdigest() == PASSWORD_HASH:
                st.session_state.autenticado = True
                st.success("Acceso concedido ✅")
            else:
                st.error("Contraseña incorrecta")
        st.stop()

    st.success("Modo administrador activo ✅")

    # ===========================
    # FORMULARIO DE REGISTRO
    # ===========================
    with st.expander("🧮 Registrar nueva producción"):
        with st.form("registro_form"):
            periodicidad = st.selectbox("Periodicidad:", ["Diaria", "Semanal"])
            tipo_plano = st.selectbox("Tipo de plano:", ["Arquitectonico", "Robo", "Otro"])
            planos_hechos = st.number_input("Cantidad de planos hechos", min_value=0, step=1)
            precio_plano = st.number_input("Precio de venta por plano ($)", min_value=0, step=100)
            costo_plano = st.number_input("Costo de producción por plano ($)", min_value=0, step=100)
            enviar = st.form_submit_button("💾 Guardar registro")

            if enviar:
                if planos_hechos <= 0:
                    st.warning("Debe ingresar al menos 1 plano.")
                elif costo_plano > precio_plano:
                    st.warning("⚠️ Advertencia: costo mayor que precio de venta.")
                else:
                    hoy = pd.Timestamp(date.today())
                    if periodicidad == "Semanal":
                        fecha_registro = hoy - pd.Timedelta(days=hoy.weekday())
                        semana_registro = fecha_registro
                    else:
                        fecha_registro = hoy
                        semana_registro = pd.NA

                    costo_total = planos_hechos * costo_plano
                    ganancia = (planos_hechos * precio_plano) - costo_total

                    nuevo_registro = pd.DataFrame({
                        "Fecha": [fecha_registro],
                        "Semana": [semana_registro],
                        "Periodicidad": [periodicidad],
                        "Tipo de Plano": [tipo_plano],
                        "Planos Hechos": [planos_hechos],
                        "Precio por Plano": [precio_plano],
                        "Costo Total": [costo_total],
                        "Ganancia Neta": [ganancia]
                    })
                    historial = pd.concat([historial, nuevo_registro], ignore_index=True)
                    historial.to_csv(ruta_historial, index=False)
                    st.success(f"✅ Registro guardado correctamente para {tipo_plano} ({planos_hechos} planos).")

    # ===========================
    # BORRAR REGISTROS
    # ===========================
    if len(historial) > 0:
        with st.expander("🗑️ Borrar registros"):
            indices_seleccionados = st.multiselect(
                "Selecciona registros para borrar (ID):",
                options=historial.index,
                format_func=lambda x: f"{x} | {historial.loc[x, 'Fecha']} | {historial.loc[x, 'Tipo de Plano']}"
            )
            if st.button("Borrar seleccionados"):
                if indices_seleccionados:
                    historial.drop(indices_seleccionados, inplace=True)
                    historial.to_csv(ruta_historial, index=False)
                    st.success("✅ Registros eliminados")
                else:
                    st.warning("No se seleccionó ningún registro.")

    # ===========================
    # FILTRO DE FECHAS
    # ===========================
    if len(historial) > 0:
        st.subheader("🔍 Filtrar por rango de fechas")
        min_fecha = historial["Fecha"].min()
        max_fecha = historial["Fecha"].max()

        fecha_inicio, fecha_fin = st.date_input(
            "Selecciona rango de fechas:",
            value=[min_fecha.date(), max_fecha.date()],
            min_value=min_fecha.date(),
            max_value=max_fecha.date()
        )

        historial_filtrado = historial[
            (historial["Fecha"] >= pd.Timestamp(fecha_inicio)) &
            (historial["Fecha"] <= pd.Timestamp(fecha_fin))
        ]
    else:
        historial_filtrado = pd.DataFrame(columns=historial.columns)

    # ===========================
    # HISTORIAL Y GRÁFICOS
    # ===========================
    if len(historial_filtrado) > 0:
        st.header("📚 Historial completo (privado)")
        with st.expander("📋 Mostrar historial completo"):
            st.dataframe(historial_filtrado, use_container_width=True, height=400)

        st.subheader("📊 Métricas")
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Ganancia total", f"${historial_filtrado['Ganancia Neta'].sum():,.0f}")
        col2.metric("🛠️ Costo total", f"${historial_filtrado['Costo Total'].sum():,.0f}")
        col3.metric("📄 Planos totales", f"{historial_filtrado['Planos Hechos'].sum()}")

        # Gráfico de ganancias
        fig_ganancia = px.line()
        for tipo in historial_filtrado["Tipo de Plano"].unique():
            subset = historial_filtrado[historial_filtrado["Tipo de Plano"] == tipo].copy()
            if subset["Semana"].notna().any():
                df_plot = subset.groupby("Semana")["Ganancia Neta"].sum().reset_index()
                fig_ganancia.add_scatter(x=pd.to_datetime(df_plot["Semana"]), y=df_plot["Ganancia Neta"], mode='lines+markers', name=tipo)
            else:
                fig_ganancia.add_scatter(x=pd.to_datetime(subset["Fecha"]), y=subset["Ganancia Neta"], mode='lines+markers', name=tipo)
        fig_ganancia.update_layout(title="Evolución de ganancias por tipo de plano", xaxis_title="Fecha", yaxis_title="Ganancia Neta ($)")
        fig_ganancia = agregar_marca_diagonal(fig_ganancia)
        st.plotly_chart(fig_ganancia, use_container_width=True)

        # Gráfico de producción
        fig_prod = px.line()
        for tipo in historial_filtrado["Tipo de Plano"].unique():
            subset = historial_filtrado[historial_filtrado["Tipo de Plano"] == tipo].copy()
            if subset["Semana"].notna().any():
                df_plot = subset.groupby("Semana")["Planos Hechos"].sum().reset_index()
                fig_prod.add_scatter(x=pd.to_datetime(df_plot["Semana"]), y=df_plot["Planos Hechos"], mode='lines+markers', name=tipo)
            else:
                fig_prod.add_scatter(x=pd.to_datetime(subset["Fecha"]), y=subset["Planos Hechos"], mode='lines+markers', name=tipo)
        fig_prod.update_layout(title="Producción por tipo de plano", xaxis_title="Fecha", yaxis_title="Planos Hechos")
        fig_prod = agregar_marca_diagonal(fig_prod)
        st.plotly_chart(fig_prod, use_container_width=True)

    # ===========================
    # PIE DE PÁGINA
    # ===========================
    st.markdown("---")
    st.caption("© Vlazkou2025")
