import streamlit as st
import pandas as pd
import numpy as np

# COSTE TOTAL
def calcular_coste_total(recepcion_pedidos, necesidades_netas, costo_pedido, costo_mantenimiento):
    """
    - recepcion_pedidos: lista Q_t para cada periodo t
    - necesidades_netas: lista NN_t para cada periodo t
    - costo_pedido: C_p (€/pedido)
    - costo_mantenimiento: h (€/unidad·periodo)
    """
    inv_acumulado = 0
    coste_total_posesion = 0
    coste_total_pedido = 0

    for t in range(len(recepcion_pedidos)):
        # 1) Cada vez que haces un pedido, sumas C_p
        if recepcion_pedidos[t] > 0:
            coste_total_pedido += costo_pedido

        # 2) Actualizas inventario
        inv_acumulado += recepcion_pedidos[t] - necesidades_netas[t]

        # 3) Si es >0, le aplicas coste de mantenimiento
        if inv_acumulado > 0:
            coste_total_posesion += inv_acumulado * costo_mantenimiento

    coste = coste_total_pedido + coste_total_posesion
    return coste, coste_total_posesion, coste_total_pedido


# LOTE A LOTE
def calcular_lote_a_lote(necesidades_brutas, recepciones_programadas, tiempo_suministro, stock_seguridad, disponibilidad_inicial):
    periodos = len(necesidades_brutas)
    disponibilidades = [0] * periodos
    necesidades_netas = [0] * periodos
    recepcion_pedidos = [0] * periodos
    lanzamiento_pedidos = [0] * periodos
    disponible_adicional = [0] * periodos

    # Disponibilidad inicial
    disponibilidades[0] = max(disponibilidad_inicial, stock_seguridad)

    for t in range(periodos):
        if t > 0:
            disponibilidades[t] = max(
                stock_seguridad, 
                recepcion_pedidos[t-1] - necesidades_brutas[t-1] + disponibilidades[t-1] + recepciones_programadas[t-1]
            )
        necesidades_netas[t] = max(
            0, 
            necesidades_brutas[t] - disponibilidades[t] - recepciones_programadas[t] + stock_seguridad
        )
        recepcion_pedidos[t] = necesidades_netas[t]
        lanzamiento_pedidos[t - tiempo_suministro] = recepcion_pedidos[t]
        if t > 0:
            disponible_adicional[t] = disponible_adicional[t-1] - necesidades_netas[t] + recepcion_pedidos[t]
        else:
            disponible_adicional[t] = disponibilidades[t] - necesidades_netas[t] + recepcion_pedidos[t]
    return disponibilidades, necesidades_netas, recepcion_pedidos, lanzamiento_pedidos, disponible_adicional

# EOQ
def calcular_eoq(necesidades_brutas, costo_pedido, costo_mantenimiento, recepciones_programadas, periodos, tiempo_suministro, stock_seguridad, disponibilidad_inicial):
    periodos = len(necesidades_brutas)
    disponibilidades = [0] * periodos
    necesidades_netas = [0] * periodos
    recepcion_pedidos = [0] * periodos
    lanzamiento_pedidos = [0] * periodos
    disponible_adicional = [0] * periodos

    # Disponibilidad inicial
    disponibilidades[0] = max(disponibilidad_inicial, stock_seguridad)

    for t in range(periodos):
        if t > 0:
            disponibilidades[t] = max(
                stock_seguridad,
                recepcion_pedidos[t-1] - necesidades_brutas[t-1] + disponibilidades[t-1] + recepciones_programadas[t-1]
            )
        necesidades_netas[t] = max(
            0,
            necesidades_brutas[t] - disponibilidades[t] - recepciones_programadas[t] + stock_seguridad
        )

    demanda_total = sum(necesidades_netas)
    if demanda_total == 0:
        return disponibilidades, necesidades_netas, recepcion_pedidos, lanzamiento_pedidos, 0, disponible_adicional

    EOQ = int(np.ceil(np.sqrt((2 * demanda_total * costo_pedido) / (costo_mantenimiento * periodos))))
    stock = 0

    for t in range(periodos):
        if stock < necesidades_netas[t]:
            recepcion_pedidos[t] = EOQ
            stock += EOQ
        stock -= necesidades_netas[t]
        lanzamiento_pedidos[t - tiempo_suministro] = recepcion_pedidos[t]
        disponible_adicional[t] = stock

    return disponibilidades, necesidades_netas, recepcion_pedidos, lanzamiento_pedidos, EOQ, disponible_adicional

