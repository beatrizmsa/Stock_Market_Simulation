import yfinance as yf
import plotly.graph_objects as go

# Função para obter dados do yfinance
def obter_dados(stock, start, end):
    stock_data = yf.Ticker(stock)
    interval = '1d'
    tickers_hist = stock_data.history(start=start, end=end, interval=interval)
    return tickers_hist

# Substitua esses valores pelos desejados
stocks = ["NKE", "UNH", "BRK-B", "GOOGL", "NFLX","LLY", "MSFT"]  # Adicione mais ações conforme necessário
start_date = "2021-02-15"
end_date = "2023-11-12"

# Obtém os dados do yfinance para cada ação
dados = {stock: obter_dados(stock, start_date, end_date) for stock in stocks}

# Cria um gráfico interativo de linhas para cada ação usando plotly.graph_objects
fig = go.Figure()

for stock, data in dados.items():
    fig.add_trace(go.Scatter(x=data.index, y=data['Open'], mode='lines', name=stock))

# Adiciona rótulos e título ao gráfico
fig.update_layout(xaxis_title='Data', yaxis_title='Valor de Abertura', title='Gráfico do Valor de Abertura para Ações')

# Mostra o gráfico interativo
fig.show()
