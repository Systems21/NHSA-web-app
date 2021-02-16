import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from app import app
from census import CensusViewer
from load_configcustom import load_config
import pathlib

# configure data
# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("..").resolve()
# Create dataframe for simple selections and filters
state_county_choices = pd.read_csv(DATA_PATH.joinpath("state_county_fips.csv"))

# setup census viewer
censusViewer = CensusViewer(vars_config=load_config("vars.json"), api_key='e12de88e1f23dcdd9a802fbbb92b362a1e67c3c4')

# List of variable category choices
vars = censusViewer.available_vars
varcategories = [var[0] for var in vars]

layout = html.Div([
    html.H1('Census County Data', style={"textAlign": "center"}),

    html.Div([
        html.Div(dcc.Dropdown(
            id='states-dropdown', value=None, clearable=False,
            options=[{'label': x, 'value': x} for x in state_county_choices["State"].unique()],
            multi=True
        ), className='six columns', style={'width': '20%'}),

        html.Div(dcc.Dropdown(
            id='county-dropdown', value='Autauga County, Alabama', clearable=False,
            options=[],
            multi=True
        ), className='six columns', style={'width': '30%'}),

        html.Div(dcc.Dropdown(
            id='vars-dropdown', placeholder="Select variables",
            persistence=True, persistence_type='memory',
            options=[{'label': x, 'value': x} for x in varcategories],
            multi=True
        ), className='six columns', style={'width': '30%'}),
     ], className='row'),
    #
    # dcc.Graph(id='my-bar', figure={}),
    dash_table.DataTable(id='table', columns=[], data=[],
                         style_cell={'textAlign': 'left'},
                         export_format="csv",),
])


# Populate the counties dropdown with options and values
@app.callback(
    Output('county-dropdown', 'options'),
    Input('states-dropdown', 'value'),
)
def set_county_options(chosen_state):
    dff = state_county_choices[state_county_choices['State'].isin(chosen_state)]
    counties_of_states = [{'label': c, 'value': c} for c in dff["County"]]
    return counties_of_states

# Populate the counties dropdown with options and values
@app.callback(
    Output('table', 'columns'),
    Output('table', 'data'),
    Input('vars-dropdown', 'value'),
    Input('county-dropdown', 'value'),
)
def fill_table(svars, scounties):
    # Pull details for selected var categories
    varlist = [t for t in vars if t[0] in svars]
    # Pull list of var ids for data extraction
    selected_ids = []
    for var in varlist:
        for pair in var[1]:
            tempdict = pair[0]
            id = tempdict.get('value')
            selected_ids.append(str(id))
    selected_counties = [[state.strip(), county] for county, state in [county.split(",") for county in scounties]]
    fulldf = censusViewer.view_df(county_names=selected_counties, selected_var_ids=selected_ids)
    cols = [{"name": i, "id": i} for i in fulldf.columns]
    cols[0]['name'] = 'Variable'
    dat = fulldf.to_dict('records')
    return cols, dat
#
# @app.callback(
#     Output(component_id='my-bar', component_property='figure'),
#     [Input(component_id='genre-dropdown', component_property='value'),
#      Input(component_id='sales-dropdown', component_property='value')]
# )
# def display_value(genre_chosen, sales_chosen):
#     dfv_fltrd = dfv[dfv['Genre'] == genre_chosen]
#     dfv_fltrd = dfv_fltrd.nlargest(10, sales_chosen)
#     fig = px.bar(dfv_fltrd, x='Video Game', y=sales_chosen, color='Platform')
#     fig = fig.update_yaxes(tickprefix="$", ticksuffix="M")
#     return fig
