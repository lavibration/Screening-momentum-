from dash import Dash, html, dcc, dash_table, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from data_provider import get_cac40_tickers, get_cac_mid_tickers, get_cac_small_tickers, fetch_data, get_financial_metrics
from scoring_engine import calculate_scores
from strategy import generate_signals

def create_layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col(html.H1("Multivariate Factor Scoring Portfolio", className="text-center my-4"), width=12)
        ]),
        
        dbc.Row([
            dbc.Col([
                html.H4("Configurations"),
                html.Label("Sélection de l'indice"),
                dbc.RadioItems(
                    id="index-selector",
                    options=[
                        {"label": "CAC 40", "value": "cac40"},
                        {"label": "CAC Mid 60", "value": "cacmid"},
                        {"label": "CAC Small", "value": "cacsmall"},
                    ],
                    value="cac40",
                    className="mb-3"
                ),

                html.Label("Seuil d'achat VIP (Top X%)"),
                dcc.Slider(id='buy-threshold', min=50, max=100, step=5, value=80, marks={i: str(i) for i in range(50, 101, 10)}),
                
                html.Label("Seuil de sortie VIP"),
                dcc.Slider(id='exit-threshold', min=0, max=80, step=5, value=50, marks={i: str(i) for i in range(0, 81, 10)}),

                html.Label("Colonnes de Score à afficher", className="mt-3"),
                dcc.Checklist(
                    id='column-selector',
                    options=[
                        {'label': ' Value Rank', 'value': 'Value_Rank'},
                        {'label': ' Investment Rank', 'value': 'Inv_Rank'},
                        {'label': ' Profitability Rank', 'value': 'Prof_Rank'},
                        {'label': ' Momentum Rank', 'value': 'Momentum_Rank'},
                    ],
                    value=['Value_Rank', 'Inv_Rank', 'Prof_Rank', 'Momentum_Rank'],
                    labelStyle={'display': 'block'}
                ),
                
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
                    row_selectable='single',
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
                        },
                        {
                            'if': {'column_id': 'Signal', 'filter_query': '{Signal} eq "Données Insuffisantes"'},
                            'backgroundColor': '#f8d7da', 'color': '#721c24'
                        }
                    ]
                ),
                html.Div(id='detail-section', className="mt-4")
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
    Input('refresh-btn', 'n_clicks'),
    State('index-selector', 'value')
)
def update_data(n_clicks, selected_index):
    if n_clicks is None:
        return None, ""
    
    if selected_index == "cacmid":
        tickers = get_cac_mid_tickers()
    elif selected_index == "cacsmall":
        tickers = get_cac_small_tickers()
    else:
        tickers = get_cac40_tickers()

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
    Input('column-selector', 'value')
)
def update_ui(data, buy_th, exit_th, selected_ranks):
    if data is None:
        return [], [], {}, {}
    
    df = pd.DataFrame(data)
    df_signals = generate_signals(df, buy_vip_threshold=buy_th, exit_vip_threshold=exit_th)

    base_cols = ['Ticker', 'Name', 'Signal', 'Global_Rel', 'VIP_Rank', 'Weighting_Type']
    end_cols = ['Price']

    display_cols = base_cols + selected_ranks + end_cols

    cols = [{"name": i, "id": i} for i in display_cols]
    
    buys = df_signals[df_signals['Signal'] == 'Buy']
    fig_sector = px.pie(buys, names='Sector', title='Répartition sectorielle du portefeuille') if not buys.empty else {}

    fig_perf = px.scatter(df_signals, x='Momentum_Rank', y='VIP_Rank', color='Signal', 
                         hover_name='Ticker', title='Momentum vs VIP Rank')
    fig_perf.add_hline(y=buy_th, line_dash="dash", line_color="green", annotation_text="Seuil Achat")
    fig_perf.add_vline(x=50, line_dash="dash", line_color="blue", annotation_text="Médiane Momentum")

    return df_signals.to_dict('records'), cols, fig_sector, fig_perf

@app.callback(
    Output('detail-section', 'children'),
    Input('signals-table', 'derived_virtual_data'),
    Input('signals-table', 'derived_virtual_selected_rows'),
    State('buy-threshold', 'value'),
    State('exit-threshold', 'value')
)
def display_details(rows, selected_rows, buy_th, exit_th):
    if not selected_rows or rows is None:
        return html.Div("Sélectionnez une ligne pour voir le détail des scores.")

    row = rows[selected_rows[0]]

    # Gauge Figure for VIP Rank
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = row['VIP_Rank'],
        title = {'text': f"Position VIP ({row['Ticker']})"},
        gauge = {
            'axis': {'range': [0, 100]},
            'steps' : [
                {'range': [0, exit_th], 'color': "lightcoral"},
                {'range': [exit_th, buy_th], 'color': "lemonchiffon"},
                {'range': [buy_th, 100], 'color': "lightgreen"}
            ],
            'threshold' : {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': buy_th}
        }
    ))
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))

    reliability_info = html.Div([
        html.H5(f"Fiabilité des données : {row['Global_Rel']}"),
        html.P(f"Valeur : {row['Rel_V']} | Investissement : {row['Rel_I']} | Profitabilité : {row['Rel_P']}")
    ])

    return html.Div([
        dbc.Row([
            dbc.Col(reliability_info, md=6),
            dbc.Col(dcc.Graph(figure=fig), md=6)
        ])
    ])

if __name__ == "__main__":
    app.run(debug=True, port=8050)
