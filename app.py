import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# --- CONFIGURACIÓN DE LA PÁGINA WEB ---
st.set_page_config(page_title="Diagnóstico A.R.M. | VFC", layout="wide")
st.title("Arquitectura de Resiliencia Multidimensional (A.R.M.)")
st.subheader("Plataforma de Diagnóstico Autonómico y Neuroquímico")

# --- PROTOCOLOS CLÍNICOS ---
PROTOCOLOS = {
    'ELITE': {'Neuro': 'Dopamina de Control / H&A Óptimo', 'Accion': 'Optimización: Alta complejidad cognitiva.', 'Color': '#008000'},
    'OPTIMO': {'Neuro': 'Dopamina Estable', 'Accion': 'Mantenimiento: Continuar rutina actual.', 'Color': '#32CD32'},
    'ALERTA': {'Neuro': 'Dominancia Cortisol', 'Accion': 'Sostenibilidad: Pausas activas e hidratación.', 'Color': '#FFA500'},
    'RIESGO': {'Neuro': 'Agotamiento Serotonina', 'Accion': 'Recuperación: Descanso absoluto y respiración 4-7-8.', 'Color': '#FF0000'}
}

def calculate_rmssd(series):
    if len(series) < 15: return np.nan
    diffs = np.diff(series)
    diffs = diffs[np.abs(diffs) < 250]
    return np.sqrt(np.mean(diffs ** 2)) if len(diffs) > 10 else np.nan

def get_zone(vfc, br):
    if vfc >= 100 and br <= 14: return 'ELITE'
    elif vfc >= 40: return 'OPTIMO' if vfc >= 60 else 'ALERTA'
    else: return 'RIESGO'

st.markdown("### 1. Carga de Datos Biométricos")
st.info("Sube el archivo CSV exportado con los datos de intervalos de latidos (BBI) de Garmin.")
uploaded_files = st.file_uploader("Subir CSV de Garmin", type=['csv'], accept_multiple_files=True)

if uploaded_files:
    all_people_data = []
    for file in uploaded_files:
        if 'bbi' in file.name.lower():
            try:
                df_bbi = pd.read_csv(file, skiprows=6)
                df_bbi['dt'] = pd.to_datetime(df_bbi['isoDate'])
                df_bbi = df_bbi[df_bbi['dt'].dt.hour.isin([0, 1, 2, 3, 4, 5])] # Ventana de sueño nocturno
                
                if len(df_bbi) >= 60:
                    vfc_val = calculate_rmssd(df_bbi['bbi'])
                    hr_val = 60000 / df_bbi['bbi'].median()
                    avg_br = 14.0 # Base estándar si no hay datos respiratorios
                    
                    if 15 < vfc_val < 250:
                        all_people_data.append({
                            'Fecha': df_bbi['dt'].dt.date.iloc[0],
                            'VFC_ms': vfc_val, 
                            'RHR_bpm': hr_val, 
                            'BR_pm': avg_br
                        })
            except Exception as e:
                st.error(f"Error procesando {file.name}: {e}")

    if all_people_data:
        df_all = pd.DataFrame(all_people_data).sort_values('Fecha')
        df_all['Zona'] = df_all.apply(lambda row: get_zone(row['VFC_ms'], row['BR_pm']), axis=1)
        
        st.markdown("### 2. Resultados del Diagnóstico")
        col1, col2, col3 = st.columns(3)
        col1.metric("VFC Promedio", f"{df_all['VFC_ms'].mean():.1f} ms")
        col2.metric("Gasto Metabólico (8h)", f"{int(df_all['RHR_bpm'].mean()*60*8):,} latidos")
        col3.metric("Estado Predominante", df_all['Zona'].mode()[0])

        st.markdown("#### Tendencia de Variabilidad de Frecuencia Cardíaca (VFC)")
        fig, ax = plt.subplots(figsize=(10, 4))
        sns.lineplot(data=df_all, x='Fecha', y='VFC_ms', marker='o', ax=ax, color='black')
        ax.axhspan(0, 40, facecolor='red', alpha=0.15, label='Riesgo')
        ax.axhspan(40, 100, facecolor='yellow', alpha=0.15, label='Mantenimiento')
        ax.axhspan(100, 220, facecolor='green', alpha=0.15, label='Élite')
        plt.xticks(rotation=45)
        st.pyplot(fig)

        st.markdown("#### Plan de Intervención por Día")
        df_display = df_all[['Fecha', 'VFC_ms', 'Zona']].copy()
        df_display['Neuroquímica'] = df_display['Zona'].map(lambda z: PROTOCOLOS[z]['Neuro'])
        df_display['Acción Inmediata'] = df_display['Zona'].map(lambda z: PROTOCOLOS[z]['Accion'])
        st.dataframe(df_display, use_container_width=True)
        st.success("Análisis clínico completado. Procesamiento A.R.M. finalizado.")
