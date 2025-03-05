import streamlit as st
import pandas as pd
import numpy as np

def calcular_lote_a_lote(necesidades_brutas, recepciones_programadas, tiempo_suministro, stock_seguridad, disponibilidad_inicial):
    periodos = len(necesidades_brutas)
    disponibilidades = [0] * periodos
    necesidades_netas = []
    recepcion_pedidos = []
    lanzamiento_pedidos = [0] * periodos
    
    disponibilidades[0] = max(disponibilidad_inicial, stock_seguridad)
    
    for t in range(periodos):
        if t > 0:
            disponibilidades[t] = max(0, recepcion_pedidos[t-1] - necesidades_brutas[t-1] + disponibilidades[t-1] + recepciones_programadas[t-1])
        
        necesidad_neta = max(0, necesidades_brutas[t] - disponibilidades[t] - recepciones_programadas[t] + stock_seguridad)
        necesidades_netas.append(necesidad_neta)
        
        recepcion_pedidos.append(necesidad_neta)
        
        if t >= tiempo_suministro:
            lanzamiento_pedidos[t - tiempo_suministro + 1] = necesidad_neta
    
    return disponibilidades, necesidades_netas, recepcion_pedidos, lanzamiento_pedidos

def main():
    st.title("Calculadora de Métodos de Planificación de Inventario")
    metodos = ["Lote a Lote"]
    metodo = st.selectbox("Seleccione un método", metodos)
    
    periodos = st.number_input("Número de períodos", min_value=1, step=1, value=8)
    tiempo_suministro = st.number_input("Tiempo de suministro", min_value=1, step=1, value=1)
    stock_seguridad = st.number_input("Stock de seguridad", min_value=0, step=1, value=40)
    disponibilidad_inicial = st.number_input("Disponibilidad inicial (Semana 1)", min_value=stock_seguridad, step=1, value=90)
    
    if metodo == "Lote a Lote":
        st.subheader("Ingrese los datos por período")
        
        def input_row(label, key_prefix, default_values):
            st.write(f"### {label}")
            cols = st.columns(periodos)
            for i, col in enumerate(cols):
                with col:
                    st.markdown(f"<div style='text-align: center; font-weight: bold;'>{i+1}</div>", unsafe_allow_html=True)
            return [cols[i].number_input("", min_value=0, step=1, key=f"{key_prefix}_{i}", value=default_values[i]) for i in range(periodos)]
        
        necesidades_brutas_defaults = [0, 560, 1480, 200, 1200, 1800, 0, 200]
        recepciones_programadas_defaults = [0, 0, 0, 0, 0, 0, 0, 0]
        
        necesidades_brutas = input_row("Necesidades Brutas", "nb", necesidades_brutas_defaults)
        recepciones_programadas = input_row("Recepciones Programadas", "rp", recepciones_programadas_defaults)
        
        if st.button("Calcular"):
            disponibilidades, necesidades_netas, recepcion_pedidos, lanzamiento_pedidos = calcular_lote_a_lote(necesidades_brutas, recepciones_programadas, tiempo_suministro, stock_seguridad, disponibilidad_inicial)
            
            st.subheader("Resultados")
            def output_row(label, values):
                st.write(f"### {label}")
                cols = st.columns(periodos)
                for i, col in enumerate(cols):
                    with col:
                        st.markdown(f"<div style='text-align: center; font-weight: bold;'>{i+1}</div>", unsafe_allow_html=True)
                for i, col in enumerate(cols):
                    with col:
                        st.text(values[i])
            
            output_row("Necesidades Brutas", necesidades_brutas)
            output_row("Disponibilidades", disponibilidades)
            output_row("Recepciones Programadas", recepciones_programadas)
            output_row("Necesidades Netas", necesidades_netas)
            output_row("Recepción de Pedidos", recepcion_pedidos)
            output_row("Lanzamiento de Pedidos", lanzamiento_pedidos)

if __name__ == "__main__":
    main()
