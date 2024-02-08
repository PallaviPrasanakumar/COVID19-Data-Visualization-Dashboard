import colorsys
import pandas as pd
import numpy as np
import streamlit as st
from plotly.subplots import make_subplots
from urllib.request import urlopen
import json
import plotly.express as px
from datetime import datetime

path_to_covid_confirmed_file="data/covid_confirmed_usafacts.csv"
path_to_covid_deaths_file="data/covid_deaths_usafacts.csv"
path_to_county_population_file="data/covid_county_population_usafacts.csv"

st.title("USA Countywise Covid-19 Data Analysis Dashboard")

covid_county_population = pd.read_csv(path_to_county_population_file)
covid_county_population = covid_county_population[covid_county_population['countyFIPS']!=0][["countyFIPS","population"]]
covid_county_population['countyFIPS'] = covid_county_population['countyFIPS'].astype(str).apply(lambda x: x.zfill(5))
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

@st.cache(suppress_st_warning=True)
def weekly_aggregate_covid_confirmed_cases(path_to_covid_confirmed_file):
    covid_confirmed_df = pd.read_csv(path_to_covid_confirmed_file, header=0)
    covid_confirmed_df = covid_confirmed_df.set_index(['County Name', 'State', 'countyFIPS','StateFIPS']).stack().reset_index().rename(columns={'level_4':'date', 0:'count'})
    covid_confirmed_df = covid_confirmed_df[covid_confirmed_df['countyFIPS']!=0][["countyFIPS","date","count"]]
    covid_confirmed_df['date']=pd.to_datetime(covid_confirmed_df['date'], format='%Y-%m-%d')
    covid_confirmed_df['Year-Week'] = covid_confirmed_df['date'].dt.strftime('%Y-%U')
    covid_confirmed_df['Day-Name'] = covid_confirmed_df['date'].dt.day_name()
    covid_confirmed_df['Cnt'] = covid_confirmed_df.sort_values(by=['date'], ascending=True).groupby(['countyFIPS'])['count'].diff()
    covid_confirmed_df['Cnt'] = np.where(covid_confirmed_df['Cnt'].isnull(),covid_confirmed_df['count'], covid_confirmed_df['Cnt'])
    covid_confirmed_county_groupedData = covid_confirmed_df.groupby(['countyFIPS',pd.Grouper(key='date', freq='W-SUN')]).filter(lambda x: len(x) > 6)
    covid_confirmed_groupedData = covid_confirmed_county_groupedData.groupby([pd.Grouper(key='date', freq='W-SUN')])['Cnt'].sum().reset_index()
    covid_confirmed_groupedData = covid_confirmed_groupedData.rename(columns={'date':'index', 'Cnt' : 'Confirmed Cases'}).set_index('index')
    return covid_confirmed_county_groupedData,covid_confirmed_groupedData

covid_confirmed_county_groupedData,covid_confirmed_groupedData = weekly_aggregate_covid_confirmed_cases(path_to_covid_confirmed_file)
st.write("### Weekly new confirmed cases of Covid-19 in the USA")
st.line_chart(covid_confirmed_groupedData)

@st.cache(suppress_st_warning=True)
def weekly_aggregate_covid_death_cases(path_to_covid_deaths_file):
    covid_deaths_df = pd.read_csv(path_to_covid_deaths_file, header=0)
    covid_deaths_df = covid_deaths_df.set_index(['County Name', 'State', 'countyFIPS','StateFIPS']).stack().reset_index().rename(columns={'level_4':'date', 0:'count'})
    covid_deaths_df = covid_deaths_df[covid_deaths_df['countyFIPS']!=0][["countyFIPS","date","count"]]
    covid_deaths_df['date']=pd.to_datetime(covid_deaths_df['date'], format='%Y-%m-%d')
    covid_deaths_df['Year-Week'] = covid_deaths_df['date'].dt.strftime('%Y-%U')
    covid_deaths_df['Day-Name'] = covid_deaths_df['date'].dt.day_name()
    covid_deaths_df['Cnt'] = covid_deaths_df.sort_values(by=['date'], ascending=True).groupby(['countyFIPS'])['count'].diff()
    covid_deaths_df['Cnt'] = np.where(covid_deaths_df['Cnt'].isnull(),covid_deaths_df['count'], covid_deaths_df['Cnt'])
    covid_deaths_county_groupedData = covid_deaths_df.groupby(['countyFIPS',pd.Grouper(key='date', freq='W-SUN')]).filter(lambda x: len(x) > 6)
    covid_deaths_groupedData = covid_deaths_county_groupedData.groupby([pd.Grouper(key='date', freq='W-SUN')])['Cnt'].sum().reset_index()
    covid_deaths_groupedData = covid_deaths_groupedData.rename(columns={'date':'index', 'Cnt' : 'Death Cases'}).set_index('index')
    return covid_deaths_county_groupedData,covid_deaths_groupedData

