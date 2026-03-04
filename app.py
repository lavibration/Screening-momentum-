from dash import Dash, html, dcc, dash_table, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from src.data_provider import get_cac40_tickers, fetch_data, get_financial_metrics
from src.scoring_engine import calculate_scores
from src.strategy import generate_signals

def create_layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col(html.H1("Multivariate Factor Scoring Portfolio", className="text-center my-4"), width=12)
        ]),
        
        dbc.Row([
            dbc.Col([
                html.H4("Configurations"),
                html.Label("Seuil d'achat VIP (Top X%)"),
                dcc.Slider(id='buy-threshold', min=50, max=100, step=5, value=80, marks={i: str(i) for i in range(50, 101, 10)}),
                
                html.Label("Seuil de sortie VIP"),
                dcc.Slider(id='exit-threshold', min=0, max=80, step=5, value=50, marks={i: str(i) for i in range(0, 81, 10)}),
                
                html.Label("Seuil Momentum critique (Percentile)"),
                dcc.Slider(id='mom-exit-threshold', min=0, max=50, step=5, value=20, marks={i: str(i) for i in range(0, 51, 10)}),
                
                dbc.Button("Rafraîchir les données", id='refresh-btn', color="primary", className="mt-3 w-100"),
                dcc.Loading(id="loading-1", type="default", children=html.Div(id="loading-output")),
            ], md=3),
            
            dbc.Col([
                html.H4("Signaux et Classement VIP"),
                dash_table.DataTable(
                    id='signals-table',
                    columns=[],
                    data=[],
                    sort_action="native",
                    filter_action="native",
                    page_size=10,
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left'},
                    style_data_conditional=[
                        {
                            'if': {'column_id': 'Signal', 'filter_query': '{Signal} eq "Buy"'},
                            'backgroundColor': '#d4edda', 'color': '#155724'
                        },
                        {
                            'if': {'column_id': 'Signal', 'filter_query': '{Signal} eq "Sell"'},
                            'backgroundColor': '#f8d7da', 'color': '#721c24'
                        }
                    ]
                )
            ], md=9)
        ]),
        
        dbc.Row([
            dbc.Col([
                html.H4("Répartition Sectorielle", className="mt-4"),
                dcc.Graph(id='sector-chart')
            ], md=6),
            dbc.Col([
                html.H4("Performance Relative", className="mt-4"),
                dcc.Graph(id='performance-chart')
            ], md=6)
        ]),
        
        dcc.Store(id='full-data-store')
    ], fluid=True)

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = create_layout()

@app.callback(
    Output('full-data-store', 'data'),
    Output('loading-output', 'children'),
    Input('refresh-btn', 'n_clicks')
)
def update_data(n_clicks):
    if n_clicks is None:
        return None, ""
    
    tickers = get_cac40_tickers()
    # Limit to 10 for faster loading during demo/testing if needed
    # tickers = tickers[:15]
    raw_data = fetch_data(tickers)
    df = get_financial_metrics(raw_data)
    scored_df = calculate_scores(df)
    
    return scored_df.to_dict('records'), f"Données mises à jour ({len(scored_df)} actions)"

@app.callback(
    Output('signals-table', 'data'),
    Output('signals-table', 'columns'),
    Output('sector-chart', 'figure'),
    Output('performance-chart', 'figure'),
    Input('full-data-store', 'data'),
    Input('buy-threshold', 'value'),
    Input('exit-threshold', 'value'),
    Input('mom-exit-threshold', 'value')
)
def update_ui(data, buy_th, exit_th, mom_th):
    if data is None:
        return [], [], {}, {}
    
    df = pd.DataFrame(data)
    df_signals = generate_signals(df, buy_vip_threshold=buy_th, exit_vip_threshold=exit_th, exit_momentum_threshold=mom_th)
    
    # Table columns
    cols = [{"name": i, "id": i} for i in ['Ticker', 'Name', 'Signal', 'VIP_Rank', 'Momentum_Rank', 'Sector', 'Price']]
    
    # Sector Chart (for Buy signals)
    buys = df_signals[df_signals['Signal'] == 'Buy']
    if not buys.empty:
        fig_sector = px.pie(buys, names='Sector', title='Répartition sectorielle du portefeuille')
    else:
        fig_sector = {}
        
    # Performance Chart (Scatter VIP vs Momentum)
    fig_perf = px.scatter(df_signals, x='Momentum_Rank', y='VIP_Rank', color='Signal', 
                         hover_name='Ticker', title='Momentum vs VIP Rank')
    fig_perf.add_hline(y=buy_th, line_dash="dash", line_color="green", annotation_text="Seuil Achat")
    fig_perf.add_vline(x=50, line_dash="dash", line_color="blue", annotation_text="Médiane Momentum")

    return df_signals.to_dict('records'), cols, fig_sector, fig_perf

if __name__ == "__main__":
    app.run(debug=True, port=8050)
