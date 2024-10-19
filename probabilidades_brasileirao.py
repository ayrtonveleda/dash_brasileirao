from dash import Dash, dcc, html, Input, Output
from dash import dash_table
import pandas as pd
import requests
from bs4 import BeautifulSoup
from io import StringIO

# Inicializar o aplicativo Dash
app = Dash(__name__)

# DataFrame global para armazenar os dados
df_br = pd.DataFrame()

# Função para coletar dados
def fetch_data():
    global df_br
    queries = ['campeao_seriea', 'rebaixamento_seriea','classificacao-para-libertadores_seriea', 'classificacao-para-sulamericana_seriea']
    url = 'https://www.mat.ufmg.br/futebol/{query}/'

    data_frames = []
    for query in queries:
        urll = url.format(query=query)
        response = requests.get(urll)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Encontrar a tabela
        table = soup.find('table')
        if table:
            df = pd.read_html(StringIO(str(table)))[0]
            
            # Adicionar a coluna de Categoria
            if 'campeao' in query:
                df['Categoria'] = 'Campeão'
            
            elif 'rebaixamento' in query:
                df['Categoria'] = 'Rebaixamento'
            
            elif 'libertadores' in query:
                df['Categoria'] = 'Classificação Libertadores'
            
            elif 'sulamericana' in query:
                df['Categoria'] = 'Classificação Sul-Americana'
            data_frames.append(df)

    # Concatenar os DataFrames e ajustar os nomes das colunas
    df_br = pd.concat(data_frames, ignore_index=True)
    df_br.columns = ['Ranking', 'Time', 'Probabilidade', 'Categoria']

# Coletar os dados pela primeira vez ao iniciar o aplicativo
fetch_data()

# Layout do dashboard
app.layout = html.Div([
    html.H1("Probabilidades do Brasileirão 2024"),
    
    dcc.Dropdown(
        id='category-dropdown',
        options=[
            {'label': 'Campeão', 'value': 'Campeão'},
            {'label': 'Rebaixamento', 'value': 'Rebaixamento'},
            {'label': 'Classificação Libertadores', 'value': 'Classificação Libertadores'},
            {'label': 'Classificação Sul-Americana', 'value': 'Classificação Sul-Americana'}
        ],
        value='Campeão',
        clearable=False
    ),
    
    # Tabela de classificação
    dash_table.DataTable(
        id='ranking-table',
        columns=[
            {"name": "Ranking", "id": "Ranking"},
            {"name": "Time", "id": "Time"},
            {"name": "Probabilidade", "id": "Probabilidade"}
        ],
        page_size=10,
        style_table={'overflowX': 'auto'},  # Para scroll horizontal se necessário
        style_cell={
            'textAlign': 'left',  # Alinhamento do texto
            'padding': '5px',
        }
    ),
    
    # Mensagem informativa
    html.Div(id='message-div', style={'margin-top': '20px', 'font-size': '18px', 'color': 'red'}),
    
    # Intervalo para atualização
    dcc.Interval(
        id='interval-component',
        interval=60*1000,  # Atualizar a cada 60 segundos
        n_intervals=0
    )
])

# Callback para atualizar a tabela e coletar dados
@app.callback(
    Output('ranking-table', 'data'),
    Output('message-div', 'children'),
    Input('category-dropdown', 'value'),
    Input('interval-component', 'n_intervals')  # Adicionando o input do intervalo
)
def update_table(selected_category, n):
    # Atualizar os dados ao chamar o callback
    fetch_data()
    
    # Filtrar os dados pela categoria selecionada
    filtered_data = df_br[df_br['Categoria'] == selected_category]
    filtered_data = filtered_data[filtered_data['Probabilidade'] > 0]  # Excluir probabilidades <= 0
    
    # Adicionar uma coluna de ranking
    filtered_data = filtered_data.sort_values(by='Probabilidade', ascending=False).reset_index(drop=True)
    filtered_data['Ranking'] = filtered_data.index + 1  # Cria a coluna de ranking

    # Mensagem se não houver clubes com probabilidade > 0
    if filtered_data.empty:
        message = f"Nenhum clube com probabilidade positiva nesta categoria."
    else:
        message = f"Os times fora desta lista não têm mais chances de {selected_category.lower()}."  # Mensagem para times fora da lista

    return filtered_data.to_dict('records'), message  # Retorna os dados e a mensagem

# Executar o servidor
if __name__ == '__main__':
    app.run_server(debug=True)