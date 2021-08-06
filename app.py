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
from dask import dataframe as ddf


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


start = time.time()


df = ddf.read_csv("recipe_data_final_new.csv")

recipes = df.compute()
recipes = recipes.iloc[:100]
recipes["ingredients"] = recipes["ingredients"].apply(convert_ingred)
recipes["instructions"] = recipes["instructions"].apply(convert_instruct)
recipes["ratings"] = recipes["ratings"].apply(convert_rating)

# recipes = pd.read_csv("recipe_data_final_new.csv", converters={
#                       'ingredients': convert_ingred, 'instructions': convert_instruct, 'ratings': convert_rating},
#                       skiprows=1000, chunksize=1000)


recipes = recipes.dropna(subset=['title'])
recipes = recipes[recipes["ingredients"].apply(lambda x: len(x) != 0)]
recipes = recipes.loc[recipes["url"] != "https://www.koket.se/godfather"]
recipes = recipes.reset_index(drop=True)
recipes["rating"] = recipes['ratings'].apply(lambda x:
                                             x['rating_value'] if 'rating_value' in x and x['rating_value'] else 0)

with open('recommendations.json', 'r') as fp:
    recommendations = json.load(fp)

recipes = recipes.sort_values(by='rating', ascending=False)

end = time.time()
print(end-start, "sec")


def get_recommnded_recipes(saved_urls):
    recommended_urls = []
    for url in saved_urls:
        recommended_urls.extend(recommendations.get(url, []))
    recommended_urls = list(set(recommended_urls))
    recommended_recipes = recipes[recipes["url"].isin(recommended_urls)]
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
                     for i in recipes.columns if i in show_columns],
            # data=recipes_show.to_dict('records'),
            # row_selectable="multi",
            # selected_rows=[],
            editable=True,
            row_deletable=True,
            style_data={'whiteSpace': 'normal', 'height': 'auto'},
            style_table={'height': '350px', 'overflowX': 'scroll',
                         'textOverflow': 'ellipsis',
                         # 'maxHeight': '500px',
                         'paddingTop': '2px'
                         }
        )], style={'width': '30%', 'display': 'inline-block', "margin-left": "15px"}),
        html.Div(children=[html.H1("Recommended recipes"),
                           dash_table.DataTable(
            id='table2',
            columns=[{"name": i, "id": i}
                     for i in recipes.columns if i in show_columns],
            # data=INITIAL_empty,
            editable=True,
            row_deletable=True,
            style_data={'whiteSpace': 'normal', 'height': 'auto'},
            style_table={'height': '350px', 'overflowX': 'scroll',
                         'textOverflow': 'ellipsis',
                         # 'maxHeight': '500px',
                         'paddingTop': '2px'
                         }
        )], style={'width': '30%', 'display': 'inline-block', "margin-left": "15px"}),
        html.Div(children=[html.H1("Saved recipes"),
                           dash_table.DataTable(
            id='table3',
            columns=[{"name": i, "id": i}
                     for i in recipes.columns if i in show_columns],
            # data=INITIAL_empty,
            editable=True,
            row_deletable=True,
            style_data={'whiteSpace': 'normal', 'height': 'auto'},
            style_table={'height': '350px', 'overflowX': 'scroll',
                         'textOverflow': 'ellipsis',
                         # 'maxHeight': '500px',
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
            removed_recipe = recipes.loc[recipes["url"] == removed_url].to_dict('records')[
                0]
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
              #Input('saved_recipes', 'modified_timestamp'),
              Input('saved_recipes', 'data'))
# Input('saved_recipes', 'data'))
def display_popular_recommended_recipes(saved_recipes):
    if saved_recipes:
        saved_urls = [rec['url'] for rec in saved_recipes]
        recipes_without_saved = recipes[~recipes['url'].isin(saved_urls)]
        recommended_recipes = get_recommnded_recipes(saved_urls)
        recommended_recipes_urls = recommended_recipes["url"].tolist()
        # Always show top 50 most popular recipes of the recipes lefft after removing saved and recommended
        popular_recipes = recipes_without_saved[~recipes_without_saved['url'].isin(
            recommended_recipes_urls)].iloc[:50]
        return popular_recipes.to_dict('records'), recommended_recipes.to_dict('records'), saved_recipes
    else:
        return recipes.iloc[:50].to_dict('records'), INITIAL_empty, INITIAL_empty


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
