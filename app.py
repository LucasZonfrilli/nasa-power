import streamlit as st
import pandas as pd
import requests
import io
import matplotlib.pyplot as plt

# Função para carregar os dados da API
@st.cache_data
def load_data(parameters_subset, start_date, end_date):
    url = f'https://power.larc.nasa.gov/api/temporal/daily/point?parameters={parameters_subset}&community=SB&longitude=-50.481333&latitude=-22.805694&start={20230401}&end={20240706}&format=CSV'
    response = requests.get(url)
    data = response.text
    data_parts = data.split('-END HEADER-')
    actual_data = data_parts[1].strip()
    df = pd.read_csv(io.StringIO(actual_data))
    df.replace(-999, pd.NA, inplace=True)
    return df

# Definindo os parâmetros
parameters = ['T2M_MAX', 'T2M_MIN']
parameters_subset = ','.join(parameters)

# Interface do Streamlit
st.title('Cálculo de Graus-Dia Acumulados para Colheita da Cana')
st.write('Selecione o período de data para visualizar os dados e calcular os graus-dia acumulados.')

# Seleção de data
start_date = st.date_input("Data de Início", pd.to_datetime('2023-04-01'))
end_date = st.date_input("Data de Fim", pd.to_datetime('2024-07-09'))

if start_date > end_date:
    st.error("A data de início deve ser anterior à data de fim.")
else:
    # Carregar os dados
    df = load_data(parameters_subset, start_date.strftime('%Y%m%d'), end_date.strftime('%Y%m%d'))
    
    # Verificar a estrutura do DataFrame
    st.write("Estrutura do DataFrame:")
    st.write(df.head())
    st.write("Colunas disponíveis:", df.columns)

    # Calcular Graus-Dia Acumulados (GDA)
    df['GDA'] = ((df['T2M_MAX'] + df['T2M_MIN']) / 2) - 20
    df['GDA'] = df['GDA'].fillna(0).apply(lambda x: max(x, 0)).infer_objects()  # GDA não pode ser negativo e substituir NaN por 0
    df['GDA_Acum'] = df['GDA'].cumsum()  # GDA acumulado

    # Criar a coluna 'DATE' a partir das colunas 'YEAR', 'MO', 'DY'
    if all(col in df.columns for col in ['YEAR', 'MO', 'DY']):
        df['DATE'] = pd.to_datetime(df['YEAR'].astype(str) + '-' + df['MO'].astype(str).str.zfill(2) + '-' + df['DY'].astype(str).str.zfill(2))
        df['DATE'] = df['DATE'].dt.strftime('%d/%m/%Y')
    else:
        st.error("Não foi possível encontrar colunas adequadas para formar a data.")

    # Exibir a tabela de dados
    st.write('Tabela de Dados')
    st.dataframe(df[['DATE', 'T2M_MAX', 'T2M_MIN', 'GDA', 'GDA_Acum']])

    # Exibir o gráfico de GDA Acumulado
    st.write('Gráfico de Graus-Dia Acumulados')
    plt.figure(figsize=(10, 5))
    plt.plot(pd.to_datetime(df['DATE'], format='%d/%m/%Y'), df['GDA_Acum'], marker='o')
    plt.xlabel('Data')
    plt.ylabel('Graus-Dia Acumulados')
    plt.title('Graus-Dia Acumulados ao Longo do Tempo')
    plt.grid(True)
    st.pyplot(plt.gcf())