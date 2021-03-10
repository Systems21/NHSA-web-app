from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_table

from app import app

def return_content(cols, dat):
    return html.Div(
    [
        html.H3('Selected Data', style={'textAlign': 'center'}),
        dbc.Row(
            [
                dbc.Col(
                    dash_table.DataTable(columns=cols, data=dat,
                                         style_cell={'textAlign': 'left'},
                                         export_format="csv", ), md=12,
                )
            ]
        )
    ],
    style={
    'margin-left': '25%',
    'margin-right': '5%',
    'padding': '20px 10p'
}
)