# PERIODO CONSTANTE
def calcular_periodo_constante(necesidades_brutas, recepciones_programadas, tiempo_suministro, 
                               stock_seguridad, disponibilidad_inicial, periodo_constante):
    periodos = len(necesidades_brutas)
    disponibilidades = [0] * periodos
    necesidades_netas = [0] * periodos
    recepcion_pedidos = [0] * periodos
    lanzamiento_pedidos = [0] * periodos
    disponible_adicional = [0] * periodos

    # Disponibilidad inicial
    disponibilidades[0] = max(disponibilidad_inicial, stock_seguridad)

    for t in range(periodos):
        if t > 0:
            disponibilidades[t] = max(
                stock_seguridad, 
                recepcion_pedidos[t-1] - necesidades_brutas[t-1] + disponibilidades[t-1] + recepciones_programadas[t-1]
            )
        necesidades_netas[t] = max(
            0, 
            necesidades_brutas[t] - disponibilidades[t] - recepciones_programadas[t] + stock_seguridad
        )

    for t in range(periodos):
        if t % periodo_constante == 0:
            valor_periodo = sum(necesidades_netas[t:t+periodo_constante])
            colocado = False
        if necesidades_netas[t] > 0 and not colocado:
            recepcion_pedidos[t] = valor_periodo
            colocado = True
        lanzamiento_pedidos[t - tiempo_suministro] = recepcion_pedidos[t]
        if t > 0:
            disponible_adicional[t] = recepcion_pedidos[t] - necesidades_netas[t] + disponible_adicional[t-1]
        else:
            disponible_adicional[t] = disponibilidades[t] - necesidades_netas[t] + recepcion_pedidos[t]
    return disponibilidades, necesidades_netas, recepcion_pedidos, lanzamiento_pedidos, disponible_adicional

# MÍNIMO COSTE UNITARIO (detalle con columnas: Periodo, NNi, Q, Coste Posesión, Coste Posesión / u, Cost Emisión / u, Cost Total / u)
def calcular_minimo_coste_unitario(necesidades_brutas, recepciones_programadas, tiempo_suministro, 
                                   stock_seguridad, disponibilidad_inicial, costo_pedido, costo_mantenimiento):
    periodos = len(necesidades_brutas)
    disponibilidades = [0] * periodos
    necesidades_netas = [0] * periodos
    recepcion_pedidos = [0] * periodos
    lanzamiento_pedidos = [0] * periodos
    disponible_adicional = [0] * periodos
    disponibilidades[0] = max(disponibilidad_inicial, stock_seguridad)
    for t in range(periodos):
        if t > 0:
            disponibilidades[t] = max(
                stock_seguridad,
                recepcion_pedidos[t-1] - necesidades_brutas[t-1] + disponibilidades[t-1] + recepciones_programadas[t-1]
            )
        necesidades_netas[t] = max(
            0,
            necesidades_brutas[t] - disponibilidades[t] - recepciones_programadas[t] + stock_seguridad
        )

    inicio_ciclo = None
    Q_acumulado = 0
    costo_posesion_acumulado = 0
    prev_unit_cost = None

    periodo_tabla = []
    necesidades_netas_tabla = []
    Q_list = []
    cost_pos_list = []
    cost_pos_por_unidad = []
    cost_emi_por_unidad = []
    cost_total_por_unidad = []

    def registrar_fila(periodo, necesidad, Q_val, cost_pos_val, cost_pos_u, cost_emi_u, cost_tot_u):
        periodo_tabla.append(periodo)
        necesidades_netas_tabla.append(necesidad)
        Q_list.append(Q_val)
        cost_pos_list.append(cost_pos_val)
        cost_pos_por_unidad.append(cost_pos_u)
        cost_emi_por_unidad.append(cost_emi_u)
        cost_total_por_unidad.append(cost_tot_u)

    for t in range(periodos):
        if necesidades_netas[t] > 0 or inicio_ciclo is not None:
            if inicio_ciclo is None:
                inicio_ciclo = t
                Q_acumulado = necesidades_netas[t]
                costo_posesion_acumulado = 0
                unit_cost = (costo_pedido / Q_acumulado) if Q_acumulado else 0
                prev_unit_cost = unit_cost
                registrar_fila(
                    periodo=t+1,
                    necesidad=necesidades_netas[t],
                    Q_val=Q_acumulado,
                    cost_pos_val=costo_posesion_acumulado,
                    cost_pos_u=0,
                    cost_emi_u=(costo_pedido / Q_acumulado if Q_acumulado else 0),
                    cost_tot_u=unit_cost
                )
            else:
                Q_nuevo = Q_acumulado + necesidades_netas[t]
                costo_adicional = (t - inicio_ciclo) * costo_mantenimiento * necesidades_netas[t]
                costo_posesion_nuevo = costo_posesion_acumulado + costo_adicional
                unit_cost_nuevo = ((costo_pedido + costo_posesion_nuevo) / Q_nuevo) if Q_nuevo else 0
                registrar_fila(
                    periodo=t+1,
                    necesidad=necesidades_netas[t],
                    Q_val=Q_nuevo,
                    cost_pos_val=costo_posesion_nuevo,
                    cost_pos_u=(costo_posesion_nuevo / Q_nuevo if Q_nuevo else 0),
                    cost_emi_u=(costo_pedido / Q_nuevo if Q_nuevo else 0),
                    cost_tot_u=unit_cost_nuevo
                )
                if unit_cost_nuevo > prev_unit_cost:
                    recepcion_pedidos[inicio_ciclo] = Q_acumulado
                    lanzamiento_pedidos[inicio_ciclo - tiempo_suministro] = recepcion_pedidos[inicio_ciclo]
                    inicio_ciclo = t
                    Q_acumulado = necesidades_netas[t]
                    costo_posesion_acumulado = 0
                    unit_cost_nuevo = (costo_pedido / Q_acumulado) if Q_acumulado else 0
                    prev_unit_cost = unit_cost_nuevo
                    registrar_fila(
                        periodo=t+1,
                        necesidad=necesidades_netas[t],
                        Q_val=Q_acumulado,
                        cost_pos_val=costo_posesion_acumulado,
                        cost_pos_u=0,
                        cost_emi_u=(costo_pedido / Q_acumulado if Q_acumulado else 0),
                        cost_tot_u=unit_cost_nuevo
                    )
                elif unit_cost_nuevo == prev_unit_cost:
                    if any(n > 0 for n in necesidades_netas[t+1:]):
                        Q_acumulado = Q_nuevo
                        costo_posesion_acumulado = costo_posesion_nuevo
                        prev_unit_cost = unit_cost_nuevo
                    else:
                        recepcion_pedidos[inicio_ciclo] = Q_acumulado
                        lanzamiento_pedidos[inicio_ciclo - tiempo_suministro] = recepcion_pedidos[inicio_ciclo]
                        inicio_ciclo = None
                        Q_acumulado = 0
                        costo_posesion_acumulado = 0
                        prev_unit_cost = None
                else:
                    Q_acumulado = Q_nuevo
                    costo_posesion_acumulado = costo_posesion_nuevo
                    prev_unit_cost = unit_cost_nuevo

    if inicio_ciclo is not None and Q_acumulado > 0:
        recepcion_pedidos[inicio_ciclo] = Q_acumulado
        lanzamiento_pedidos[inicio_ciclo - tiempo_suministro] = recepcion_pedidos[inicio_ciclo]
    
    return {
        "disponibilidades": disponibilidades,
        "necesidades_netas": necesidades_netas,
        "recepcion_pedidos": recepcion_pedidos,
        "lanzamiento_pedidos": lanzamiento_pedidos,
        "disponible_adicional": disponible_adicional,
        "periodo_tabla": periodo_tabla,
        "necesidades_netas_tabla": necesidades_netas_tabla,
        "Q": Q_list,
        "coste_posesion": cost_pos_list,
        "coste_posesion_por_unidad": cost_pos_por_unidad,
        "coste_emision_por_unidad": cost_emi_por_unidad,
        "coste_total_por_unidad": cost_total_por_unidad
    }

