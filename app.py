# Author: Cayson Seipel
# Datadive 5

import pandas as pd
import numpy as np
from datetime import date
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import  Output, Input
import plotly.graph_objects as go
import missingno as msn

# Import the datasets
dino = pd.read_csv("dinosaur.csv")
everest = pd.read_csv("expedition_everest.csv")
passage = pd.read_csv("flight_of_passage.csv")
safari = pd.read_csv("kilimanjaro_safaris.csv")
navi = pd.read_csv("navi_river.csv")

# Create lists to represent the dataframes and the suffix to add to the duplicate column names
dfs = [dino, everest, passage, safari, navi]
names = ["_dino", "_everest", "_passage", "_safari", "_navi"]

# Iterate through the dataframes
for df in range(len(dfs)):
    dfs[df].drop(["SACTMIN", "date"], axis = 1, inplace = True) # Drop the date field and the actual time field
    dfs[df].dropna(subset = ["SPOSTMIN"], inplace = True) # Drop the NaNs where there is an NaN
    dfs[df].rename({"SPOSTMIN": "SPOSTMIN" + names[df]}, axis = 1, inplace = True) # Rename the duplicate column names
    dfs[df]["datetime"] = pd.to_datetime(dfs[df].datetime) # Convert the datetime column to a datetime type

# Priming merge
data_df = pd.merge(dino, everest, how = "outer")

# merge the dataframes into a new, complete dataframe
for df in range(2, len(dfs)):
    data_df = pd.merge(data_df, dfs[df], how = "outer")

# Create new columns for the year, month, day, and hour for ease of use
data_df["Year"] = data_df["datetime"].dt.year
data_df["Month"] = data_df["datetime"].dt.month
data_df["Day"] = data_df["datetime"].dt.day
data_df["Hour"] = data_df["datetime"].dt.hour


# Check the dataset
print(msn.matrix(data_df))

# Sort the values by date and time
data_df.sort_values("datetime", inplace = True)

# Check the dataset after sort
print(msn.matrix(data_df))

# Backfill every posted time per ride
for col in ["SPOSTMIN_dino", "SPOSTMIN_everest", "SPOSTMIN_passage", "SPOSTMIN_safari", "SPOSTMIN_navi"]:
    data_df[col] = data_df.groupby(["Year", "Month", "Day"])[col].bfill()

# Check the dataset after the backfill
print(msn.matrix(data_df))

# Check for the missing values
data_df.info()

# Fill in the remaining values with -999 to show that the ride is closed
data_df.replace(-999, np.nan, inplace = True)

# Get a visualization of the missing data now that the -999s have been replaced
print(msn.matrix(data_df))

# -------------------------------------
# Set up the Dash application
# https://realpython.com/python-dash/
# -------------------------------------

# External stylesheets for the app
external_stylesheets = [{"href": "https://fonts.googleapis.com/css2?"
                        "family=Lato:wght@400;700&display=swap",
                        "rel": "stylesheet"}]

# Create the app and add title
app = dash.Dash(__name__, external_stylesheets = external_stylesheets)
server = app.server
app.title = "Average Past Wait Times for Disney's Animal Kingdom"

# App layout
# App header
app.layout = html.Div([
        html.Div([
            html.H1(children = "Disney's Animal Kingdom Ride Wait Times", className = "header-title"),
            html.P(children = "This application gives the ride wait times of Disney's Animal Kingdom rides: "
                    "Expedition Everest, Dinosaur, Flight of Passage, Kilimanjaro Safaris, and the Navi River by date.", className = "header-description")
                    ],
            className = "header"),
        # App Body (Includes the menu and the two graphs)
        html.Div([
            # Menus option for ride
            html.Div([
                html.Div("Ride", className = "menu-title"),
                dcc.Dropdown(
                    id = "ride-filter",
                    options = [
                        {"label": "All", "value": "All"},
                        {"label": "Expedition Everest", "value": "SPOSTMIN_everest"},
                        {"label": "Dinosaur", "value": "SPOSTMIN_dino"},
                        {"label": "Flight of Passage", "value": "SPOSTMIN_passage"},
                        {"label": "Kilimanjaro Safaris", "value": "SPOSTMIN_safari"},
                        {"label": "Navi River", "value": "SPOSTMIN_navi"}
                        ],
                        value = "All",
                        clearable = False,
                        searchable = False
                )
            ],
            className = "dropdown"
            ),
            # Menu option for date
            html.Div([
                html.Div("Date", className = "menu-title"),
                dcc.DatePickerSingle(
                    id = "date-filter",
                    min_date_allowed = date(2021, 1, 1),
                    max_date_allowed = date(2022, 12, 31),
                    initial_visible_month = date.today(),
                    date = date.today()
                ),
            ],
            className = "dropdown")
        ],
        className = "menu"
        ),
        # Line graph
        html.Div(
            dcc.Graph(
                id = "line-chart",
                config = {"displayModeBar": False},
            ),
            className = "card",
        ),
        # Box plot
        html.Div(
            dcc.Graph(
                id = "bar-chart",
                config = {"displayModeBar": False},
            ),
            className = "card",
        ),
    ]
)

