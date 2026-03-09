from dash import Dash, html, dcc, dash_table, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from data_provider import get_cac40_tickers, get_cac_mid_tickers, get_cac_small_tickers, fetch_data, get_financial_metrics
from scoring_engine import calculate_scores
from strategy import generate_signals

app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

def create_layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col(html.H1("Multivariate Factor Scoring Portfolio", className="text-center my-4 text-primary"), width=12)
        ]),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4("Configurations", className="mb-0")),
                    dbc.CardBody([
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

                        dbc.Button("Rafraîchir les données", id='refresh-btn', color="primary", className="mt-3 w-100 shadow-sm"),
                        dcc.Loading(id="loading-1", type="circle", children=html.Div(id="loading-output", className="text-muted small mt-2")),
                    ])
                ], className="shadow-sm mb-3"),
                dbc.Card([
                    dbc.CardHeader(html.H4("Répartition Sectorielle", className="mb-0")),
                    dbc.CardBody(dcc.Graph(id='sector-chart'), style={'height': '350px'})
                ], className="shadow-sm mb-3")
            ], md=3),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4("Signaux et Classement VIP", className="mb-0")),
                    dbc.CardBody([
                        dash_table.DataTable(
                            id='signals-table',
                            columns=[],
                            data=[],
                            sort_action="native",
                            filter_action="native",
                            page_size=10,
                            row_selectable='single',
                            style_table={'overflowX': 'auto'},
                            style_cell={'textAlign': 'left', 'fontFamily': 'inherit'},
                            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                            style_data_conditional=[
                                {
                                    'if': {'column_id': 'Signal', 'filter_query': '{Signal} contains "Buy"'},
                                    'backgroundColor': '#d4edda', 'color': '#155724'
                                },
                                {
                                    'if': {'column_id': 'Signal', 'filter_query': '{Signal} eq "Sell"'},
                                    'backgroundColor': '#f8d7da', 'color': '#721c24'
                                },
                                {
                                    'if': {'column_id': 'Signal', 'filter_query': '{Signal} eq "Données Insuffisantes"'},
                                    'backgroundColor': '#dc3545', 'color': 'white'
                                },
                                {
                                    'if': {'column_id': 'Zone_Prix', 'filter_query': '{Zone_Prix} contains "Prix de Gros"'},
                                    'color': '#28a745', 'fontWeight': 'bold'
                                },
                                {
                                    'if': {'column_id': 'Zone_Prix', 'filter_query': '{Zone_Prix} contains "Prix de Détail"'},
                                    'color': '#fd7e14', 'fontWeight': 'bold'
                                },
                                {
                                    'if': {'column_id': 'Zone_Prix', 'filter_query': '{Zone_Prix} contains "Attendre Repli"'},
                                    'color': '#dc3545', 'fontWeight': 'bold'
                                }
                            ]
                        ),
                    ])
                ], className="shadow-sm mb-3"),
                dbc.Card([
                    dbc.CardHeader(html.H4("Analyse Détaillée", className="mb-0")),
                    dbc.CardBody(id='detail-section')
                ], className="shadow-sm mb-3"),
                dbc.Card([
                    dbc.CardHeader(html.H4("Performance Relative Portfolio (VIP vs Momentum)", className="mb-0")),
                    dbc.CardBody(dcc.Graph(id='performance-chart'))
                ], className="shadow-sm mb-3")
            ], md=9)
        ]),

        dcc.Store(id='full-data-store')
    ], fluid=True)

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

    base_cols = ['Ticker', 'Name', 'Signal', 'Value_Rank', 'Inv_Rank', 'Prof_Rank', 'Zone_Prix', 'Dist_POC', 'Global_Rel', 'VIP_Rank', 'Weighting_Type']
    end_cols = ['Price']

    display_cols = base_cols + selected_ranks + end_cols

    col_names = {
        'Value_Rank': 'V',
        'Inv_Rank': 'I',
        'Prof_Rank': 'P',
        'Zone_Prix': 'Timing',
        'Dist_POC': 'Dist. POC (%)',
        'Global_Rel': 'Fiabilité',
        'VIP_Rank': 'Rang VIP'
    }

    cols = [{"name": col_names.get(i, i), "id": i} for i in display_cols]

    buys = df_signals[df_signals['Signal'].str.contains('Buy', na=False)]
    fig_sector = px.pie(buys, names='Sector', title='Portefeuille "Buy"') if not buys.empty else {}

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
        return html.Div("Sélectionnez une ligne dans le tableau pour voir l'analyse détaillée.", className="text-muted text-center py-4")

    row = rows[selected_rows[0]]

    # Gauge Figure for VIP Rank
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = row['VIP_Rank'],
        title = {'text': f"Position VIP ({row['Ticker']})", 'font': {'size': 18}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': "#2c3e50"},
            'steps' : [
                {'range': [0, exit_th], 'color': "#f8d7da"},
                {'range': [exit_th, buy_th], 'color': "#fff3cd"},
                {'range': [buy_th, 100], 'color': "#d4edda"}
            ],
            'threshold' : {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': buy_th}
        }
    ))
    fig.update_layout(height=250, margin=dict(l=30, r=30, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    # Reliability Indicators
    def get_rel_badge(val):
        color = "success" if val == 1.0 else "warning" if val == 0.5 else "danger"
        return dbc.Badge(f"{val}", color=color, className="ms-1")

    reliability_content = html.Div([
        html.H5(["Fiabilité Globale: ", get_rel_badge(row['Global_Rel'])], className="mb-3"),
        html.Div([
            html.P(["Valeur: ", get_rel_badge(row['Rel_V'])], className="mb-1"),
            html.P(["Investissement: ", get_rel_badge(row['Rel_I'])], className="mb-1"),
            html.P(["Profitabilité: ", get_rel_badge(row['Rel_P'])], className="mb-1"),
        ], className="small")
    ], className="p-3 border rounded bg-light h-100")

    # Pillar breakdown Bar Chart
    pillar_data = pd.DataFrame({
        'Pillar': ['Value', 'Investment', 'Profitability'],
        'Score': [row['Value_Rank'], row['Inv_Rank'], row['Prof_Rank']]
    })
    fig_pillars = px.bar(
        pillar_data, x='Score', y='Pillar', orientation='h',
        title="Détail des Scores (V, I, P)",
        range_x=[0, 100],
        color='Score',
        color_continuous_scale='RdYlGn'
    )
    fig_pillars.update_layout(height=250, margin=dict(l=30, r=30, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False)

    # Tab 1: Visual Analysis
    tab1_content = html.Div([
        dbc.Row([
            dbc.Col(reliability_content, md=4),
            dbc.Col(dcc.Graph(figure=fig), md=4),
            dbc.Col(dcc.Graph(figure=fig_pillars), md=4)
        ]),
    ], className="mt-3")

    # Tab 2: Fundamental Details
    # Identify missing data
    essential_fields = {
        'PB': 'P/B', 'PE': 'P/E', 'FCF_Yield': 'FCF Yield',
        'TotalAssets': 'Total Assets', 'PrevTotalAssets': 'Prev Total Assets',
        'Revenue': 'Chiffre d\'Affaires', 'BookEquity': 'Capitaux Propres'
    }
    missing = [name for field, name in essential_fields.items() if pd.isna(row.get(field))]

    missing_alert = ""
    if missing:
        missing_alert = dbc.Alert([
            html.I(className="bi bi-exclamation-triangle-fill me-2"),
            f"Données manquantes : {', '.join(missing)}"
        ], color="danger", className="mt-2 small py-1")

    def fmt(val, is_pct=False):
        if val is None or pd.isna(val): return "N/A"
        if is_pct: return f"{val*100:.2f}%"
        return f"{val:,.2f}"

    fundamental_content = html.Div([
        dbc.Row([
            dbc.Col([
                html.H6("Valorisation (Value)", className="text-primary border-bottom pb-1"),
                html.P(f"P/B : {fmt(row.get('PB'))}"),
                html.P(f"P/E : {fmt(row.get('PE'))}"),
                html.P(f"FCF Yield : {fmt(row.get('FCF_Yield'), True)}"),
            ], md=4),
            dbc.Col([
                html.H6("Bilan & Profitabilité", className="text-primary border-bottom pb-1"),
                html.P(f"Assets Growth : {fmt((row.get('TotalAssets',0)-row.get('PrevTotalAssets',0))/row.get('PrevTotalAssets',1) if row.get('PrevTotalAssets') else None, True)}"),
                html.P(f"Revenue : {fmt(row.get('Revenue'))}"),
                html.P(f"Equity : {fmt(row.get('BookEquity'))}"),
            ], md=4),
            dbc.Col([
                html.H6([
                    "Timing (Volume Profile) ",
                    html.Span("(i)", id="timing-info-icon", style={"cursor": "pointer", "fontSize": "0.8rem", "color": "#17a2b8"}),
                    dbc.Tooltip(
                        "Le prix de gros (POC) est le niveau où les volumes institutionnels sont les plus denses sur 6 mois.",
                        target="timing-info-icon",
                    ),
                ], className="text-primary border-bottom pb-1"),
                html.P(f"POC : {fmt(row.get('POC'))}"),
                html.P(f"VAH : {fmt(row.get('VAH'))}"),
                html.P(f"VAL : {fmt(row.get('VAL'))}"),
                html.P(f"Dist. POC : {row.get('Dist_POC')}%", className="fw-bold"),
            ], md=4),
        ], className="mt-3"),
        dbc.Row([
            dbc.Col([
                html.H6("Performance", className="text-primary border-bottom pb-1"),
                html.P(f"Perf 12m : {fmt(row.get('Perf_12m'), True)}"),
                html.P(f"Momentum r(12,1) : {fmt(row.get('Momentum'), True)}"),
                html.P(f"Market Cap : {fmt(row.get('MarketCap'))}"),
            ], md=12),
        ], className="mt-3"),
        missing_alert
    ], className="p-3")

    return dbc.Tabs([
        dbc.Tab(tab1_content, label="Analyse Graphique", tab_id="tab-graph"),
        dbc.Tab(fundamental_content, label="Détails Fondamentaux", tab_id="tab-fund"),
    ], active_tab="tab-graph")

if __name__ == "__main__":
    app.run(debug=True, port=8050)