# MINIMO COSTE TOTAL  
# En esta función el coste de emisión es siempre costo_pedido (no se divide), y la desviación se calcula como |coste_posesion - costo_pedido|
def calcular_minimo_coste_total(necesidades_brutas, recepciones_programadas, tiempo_suministro, 
                                stock_seguridad, disponibilidad_inicial, costo_pedido, costo_mantenimiento):
    periodos = len(necesidades_brutas)
    disponibilidades = [0] * periodos
    necesidades_netas = [0] * periodos
    recepcion_pedidos = [0] * periodos
    lanzamiento_pedidos = [0] * periodos
    disponible_adicional = [0] * periodos

    # Calcular disponibilidades y necesidades netas
    disponibilidades[0] = max(disponibilidad_inicial, stock_seguridad)
    for t in range(periodos):
        if t > 0:
            disponibilidades[t] = max(
                stock_seguridad,
                recepcion_pedidos[t-1] - necesidades_brutas[t-1]
                + disponibilidades[t-1] + recepciones_programadas[t-1]
            )
        necesidades_netas[t] = max(
            0,
            necesidades_brutas[t] - disponibilidades[t] - recepciones_programadas[t] + stock_seguridad
        )

    # Variables para la lógica de acumulación
    inicio_ciclo = None            
    Q_acumulado = 0                
    costo_posesion_acumulado = 0   
    prev_desviacion = None         

    # Listas para la tabla final
    periodo_tabla = []
    necesidades_netas_tabla = []
    Q_list = []
    coste_posesion_list = []
    coste_emision_list = []
    desviacion_list = []

    # Función para registrar una fila
    def registrar_fila(periodo, necesidad, Q_val, coste_pos_val):

        coste_emision_val = costo_pedido
        desviacion_val = abs(coste_pos_val - coste_emision_val)

        periodo_tabla.append(periodo)
        necesidades_netas_tabla.append(necesidad)
        Q_list.append(Q_val)
        coste_posesion_list.append(coste_pos_val)
        coste_emision_list.append(coste_emision_val)
        desviacion_list.append(desviacion_val)

        return desviacion_val  # Devolvemos la desviación para compararla afuera

    # Bucle principal
    for t in range(periodos):
        # Solo procesamos si hay necesidad en este periodo o si ya se inició un ciclo
        if necesidades_netas[t] > 0 or inicio_ciclo is not None:
            if inicio_ciclo is None:
                # Iniciar ciclo en este periodo
                inicio_ciclo = t
                Q_acumulado = necesidades_netas[t]
                costo_posesion_acumulado = 0
                # Registramos la fila (desviacion_inicial)
                desviacion_nueva = registrar_fila(periodo=t+1,
                                                  necesidad=necesidades_netas[t],
                                                  Q_val=Q_acumulado,
                                                  coste_pos_val=costo_posesion_acumulado)
                prev_desviacion = desviacion_nueva
            else:
                # Acumulamos
                Q_nuevo = Q_acumulado + necesidades_netas[t]
                # Coste adicional de posesión
                costo_adicional = (t - inicio_ciclo) * costo_mantenimiento * necesidades_netas[t]
                costo_posesion_nuevo = costo_posesion_acumulado + costo_adicional

                # Registramos la fila y calculamos la desviación nueva
                desviacion_nueva = registrar_fila(periodo=t+1,
                                                  necesidad=necesidades_netas[t],
                                                  Q_val=Q_nuevo,
                                                  coste_pos_val=costo_posesion_nuevo)

                # Comparamos la desviación
                if desviacion_nueva > prev_desviacion:
                    # El mínimo relativo se produjo en el paso anterior
                    # Fijamos el pedido en el periodo "inicio_ciclo"
                    recepcion_pedidos[inicio_ciclo] = Q_acumulado
                    lanzamiento_pedidos[inicio_ciclo - tiempo_suministro] = recepcion_pedidos[inicio_ciclo]

                    # Reiniciamos el ciclo en este periodo
                    inicio_ciclo = t
                    Q_acumulado = necesidades_netas[t]
                    costo_posesion_acumulado = 0
                    # Registramos la "segunda fila" para el mismo periodo t
                    desviacion_nueva = registrar_fila(periodo=t+1,
                                                      necesidad=necesidades_netas[t],
                                                      Q_val=Q_acumulado,
                                                      coste_pos_val=costo_posesion_acumulado)
                    prev_desviacion = desviacion_nueva

                elif desviacion_nueva == prev_desviacion:
                    # Si es igual, comprobamos si quedan necesidades futuras
                    if any(n > 0 for n in necesidades_netas[t+1:]):
                        Q_acumulado = Q_nuevo
                        costo_posesion_acumulado = costo_posesion_nuevo
                        prev_desviacion = desviacion_nueva
                    else:
                        # No quedan necesidades futuras
                        recepcion_pedidos[inicio_ciclo] = Q_acumulado
                        lanzamiento_pedidos[inicio_ciclo - tiempo_suministro] = recepcion_pedidos[inicio_ciclo]
                        inicio_ciclo = None
                        Q_acumulado = 0
                        costo_posesion_acumulado = 0
                        prev_desviacion = None
                else:
                    # Si la desviación ha disminuido
                    Q_acumulado = Q_nuevo
                    costo_posesion_acumulado = costo_posesion_nuevo
                    prev_desviacion = desviacion_nueva

    # Si al finalizar el bucle queda un ciclo abierto, se programa el pedido final
    if inicio_ciclo is not None and Q_acumulado > 0:
        recepcion_pedidos[inicio_ciclo] = Q_acumulado
        lanzamiento_pedidos[inicio_ciclo - tiempo_suministro] = recepcion_pedidos[inicio_ciclo]

    # Devolvemos todos los vectores
    return {
        "disponibilidades": disponibilidades,
        "necesidades_netas": necesidades_netas,
        "recepcion_pedidos": recepcion_pedidos,
        "lanzamiento_pedidos": lanzamiento_pedidos,
        "disponible_adicional": disponible_adicional,
        "periodo_tabla": periodo_tabla,
        "necesidades_netas_tabla": necesidades_netas_tabla,
        "Q": Q_list,
        "coste_posesion": coste_posesion_list,
        "coste_emision": coste_emision_list,
        "desviacion": desviacion_list
    }


