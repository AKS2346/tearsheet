#! /bin/python3
# A simle 'tearsheet' for tickers reading data from yahoo finance
# using yfinance library
# requires rich and plotext libraries as well

import yfinance as yf
import sys
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
import plotext as plt

# set up console and ticker
console = Console()
ticker = yf.Ticker(sys.argv[1])

# Get the initial data and title one of the output tables with ticker name
output = ticker.info
# Fix format for large numbers
output['totalRevenue'] /= 1e6
output['ebitda'] /= 1e6
output['enterpriseValue'] /= 1e6

# Set up left side of first table with data you want
description = {
       'longBusinessSummary': "s",
       }

# Set up right side of first table with data you want
numbers = {
       'currentPrice': "3.1f",
       'ebitdaMargins': "3.1%",
       'profitMargins':"2.1%",
       'grossMargins':"2.1%",
       'revenueGrowth':"2.1%",
       'totalRevenue':",.1f",
       'ebitda':",.2f",
       '52WeekChange': "2.1%",
       #'ytdReturn': "2.1%",
       'numberOfAnalystOpinions': "d",
       'enterpriseValue': ".1f",
       'enterpriseToRevenue': ".1f",
       'enterpriseToEbitda': ".1f",
       'targetMedianPrice': ".2f",
   }

# Clean up if can't find some numbers
for i in numbers:
    if not output[i] :
        output[i] = 0

# Create some lists of the data for each side of the first table
left = [f"[yellow]{i}: [green]{output[i]:{description[i]}}" for i in description]
right = [f"[yellow]{i}: [green]{output[i]:{numbers[i]}}" for i in numbers]



# get some more data to show EBITDA and Capex and Debt/cash
cf = ticker.cashflow
fins = ticker.financials
bs = ticker.balancesheet
fins = fins.append(cf.loc['Depreciation'])
fins = fins.append(cf.loc['Capital Expenditures'])
fins.loc['EBITDA'] = fins.loc['Ebit'] + fins.loc['Depreciation']

# Not all companies report Long-term Debt apparently
try:
    fins = fins.append(bs.loc['Long Term Debt'])
except:
    fins.loc['Long Term Debt'] = 0
fins = fins.append(bs.loc['Cash'])


# put financials into a string
fins = fins/1e6
fins.loc['Net_Debt_to_EBITDA'] = (fins.loc['Long Term Debt'] - fins.loc['Cash']) / fins.loc['EBITDA']
fins_string = fins.loc[
    [
        'Total Revenue',
        'Cost Of Revenue',
        'Gross Profit',
        'Operating Income',
        'EBITDA',
        'Capital Expenditures',
        'Cash',
        'Long Term Debt',
        'Net_Debt_to_EBITDA',
        ],
    :
    ].to_string()

# Set up the terminal graph for stock prices and put to the graph string
period = '1y'
interval = '1wk'
half_screen = int(console.size[0]/2.5)
graph_height = int(len(output['longBusinessSummary']) / half_screen)
try:
     hist = ticker.history(period = period, interval = interval)
     y = hist.Close
     plt.datetime.set_datetime_form(date_form='%m/%d/%Y')
     x = [plt.datetime.datetime_to_string(el) for el in hist.index]
     plt.plot_size(half_screen,graph_height)
     plt.plot_date(x,y, marker = 'dot')
     plt.clc()
     plt.ticks_color('green')
     # special function to report graph as a string rather than plt.show()
     graph_string = plt.build()
except:
    graph_string = "[red] No graph available"

# Print everything out!
# Print the first table
table1 = Table(title = f"{output['shortName']:s}", box=box.MINIMAL)
table1.add_column("Description", justify = 'left')
table1.add_column("52 Week Stock Chart", no_wrap = True)
table1.add_row(output['longBusinessSummary'], graph_string)
console.print(table1)

# Set up the financials and graph table
table2 = Table()
table2.add_column("Basic financials")
table2.add_column("Key Stats")
table2.add_row(fins_string, Columns(right))
console.print(table2)

# Set up the last table with news and recommendations
table3 = Table()
table3.add_column("News")
table3.add_column(f"Recommendations. Median Target: {output['targetMedianPrice']: 3.2f}")

# get the news
news = [i['title'] for i in ticker.news]
table3.add_row(Columns(news), ticker.recommendations.sort_index(ascending = False).head(5).to_string())
console.print(table3)