# Gets updates in the menu and sends it to the update_charts function
@app.callback(
    [Output("line-chart", "figure"), Output("bar-chart", "figure")],
    [Input("ride-filter", "value"), Input("date-filter", "date")]
)

# Update the charts based on the menu options
def update_charts(ride, date):
    # column names and ride names in the same order for easy access
    col = ["SPOSTMIN_dino", "SPOSTMIN_everest", "SPOSTMIN_passage", "SPOSTMIN_safari", "SPOSTMIN_navi"]
    name = ["Dinosaur", "Expedition Everest", "Flight of Passage", "Kilimanjaro Safaris", "Navi River"]
    date = pd.to_datetime(date) # Change the datefield to datetime type

    # Update the graph if all of the rides are selected
    if ride == "All":
        # Initialize the two graphs and set up their options
        line_chart_figure = go.Figure()
        line_chart_figure.update_layout(title = "Average Wait Time by Hour", xaxis_title = "Hour", yaxis_title = "Average Wait Time", plot_bgcolor = "#363636", paper_bgcolor = "#363636", font_color = "#00897b")
        bar_chart_figure = go.Figure()
        bar_chart_figure.update_layout(title = "Park Busyness by Year", xaxis_title = "Year", yaxis_title = "Park Busyness", plot_bgcolor = "#363636", paper_bgcolor = "#363636", font_color = "#00897b")

        # Iterate through the columns for the rides and add a line and bar to the line and bar graph respectively
        for r in range(len(col)):
            # Only use the data from the day and month selected
            # https://stackoverflow.com/questions/17071871/how-to-select-rows-from-a-dataframe-based-on-column-values
            data = data_df.loc[(data_df["Day"] == date.day) & (data_df["Month"] == date.month)]
            # Find the mean wait time for each hour
            means = data.groupby(["Hour"])[col[r]].mean()
            # add a line to the graph based on hour and the means
            line_chart_figure.add_trace(go.Scatter(x = list(set(data.apply(list)["Hour"])), y = means, mode = "lines+markers", name = name[r]))
            # Update the means to be based on year for the bar
            means = data.groupby(["Year"])[col[r]].mean()
            # Sort the years
            sorted = list(set(data.apply(list)["Year"]))
            sorted.sort()
            # Add a bar to the graph
            bar_chart_figure.add_trace(go.Bar(x = sorted, y = means, name = name[r]))
    else: # A single ride was chosen
        # Get the data for the day and month selected
        data = data_df.loc[(data_df["Day"] == date.day) & (data_df["Month"] == date.month)]
        # Find the means based on the hour
        means = data.groupby(["Hour"])[ride].mean()

        # Create the line graph for the one ride
        line_chart_figure = go.Figure()
        line_chart_figure.update_layout(title = "Average Wait Time by Hour", xaxis_title = "Hour", yaxis_title = "Average Wait Time", plot_bgcolor = "#363636", paper_bgcolor = "#363636", font_color = "#00897b")
        line_chart_figure.add_trace(go.Scatter(x = list(set(data.apply(list)["Hour"])), y = means, mode = "lines+markers", name = name[col.index(ride)]))
        # Update the means to be based on year
        means = data.groupby(["Year"])[ride].mean()
        # Sort the means by year
        sorted = list(set(data.apply(list)["Year"]))
        sorted.sort()
        # Create the bar graph for the one ride
        bar_chart_figure = go.Figure()
        bar_chart_figure.update_layout(title = "Park Busyness by Year", xaxis_title = "Year", yaxis_title = "Park Busyness", plot_bgcolor = "#363636", paper_bgcolor = "#363636", font_color = "#00897b")
        bar_chart_figure.add_trace(go.Bar(x = sorted, y = means))

    # Return the figures to be graphed
    return line_chart_figure, bar_chart_figure

# Run the server
if __name__ == "__main__":
    app.run_server()