def calcular_silver_meal(necesidades_brutas, recepciones_programadas, tiempo_suministro, 
                         stock_seguridad, disponibilidad_inicial, costo_pedido, costo_mantenimiento):
    periodos = len(necesidades_brutas)
    disponibilidades = [0] * periodos
    necesidades_netas = [0] * periodos
    recepcion_pedidos = [0] * periodos
    lanzamiento_pedidos = [0] * periodos
    disponible_adicional = [0] * periodos

    # Cálculo de disponibilidades y necesidades netas
    disponibilidades[0] = max(disponibilidad_inicial, stock_seguridad)
    for t in range(periodos):
        if t > 0:
            disponibilidades[t] = max(
                stock_seguridad,
                recepcion_pedidos[t-1] - necesidades_brutas[t-1] 
                + disponibilidades[t-1] + recepciones_programadas[t-1]
            )
        necesidades_netas[t] = max(
            0,
            necesidades_brutas[t] - disponibilidades[t] - recepciones_programadas[t] + stock_seguridad
        )

    # Variables para la lógica de Silver-Meal
    inicio_ciclo = None            # Periodo donde comienza la acumulación
    Q_acumulado = 0                # Acumulación de necesidades netas
    costo_posesion_acumulado = 0   # Coste de posesión acumulado
    contador_periodos = 0          # Número de periodos que llevamos en el ciclo (incluyendo periodos con NN=0 si ya empezó)
    prev_silver_meal_val = None    # Valor anterior de la fórmula

    # Listas para la tabla final
    periodo_tabla = []
    necesidades_netas_tabla = []
    Q_list = []
    coste_posesion_list = []
    coste_emision_list = []
    silver_meal_list = []  # (coste_posesion + coste_emision) / contador_periodos

    def registrar_fila(periodo, necesidad, Q_val, coste_pos_val, num_periodos):
        """
        Añade una fila a las listas de resultados.
        cost_emision = costo_pedido (fijo).
        silver_meal_val = (coste_pos_val + costo_pedido) / num_periodos.
        """
        coste_emision_val = costo_pedido
        silver_val = (coste_pos_val + coste_emision_val) / num_periodos

        periodo_tabla.append(periodo)
        necesidades_netas_tabla.append(necesidad)
        Q_list.append(Q_val)
        coste_posesion_list.append(coste_pos_val)
        coste_emision_list.append(coste_emision_val)
        silver_meal_list.append(silver_val)

        return silver_val  # devolvemos el valor para comparar afuera

    # Bucle principal
    for t in range(periodos):
        # Si no hay necesidades netas y aún no hemos iniciado un ciclo, no hacemos nada
        if inicio_ciclo is None and necesidades_netas[t] == 0:
            continue

        if inicio_ciclo is None:
            # Primer periodo con NN>0: iniciamos el ciclo
            inicio_ciclo = t
            Q_acumulado = necesidades_netas[t]
            costo_posesion_acumulado = 0
            contador_periodos = 1  # Empezamos contando este periodo
            silver_val_inicial = registrar_fila(periodo=t+1,
                                                necesidad=necesidades_netas[t],
                                                Q_val=Q_acumulado,
                                                coste_pos_val=costo_posesion_acumulado,
                                                num_periodos=contador_periodos)
            prev_silver_meal_val = silver_val_inicial
        else:
            # Ya estamos en un ciclo
            contador_periodos += 1  # Avanzamos un periodo (aunque NN=0, se cuenta)
            if necesidades_netas[t] > 0:
                # Acumulamos la NN de este periodo
                Q_nuevo = Q_acumulado + necesidades_netas[t]
                # Coste adicional de posesión
                costo_adicional = (t - inicio_ciclo) * costo_mantenimiento * necesidades_netas[t]
                costo_posesion_nuevo = costo_posesion_acumulado + costo_adicional

                # Calculamos el nuevo valor de Silver-Meal
                silver_meal_nuevo = registrar_fila(periodo=t+1,
                                                   necesidad=necesidades_netas[t],
                                                   Q_val=Q_nuevo,
                                                   coste_pos_val=costo_posesion_nuevo,
                                                   num_periodos=contador_periodos)
                # Comparamos
                if silver_meal_nuevo > prev_silver_meal_val:
                    # El mínimo relativo se produjo en el periodo anterior
                    recepcion_pedidos[inicio_ciclo] = Q_acumulado
                    lanzamiento_pedidos[inicio_ciclo - tiempo_suministro] = recepcion_pedidos[inicio_ciclo]

                    # Reiniciamos el ciclo en este periodo
                    inicio_ciclo = t
                    Q_acumulado = necesidades_netas[t]
                    costo_posesion_acumulado = 0
                    contador_periodos = 1  # este periodo se cuenta como el primero del nuevo ciclo

                    # Registramos la "segunda fila" para el mismo t
                    silver_meal_nuevo2 = registrar_fila(periodo=t+1,
                                                        necesidad=necesidades_netas[t],
                                                        Q_val=Q_acumulado,
                                                        coste_pos_val=costo_posesion_acumulado,
                                                        num_periodos=contador_periodos)
                    prev_silver_meal_val = silver_meal_nuevo2
                elif silver_meal_nuevo == prev_silver_meal_val:
                    # Si es igual, comprobamos si hay NN futuras
                    if any(n > 0 for n in necesidades_netas[t+1:]):
                        Q_acumulado = Q_nuevo
                        costo_posesion_acumulado = costo_posesion_nuevo
                        prev_silver_meal_val = silver_meal_nuevo
                    else:
                        # No quedan NN futuras
                        recepcion_pedidos[inicio_ciclo] = Q_acumulado
                        lanzamiento_pedidos[inicio_ciclo - tiempo_suministro] = recepcion_pedidos[inicio_ciclo]
                        inicio_ciclo = None
                        Q_acumulado = 0
                        costo_posesion_acumulado = 0
                        contador_periodos = 0
                        prev_silver_meal_val = None
                else:
                    # Si ha bajado, seguimos acumulando
                    Q_acumulado = Q_nuevo
                    costo_posesion_acumulado = costo_posesion_nuevo
                    prev_silver_meal_val = silver_meal_nuevo
            else:
                # NN[t] == 0, incrementamos contador_periodos, pero NO registramos fila
                # (según la especificación, ignoramos ese periodo en la tabla).
                # No se altera Q_acumulado ni coste_posesion_acumulado.
                # Solo seguimos con la comparación en periodos futuros.
                pass

    # Si al final queda un ciclo abierto, programamos el pedido final
    if inicio_ciclo is not None and Q_acumulado > 0:
        recepcion_pedidos[inicio_ciclo] = Q_acumulado
        lanzamiento_pedidos[inicio_ciclo - tiempo_suministro] = recepcion_pedidos[inicio_ciclo]

    # Devolvemos resultados
    return {
        "disponibilidades": disponibilidades,
        "necesidades_netas": necesidades_netas,
        "recepcion_pedidos": recepcion_pedidos,
        "lanzamiento_pedidos": lanzamiento_pedidos,
        "disponible_adicional": disponible_adicional,
        "periodo_tabla": periodo_tabla,
        "necesidades_netas_tabla": necesidades_netas_tabla,
        "Q": Q_list,
        "coste_posesion": coste_posesion_list,
        "coste_emision": coste_emision_list,
        "silver_meal_value": silver_meal_list
    }


