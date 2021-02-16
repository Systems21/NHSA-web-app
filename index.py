import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

# Connect to main app.py file
from app import app
from app import server

# Connect to your app pages
from apps import censusmain, global_sales


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div([
        dcc.Link('Census Data|', href='/apps/censusmain'),
        dcc.Link('Future Data', href='/apps/global_sales'),
    ], className="row"),
    html.Div(id='page-content', children=[])
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/apps/censusmain':
        return censusmain.layout
    if pathname == '/apps/global_sales':
        return global_sales.layout
    else:
        return censusmain.layout


if __name__ == '__main__':
    app.run_server(debug=False)
