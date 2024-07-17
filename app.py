import streamlit as st
import pandas as pd
import pydeck as pdk
import numpy as np
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt

sidebar_logo="./Logo.png"
main_body_logo="./Iso.png"
st.sidebar.image(sidebar_logo, width=200)
st.image(main_body_logo, width=200)

def main():
    st.write("# Probabilidades de incumplimiento o de default")
    st.sidebar.title('Menú')
    options = ['Documentación', 'Cálculo']
    choice = st.sidebar.radio('Secciones:', options)

    if choice == options[0]:
        st.markdown("""
        La probabilidad de default o incumplimiento, como su nombre lo indica, corresponde a la probabilidad de que una contraparte o la propia institución caiga en un evento de incumplimiento de sus obligaciones.

        Se presenta la metodología utilizada por Creasys para calcular las probabilidades de default de una contraparte, a partir de sus spreads para tres periodos de tiempo (2, 5 y 10 años) y su tasa de recuperación (recovery rate). 

        ## Pasos
        """)

        # 1. Paso 1 
        with st.expander("1. Recepción de las recovery rate"):
            st.write("""
            El primer paso consiste en recibir el valor de la Tasa de Recuperación de la contraparte (RR por sus ciclas en inglés). Con esta información, es posible calcular la tasa de Pérdida en caso de Incumplimiento (o LGD por sus siglas en inglés) de la misma. 

            Ambos conseptos se relacionan según la siguiente fórmula: 
            
            $$LGD_i=1-RR_i$$
            
            Donde:

            * $LGD_i$ corresponde a la tasa de pérdida en caso de incumplimiento de la contraparte $i$, y
            * $RR_i$ corresponde a la tasa de recuperación de la misma contraparte $i$.
            """)

        # Paso 2
        with st.expander("2. Recepción de los spreads para 2, 5 y 10 años"):
            st.write("""
            Los spreads de la contraparte pueden estar definidos como propios o genéricos. Es decir, pueden ser de una contraparte en específico, o de un tipo de contraparte que tenga ciertas características en común, como el tipo de spread, tipo de contraparte, sector de negocios y rating de riesgo. 

            Creasys solicita los spreads de 3 instantes de tiempo: 2, 5 y 10 años. Además, a la hora de interpolar asume un nuevo spread que en el tiempo 0, toma valor 0.
            """)

        # Paso 3
        with st.expander("3. Interpolación de los spreads para 20 primeros años"):
            st.write("""
            Luego de recibir los spreads para los tres periodos de tiempos dados, se procede a interpolar linealmente estos valores para un plazo de 20 años.
            """)

        # Paso 4            
        with st.expander("4. Cálculo de probabilidades de default acumuladas para los primeros 20 años"):
            st.write("""
            A partir de los spreads se calculan las probabilidades de default acumuladas según la siguiente fórmula:

            $$ PDA_{i,t} = 1 - e^{yf_t \cdot sp_{i,t}/lgd_i} $$

            Donde 
            * $PDAcumulada_{i,t}$ corresponde a la probabilidad de default acumulada para una contraparte $i$ y un periodo de tiempo $t$.
            * $yf_t$ corresponde a la fracción de año de cada instante $t$. Se mide en días hábiles. 
            * $sp_{i}$ corresponde al vector de spreads interpolado para 20 años recién calculado. 
            * $lgd_{i}$ corresponde a la pérdida dado incumplimiento.  
            """)
            
        # Paso 5
        with st.expander("5. Interpolación de las probabilidades de default acumuladas para los stopping times definidos"):
            st.write("""
            Se interpolan linealmente las probabilidades de default acumuladas para el rango de stopping times definidos. 
            """)

        # Paso 6
        with st.expander("6. Cálculo de las probabilidades de default a partir de las probabilidades acumuladas"):
            st.write("""
            Finalmente, para calcular las probabilidades de default desde las probabilidades de default acumuladas, es necesario calcular la diferencia en cada stopping time. Es decir:
            
            $$Pd_{i,st}=PdAcumulada_{i,st}-PdAcumulada_{i,st-1}$$ 
            
            Con $PdAcumulada_{i,0}=0$
            
            Donde:
            * $Pd_{i,st}$ corresponde a las probabilidades de default de una institución $i$ para un stopping time $st$. 
            * $PdAcumulada_{i,st}$ corresponde a las probabilidades de default acomuladas para un stopping time $st$. 
            """)

    elif choice == options[1]:
        st.markdown("""
        En esta vista usted podrá calcular, descargar y visualizar el vector de probabilidades de default de una contraparte dada. Entregando la siguiente información: 
        """)

        #1
        st.write("1. Ingrese la tasa de recuperación de la contraparte:")
        rr = st.number_input("",min_value=0.00, max_value=1.00, step=0.1)
        lgd=round(1-rr,2)
        st.write(f"La Recovery Rate (RR) ingresada es: {rr}, por lo que la Lost Given Default corresponde a {lgd} ")

        #2
        st.write("2. Ingrese los spreads para los siguientes años:")
        s2 = st.number_input("2 años",min_value=0.0000, max_value=1.0000, step=0.0100)
        s5 = st.number_input("5 años",min_value=0.0000, max_value=1.0000, step=0.0100)
        s10 = st.number_input("10 años",min_value=0.0000, max_value=1.0000, step=0.0100)
        spreads = {
            "Año": [0, 2, 5, 10],
            "Spreads": [0,s2,s5,s10]
        }
        s_df=pd.DataFrame(spreads)
        st.write("Spreads:")
        st.write(s_df)
        
        #3 Interpolar a 20 años
        interp_years = np.arange(0, 21)
        interp_function = interp1d(s_df['Año'], s_df['Spreads'], kind='linear', fill_value='extrapolate')
        interp_spreads = interp_function(interp_years)
        interp_data = {
            "Año": interp_years,
            "Spreads": interp_spreads
        }
        interp_df = pd.DataFrame(interp_data)

        #4 PD acumulada
        interp_df['Probabilidad Acumulada'] = 1 - np.exp(-interp_df['Año']*interp_df['Spreads'] / lgd)

        #5. Interpolar pd ac para st
        interp_df['tenors'] = interp_df['Año']*264
        st_tenors = [0, 5, 22, 89, 156, 221, 286, 353, 420, 485, 551, 618, 684, 750, 815, 882, 948, 1014, 1079, 1146, 1212, 1278, 1343, 1410, 1476, 1542, 1608, 1674, 1741, 1807, 1872, 1938, 2005, 2071, 2136, 2202, 2269, 2335, 2400, 2466, 2533, 2599, 2665, 2731, 2798, 2863, 2929, 2995, 3062, 3127, 3193, 3259, 3326, 3391, 3457, 3523, 3590, 3655, 3721, 3788, 3854, 3920, 3985, 4052, 4118, 4184, 4249, 4316, 4382, 4448, 4513, 4580, 4646, 4712, 4778, 4845, 4911, 4977, 5016]
        interp_function = interp1d(interp_df['tenors'], interp_df['Probabilidad Acumulada'], kind='linear', fill_value='extrapolate')
        interpolated_values = interp_function(st_tenors)
        interpolated_data = {
            "tenor": st_tenors,
            "Probabilidad Acumulada": interpolated_values
        }
        interpolated_df = pd.DataFrame(interpolated_data)

        #6. Cálculo de las probabilidades de default
        interpolated_df['Probabilidades de default'] = interpolated_df['Probabilidad Acumulada'].diff()
        interpolated_df.loc[interpolated_df['tenor'] == 0, 'Probabilidades de default'] = 0

        # Mostrar tabla
        col1, col2 = st.columns(2)
        with col1:
            df_final = interpolated_df[['tenor', 'Probabilidades de default']]
            st.header('Probabilidad de default por días')
            st.write(df_final)

        df_acumulada=interpolated_df[['tenor','Probabilidad Acumulada']]


        # Gráfico
        with col2:
            df_final["Años"]=df_final["tenor"]/264
            df_acumulada["Años"]=df_acumulada["tenor"]/264

            st.header('Probabilidad de default por año')

            fig, ax = plt.subplots()
            ax.plot(df_final['Años'], df_final['Probabilidades de default'], marker='o')
            ax.set_xlabel('Años')
            ax.set_ylabel('PD')
            ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
            st.pyplot(fig)

            st.header('Probabilidad de default acumulada por año')

            fig_ac, ax = plt.subplots()
            ax.plot(df_acumulada['Años'], df_acumulada['Probabilidad Acumulada'], marker='o')
            ax.set_xlabel('Años')
            ax.set_ylabel('PD')
            ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
            st.pyplot(fig_ac)
            
if __name__ == "__main__":
    main()