# Main de Streamlit
def main():
    st.title("Planificación de las Necesidades de Materiales")
    metodos = [
        "Lote a Lote",
        "Periodo Constante",
        "Minimo Coste Unitario",
        "Minimo Coste Total",
        "Silver Meal",
        "Coste Total de Todas"
    ]
    metodo = st.selectbox("Seleccione un método", metodos)

    # Parámetro extra para método Periodo Constante si se elige individual
    if metodo == "Periodo Constante":
        periodo_constante = st.number_input(
            "Periodo constante", min_value=1, step=1, value=2,
            format="%d"
        )

    periodos = st.number_input(
        "Número de períodos", min_value=1, step=1, value=8,
        format="%d"
    )
    tiempo_suministro = st.number_input(
        "Tiempo de suministro", min_value=1, step=1, value=1,
        format="%d"
    )
    stock_seguridad = st.number_input(
        "Stock de seguridad", min_value=0, step=1, value=0,
        format="%d"
    )
    disponibilidad_inicial = st.number_input(
        "Disponibilidad inicial (Semana 1)", step=1, value=0,
        format="%d"
    )

    costo_pedido = st.number_input(
        "Costo de realizar un pedido (€/pedido)",
        min_value=1, step=1, value=1000,
        format="%d"
    )
    costo_mantenimiento = st.number_input(
        "Costo de mantenimiento por unidad (€/unidad y periodo)",
        min_value=0.0, step=0.1, value=1.0,
        format="%.1f"
    )

    def input_row(label, key_prefix, default_values, periodos):
        st.write(f"### {label}")
        if len(default_values) < periodos:
            default_values = default_values + [0] * (periodos - len(default_values))
        else:
            default_values = default_values[:periodos]

        cols = st.columns(periodos)
        for i, col in enumerate(cols):
            with col:
                st.markdown(
                    f"<div style='text-align: center; font-weight: bold;'>{i+1}</div>",
                    unsafe_allow_html=True
                )
        return [
            cols[i].number_input(
                "", min_value=0, step=1,
                key=f"{key_prefix}_{i}",
                value=default_values[i],
                format="%d"
            )
            for i in range(periodos)
        ]

    necesidades_brutas_defaults = [0, 0, 0, 0, 0, 0, 0, 0]
    recepciones_programadas_defaults = [0] * periodos

    necesidades_brutas = input_row(
        "Necesidades Brutas",
        "nb",
        necesidades_brutas_defaults,
        periodos
    )
    recepciones_programadas = input_row(
        "Recepciones Programadas",
        "rp",
        recepciones_programadas_defaults,
        periodos
    )

    if st.button("Calcular"):
        # Coste Total de Todas
        if metodo == "Coste Total de Todas":
            # Lote a Lote
            d_lote, nn_lote, q_lote, l_lote, _ = calcular_lote_a_lote(
                necesidades_brutas, recepciones_programadas,
                tiempo_suministro, stock_seguridad,
                disponibilidad_inicial
            )
            coste_lote, _, _ = calcular_coste_total(
                q_lote, nn_lote, costo_pedido, costo_mantenimiento
            )
            # Periodo Constante para varios periodos: 2, 3 y 4
            costes_pc = []
            for pc in (2, 3, 4):
                d_pc, nn_pc, q_pc, l_pc, _ = calcular_periodo_constante(
                    necesidades_brutas, recepciones_programadas,
                    tiempo_suministro, stock_seguridad,
                    disponibilidad_inicial, pc
                )
                c_pc, _, _ = calcular_coste_total(
                    q_pc, nn_pc, costo_pedido, costo_mantenimiento
                )
                costes_pc.append((pc, c_pc))
            # Minimo Coste Unitario
            res_mcu = calcular_minimo_coste_unitario(
                necesidades_brutas, recepciones_programadas,
                tiempo_suministro, stock_seguridad,
                disponibilidad_inicial, costo_pedido,
                costo_mantenimiento
            )
            coste_mcu, _, _ = calcular_coste_total(
                res_mcu["recepcion_pedidos"],
                res_mcu["necesidades_netas"],
                costo_pedido, costo_mantenimiento
            )
            # Minimo Coste Total
            res_mct = calcular_minimo_coste_total(
                necesidades_brutas, recepciones_programadas,
                tiempo_suministro, stock_seguridad,
                disponibilidad_inicial, costo_pedido,
                costo_mantenimiento
            )
            coste_mct, _, _ = calcular_coste_total(
                res_mct["recepcion_pedidos"],
                res_mct["necesidades_netas"],
                costo_pedido, costo_mantenimiento
            )
            # Silver Meal
            res_sm = calcular_silver_meal(
                necesidades_brutas, recepciones_programadas,
                tiempo_suministro, stock_seguridad,
                disponibilidad_inicial, costo_pedido,
                costo_mantenimiento
            )
            coste_sm, _, _ = calcular_coste_total(
                res_sm["recepcion_pedidos"],
                res_sm["necesidades_netas"],
                costo_pedido, costo_mantenimiento
            )

            # Preparar DataFrame
            estrategias = ["Lote a Lote"] + [f"Periodo Constante ({pc})" for pc, _ in costes_pc] + [
                "Minimo Coste Unitario",
                "Minimo Coste Total",
                "Silver Meal"
            ]
            costes = [coste_lote] + [c for _, c in costes_pc] + [
                coste_mcu,
                coste_mct,
                coste_sm
            ]
            df_costes = pd.DataFrame({
                "Estrategia": estrategias,
                "Coste Total (€)": costes
            }).set_index("Estrategia")
            st.subheader("Costes Totales por Estrategia")
            st.dataframe(df_costes.style.format("{:.0f}"))
            return

        # Cálculo según método individual 
        if metodo == "Lote a Lote":
            disponibilidades, necesidades_netas, recepcion_pedidos, lanzamiento_pedidos, _ = calcular_lote_a_lote(
                necesidades_brutas, recepciones_programadas,
                tiempo_suministro, stock_seguridad,
                disponibilidad_inicial
            )
        elif metodo == "Periodo Constante":
            disponibilidades, necesidades_netas, recepcion_pedidos, lanzamiento_pedidos, _ = calcular_periodo_constante(
                necesidades_brutas, recepciones_programadas,
                tiempo_suministro, stock_seguridad,
                disponibilidad_inicial, periodo_constante
            )
        elif metodo == "Minimo Coste Unitario":
            resultados = calcular_minimo_coste_unitario(
                necesidades_brutas, recepciones_programadas,
                tiempo_suministro, stock_seguridad,
                disponibilidad_inicial, costo_pedido,
                costo_mantenimiento
            )
            disponibilidades = resultados["disponibilidades"]
            necesidades_netas = resultados["necesidades_netas"]
            recepcion_pedidos = resultados["recepcion_pedidos"]
            lanzamiento_pedidos = resultados["lanzamiento_pedidos"]
        elif metodo == "Minimo Coste Total":
            resultados = calcular_minimo_coste_total(
                necesidades_brutas, recepciones_programadas,
                tiempo_suministro, stock_seguridad,
                disponibilidad_inicial, costo_pedido,
                costo_mantenimiento
            )
            disponibilidades = resultados["disponibilidades"]
            necesidades_netas = resultados["necesidades_netas"]
            recepcion_pedidos = resultados["recepcion_pedidos"]
            lanzamiento_pedidos = resultados["lanzamiento_pedidos"]
        else:  # Silver Meal
            resultados = calcular_silver_meal(
                necesidades_brutas, recepciones_programadas,
                tiempo_suministro, stock_seguridad,
                disponibilidad_inicial, costo_pedido,
                costo_mantenimiento
            )
            disponibilidades = resultados["disponibilidades"]
            necesidades_netas = resultados["necesidades_netas"]
            recepcion_pedidos = resultados["recepcion_pedidos"]
            lanzamiento_pedidos = resultados["lanzamiento_pedidos"]

        # --- Cálculo de costes totales individual ---
        coste, coste_total_posesion, coste_total_pedido = calcular_coste_total(
            recepcion_pedidos, necesidades_netas,
            costo_pedido, costo_mantenimiento
        )

        st.markdown(f"""
        <div style='text-align: center;'>
            <p style='font-size:42px;'><strong>{metodo}</strong></p>
            <p style='font-size:28px;'>Coste total de pedido: {coste_total_pedido} €</p>
            <p style='font-size:28px;'>Coste total de posesión: {coste_total_posesion} €</p>
            <p style='font-size:40px; color:green; font-weight:bold;'>Coste total: {coste} €</p>
        </div>
        """, unsafe_allow_html=True)

                # Tabla
        launch_positions = [(i+1 - tiempo_suministro) for i in range(periodos) if recepcion_pedidos[i] > 0]
        min_launch = min(launch_positions) if launch_positions else 1
        start_col = min_launch if min_launch <= 0 else 1
        all_cols = list(range(start_col, periodos + 1))
        rows = {
            "Necesidades Brutas":      {i+1: necesidades_brutas[i] for i in range(periodos)},
            "Disponibilidades":        {i+1: disponibilidades[i]    for i in range(periodos)},
            "Recepciones Programadas": {i+1: recepciones_programadas[i] for i in range(periodos)},
            "Necesidades Netas":       {i+1: necesidades_netas[i]   for i in range(periodos)},
            "Recepción de Pedidos":    {i+1: recepcion_pedidos[i]   for i in range(periodos)},
            "Lanzamiento de Pedidos":  {(i+1 - tiempo_suministro): recepcion_pedidos[i] for i in range(periodos)}
        }
        data_aux = {name: [mapping.get(col, 0) for col in all_cols] for name, mapping in rows.items()}
        df_aux = pd.DataFrame(data_aux, index=[str(c) for c in all_cols]).T
        st.markdown("<h2 style='text-align: center;'>Resultados</h2>", unsafe_allow_html=True)
        st.dataframe(
            df_aux.style.format("{:.0f}"),
            use_container_width=True
        )

        # Mostrar detalle para métodos especiales
        if metodo == "Minimo Coste Unitario":
            st.markdown("## Detalle del cálculo de Mínimo Coste Unitario")
            data_detalle = {
                "Periodo": resultados["periodo_tabla"],
                "NNi": resultados["necesidades_netas_tabla"],
                "Q": resultados["Q"],
                "Coste Posesión": resultados["coste_posesion"],
                "Cost Posesión / u": resultados["coste_posesion_por_unidad"],
                "Cost Emisión / u": resultados["coste_emision_por_unidad"],
                "Cost Total / u": resultados["coste_total_por_unidad"]
            }
            df_detalle = pd.DataFrame(data_detalle)
            st.dataframe(df_detalle)

        elif metodo == "Minimo Coste Total":
            st.markdown("## Detalle del cálculo de Mínimo Coste Total")
            data_detalle = {
                "Periodo": resultados["periodo_tabla"],
                "NNi": resultados["necesidades_netas_tabla"],
                "Q": resultados["Q"],
                "Coste Posesión": resultados["coste_posesion"],
                "Coste Emisión": resultados["coste_emision"],
                "Desviación": resultados["desviacion"]
            }
            df_detalle = pd.DataFrame(data_detalle)
            st.dataframe(df_detalle)

        elif metodo == "Silver Meal":
            st.markdown("## Detalle del cálculo de Silver Meal")
            data_detalle = {
                "Periodo": resultados["periodo_tabla"],
                "NNi": resultados["necesidades_netas_tabla"],
                "Q": resultados["Q"],
                "Coste Posesión": resultados["coste_posesion"],
                "Coste Emisión": resultados["coste_emision"],
                "Silver Meal": resultados["silver_meal_value"]
            }
            df_detalle = pd.DataFrame(data_detalle)
            st.dataframe(df_detalle)



if __name__ == "__main__":
    main()