covid_deaths_county_groupedData,covid_deaths_groupedData = weekly_aggregate_covid_death_cases(path_to_covid_deaths_file)
st.write("### Weekly deaths of Covid-19 in the USA")
st.line_chart(covid_deaths_groupedData)

@st.cache(suppress_st_warning=True)
def weekly_aggregate_countywise_covid_data(covid_confirmed_county_groupedData, covid_deaths_county_groupedData):
    covid_confirmed_county_groupedData = covid_confirmed_county_groupedData.groupby(['countyFIPS',pd.Grouper(key='date', freq='W-SUN')])['Cnt'].sum().reset_index()
    covid_confirmed_county_groupedData['countyFIPS'] = covid_confirmed_county_groupedData['countyFIPS'].astype(str).apply(lambda x: x.zfill(5))
    covid_confirmed_county_groupedData['date'] = covid_confirmed_county_groupedData.date.apply(lambda x: x.date()).apply(str)
    covid_confirmed_county_groupedData = pd.merge(covid_confirmed_county_groupedData, covid_county_population, on="countyFIPS", how='left')
    covid_confirmed_county_groupedData['Cnt'] = covid_confirmed_county_groupedData['Cnt'].astype(int) * 100000
    covid_confirmed_county_groupedData['Cnt'] = covid_confirmed_county_groupedData['Cnt'].div(covid_confirmed_county_groupedData['population'])
    covid_deaths_county_groupedData = covid_deaths_county_groupedData.groupby(['countyFIPS',pd.Grouper(key='date', freq='W-SUN')])['Cnt'].sum().reset_index()
    covid_deaths_county_groupedData['countyFIPS'] = covid_deaths_county_groupedData['countyFIPS'].astype(str).apply(lambda x: x.zfill(5))
    covid_deaths_county_groupedData['date'] = covid_deaths_county_groupedData.date.apply(lambda x: x.date()).apply(str)
    covid_deaths_county_groupedData = pd.merge(covid_deaths_county_groupedData, covid_county_population, on="countyFIPS", how='left')
    covid_deaths_county_groupedData['Cnt'] = covid_deaths_county_groupedData['Cnt'].astype(int) * 100000
    covid_deaths_county_groupedData['Cnt'] = covid_deaths_county_groupedData['Cnt'].div(covid_confirmed_county_groupedData['population'])
    return covid_confirmed_county_groupedData,covid_deaths_county_groupedData

covid_confirmed_county_groupedData, covid_deaths_county_groupedData = weekly_aggregate_countywise_covid_data(covid_confirmed_county_groupedData, covid_deaths_county_groupedData)

sl_date = st.select_slider(
     'Select date to show weekly data:',
     options=covid_confirmed_county_groupedData['date'].unique().tolist())

@st.cache(suppress_st_warning=True)
@st.cache(allow_output_mutation=True)
def generate_choropleth_plots(counties, county_groupedData, process_date, title):
    county_filter_groupedData = county_groupedData[county_groupedData['date']==process_date]
    plot = px.choropleth(county_filter_groupedData, geojson=counties, locations='countyFIPS', color='Cnt',
                            color_continuous_scale="Viridis",
                            #range_color=(0, 100000),
                            scope="usa",
                            width=700,
                            height=400,
                            title = title + datetime.strptime(process_date, '%Y-%m-%d').strftime('%Y-%U'),
                            labels={'Cnt':'Confirmed Cases'}
                           )
    plot.update_layout(margin={"r":0,"l":0,"b":0})
    return plot

new_confirmed_plot = generate_choropleth_plots(counties, covid_confirmed_county_groupedData, sl_date,"Countywise New Confirmed Cases for Week ")
new_death_plot = generate_choropleth_plots(counties, covid_deaths_county_groupedData, sl_date,"Countywise Death Cases for Week ")
st.plotly_chart(new_confirmed_plot)
st.plotly_chart(new_death_plot)

if st.button('Start Animation to visualize data for each week in order'):
    plot_confirmed_plot_spot = st.empty()
    plot_death_plot_spot = st.empty()
    for date in covid_confirmed_county_groupedData['date'].unique().tolist():
        animated_confirmed_plot = generate_choropleth_plots(counties, covid_confirmed_county_groupedData, date,"Countywise New Confirmed Cases for Week ")
        animated_death_plot = generate_choropleth_plots(counties, covid_deaths_county_groupedData, date,"Countywise Death Cases for Week ")
        with plot_confirmed_plot_spot:
            st.plotly_chart(animated_confirmed_plot)
        with plot_death_plot_spot:
            st.plotly_chart(animated_death_plot)
