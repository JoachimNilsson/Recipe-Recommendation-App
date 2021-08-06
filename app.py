import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import pandas as pd
import json
import requests
import base64
from requests.exceptions import MissingSchema
import ast
import time
import sqlite3 as sql


def convert_ingred(ingredients):
    try:
        return ast.literal_eval(ingredients)
    except:
        return []


def convert_instruct(instructions):
    try:
        return ast.literal_eval(instructions)
    except:
        return []


def convert_rating(rating):
    try:
        return ast.literal_eval(rating)
    except:
        return {}


def convert_to_json(df):
    df["ingredients"] = df["ingredients"].apply(convert_ingred)
    df["instructions"] = df["instructions"].apply(convert_instruct)
    df["ratings"] = df["ratings"].apply(convert_rating)
    return df


start = time.time()
conn = sql.connect('recipes.db')
query = """SELECT *
            FROM recipes
            ORDER BY rating DESC
            LIMIT 50"""
conn = sql.connect('recipes.db')
initial_recipes = pd.read_sql(query, conn)
initial_recipes = convert_to_json(initial_recipes)


with open('recommendations.json', 'r') as fp:
    recommendations = json.load(fp)

end = time.time()
print(end-start, "sec")


def get_recommnded_recipes(saved_urls):
    recommended_urls = []
    for url in saved_urls:
        recommended_urls.extend(recommendations.get(url, []))
    recommended_urls = list(set(recommended_urls))

    recommended_urls_string = str(tuple(recommended_urls))
    conn = sql.connect('recipes.db')
    query = """SELECT *
            FROM recipes
            WHERE url in""" + recommended_urls_string + """
            ORDER BY rating DESC"""
    recommended_recipes = pd.read_sql(query, conn)
    recommended_recipes = convert_to_json(recommended_recipes)
    recommended_recipes = recommended_recipes.sort_values(
        by='rating', ascending=False)
    return recommended_recipes


show_columns = ["title", "rating"]
INITIAL_empty = []


app = dash.Dash(__name__)
server = app.server


def show_ingredient(ingred):
    try:
        return str(ingred["amount_info"]["from"]) + " " + ingred["unit"] + " " + ingred["name"]
    except TypeError:
        return ingred["name"]


def ingredient_list(ingredients):
    html_list = []
    for ingred in ingredients:
        if ingred["type"] == "header":
            html_list.extend([html.H3(ingred["name"]), html.Ul(children=[])])
        elif(not html_list):
            html_list.append(
                html.Ul(children=[html.Li(show_ingredient(ingred))]))
        else:
            html_list[-1].children.append(
                html.Li(show_ingredient(ingred)))
    return html.Div(html_list)


def instruction_list(instructions):
    html_list = []
    for instruction in instructions:
        if instruction["type"] == "header":
            html_list.extend(
                [html.H3(instruction["name"]), html.Ol(children=[])])
        elif(not html_list):
            html_list.append(html.Ol(children=[html.Li(instruction["name"])]))
        else:
            html_list[-1].children.append(
                html.Li(instruction["name"]))

    return html.Div(html_list)


def show_recipe(recipe):
    try:
        encoded_image = base64.b64encode(requests.get(recipe["image"]).content)
        image_src = 'data:image/png;base64,{}'.format(
            encoded_image.decode('utf-8'))
    except MissingSchema:
        image_src = ""
    return [html.Div(id="title",
                     children=html.H1(
                         html.A(href=recipe["url"], children=recipe["title"],
                                target="_blank", rel="noopener noreferrer")),
                     style={'textAlign': 'center'}),
            html.Div(id="image",
                     children=html.Img(
                         src=image_src,
                         style={'width': '100%', 'vertical-align': 'middle'}),
                     style={'marginTop': 5, 'width': '30%', 'display': 'inline-block', 'vertical-align': 'top'}),
            html.Div(id="ingredients_viewer",
                     children=[html.H2("Ingredients"), ingredient_list(
                         recipe["ingredients"])],
                     style={"margin-left": "15px", 'marginTop': 5, 'width': '30%', 'display': 'inline-block', 'vertical-align': 'top'}),
            html.Div(id="instructions_viewer",
                     children=[html.H2("Instructions"), instruction_list(
                         recipe["instructions"])],
                     style={"margin-left": "15px", 'marginTop': 5, 'width': '30%', 'display': 'inline-block', 'vertical-align': 'top'})

            ]


app.layout = html.Div([
    dcc.Store(id='saved_recipes', storage_type='local', modified_timestamp=0),
    html.Button("Clear saved recipes!", id='clear-saved'),
    html.Div(id="tables", children=[

        html.Div(id='hidden-div1', children=[html.H1("Popular recipes"),
                                             dash_table.DataTable(
            id='table1',
            columns=[{"name": i, "id": i}
                     for i in initial_recipes.columns if i in show_columns],
            editable=True,
            row_deletable=True,
            style_data={'whiteSpace': 'normal', 'height': 'auto'},
            style_table={'height': '350px', 'overflowX': 'scroll',
                         'textOverflow': 'ellipsis',
                         'paddingTop': '2px'
                         }
        )], style={'width': '30%', 'display': 'inline-block', "margin-left": "15px"}),
        html.Div(children=[html.H1("Recommended recipes"),
                           dash_table.DataTable(
            id='table2',
            columns=[{"name": i, "id": i}
                     for i in initial_recipes.columns if i in show_columns],
            # data=INITIAL_empty,
            editable=True,
            row_deletable=True,
            style_data={'whiteSpace': 'normal', 'height': 'auto'},
            style_table={'height': '350px', 'overflowX': 'scroll',
                         'textOverflow': 'ellipsis',
                         'paddingTop': '2px'
                         }
        )], style={'width': '30%', 'display': 'inline-block', "margin-left": "15px"}),
        html.Div(children=[html.H1("Saved recipes"),
                           dash_table.DataTable(
            id='table3',
            columns=[{"name": i, "id": i}
                     for i in initial_recipes.columns if i in show_columns],
            editable=True,
            row_deletable=True,
            style_data={'whiteSpace': 'normal', 'height': 'auto'},
            style_table={'height': '350px', 'overflowX': 'scroll',
                         'textOverflow': 'ellipsis',
                         'paddingTop': '2px'
                         }
        )], style={'width': '30%', 'display': 'inline-block', "margin-left": "15px"})
    ]),
    html.Div(id="recipes_viewer")
])

# Update store when recipes is removed from any table


@app.callback(Output('saved_recipes', 'data'),
              Input('table3', 'data_previous'),
              Input('table2', 'data_previous'),
              Input('table1', 'data_previous'),
              State('table3', 'data'),
              State('table2', 'data'),
              State('table1', 'data'),
              State('saved_recipes', 'data'))
def update_store_when_removed(previous_saved, previous_rec, previous_pop, current_saved, current_rec, curren_pop, saved_recipes):
    ctx = dash.callback_context
    if ctx.triggered[0]['value'] is None:
        return saved_recipes
    else:
        triggered_id = ctx.triggered[0]['prop_id']
        previous = ctx.inputs[triggered_id]
        current = ctx.states[triggered_id[:6]+".data"]
        removed_url = list(set([i['url'] for i in previous]) -
                           set([i['url'] for i in current]))[0]
        # If table3 remove otherwise add
        if triggered_id == "table3.data_previous":
            if saved_recipes:
                return [rec for rec in saved_recipes if rec["url"] != removed_url]
            else:
                return None
        else:
            query = """SELECT *
                    FROM recipes
                    WHERE url == '{}'""".format(removed_url)
            conn = sql.connect('recipes.db')
            removed_recipe = pd.read_sql(query, conn)
            removed_recipe = convert_to_json(
                removed_recipe).to_dict('records')[0]
            if saved_recipes:
                if removed_url not in [rec['url'] for rec in saved_recipes]:
                    saved_recipes.append(removed_recipe)
            else:
                saved_recipes = [removed_recipe]
            return saved_recipes


# Display saved, recommended and popular recipes tables based on the saved recipes in store


@app.callback(Output('table1', 'data'),
              Output('table2', 'data'),
              Output('table3', 'data'),
              Input('saved_recipes', 'data'))
def display_popular_recommended_recipes(saved_recipes):
    if saved_recipes:
        saved_urls = [rec['url'] for rec in saved_recipes]

        recommended_recipes = get_recommnded_recipes(saved_urls)
        recommended_recipes_urls = recommended_recipes["url"].tolist()

        urls_left_string = str(
            tuple(set(recommended_recipes_urls+saved_urls)))
        query = """SELECT *
                FROM recipes
                WHERE url not in""" + urls_left_string + """
                ORDER BY rating DESC
                LIMIT 50"""
        conn = sql.connect('recipes.db')
        popular_recipes = pd.read_sql(query, conn)
        popular_recipes = convert_to_json(popular_recipes)

        return popular_recipes.to_dict('records'), recommended_recipes.to_dict('records'), saved_recipes
    else:
        return initial_recipes.to_dict('records'), INITIAL_empty, INITIAL_empty


@app.callback(Output('saved_recipes', 'clear_data'),
              [Input('clear-saved', 'n_clicks')])
def clear(reset_clicks):
    '''Clears memory'''
    if reset_clicks and reset_clicks > 0:
        return True
    else:
        return False


# Displays recipe information based on latest selected recipe in the three tables
@ app.callback(
    Output('recipes_viewer', 'children'),
    Input('table1', 'active_cell'),
    Input('table2', 'active_cell'),
    Input('table3', 'active_cell'),
    State('table1', 'data'),
    State('table2', 'data'),
    State('table3', 'data')
)
def getActiveCell(*inputs):
    active_cells = inputs[:3]
    tables_data = inputs[3:]
    ctx = dash.callback_context

    if not ctx.triggered:
        return []
    elif all([cell is None for cell in active_cells]):
        return []
    else:
        triggered_input = ctx.triggered[0]['prop_id']
        active_cell = ctx.triggered[0]['value']
        if active_cell:
            active_data = ctx.states[triggered_input[:6] + ".data"]
            return show_recipe(active_data[active_cell['row']])
        else:
            return []


if __name__ == '__main__':
    app.run_server(debug=True)
