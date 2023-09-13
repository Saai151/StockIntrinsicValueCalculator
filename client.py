import json
from urllib3 import HTTPResponse
from urllib.request import urlopen
from yahoo_fin.stock_info import *
import yfinance as yf
import pandas as pd
import numpy as np
#from yahoo_fin.stock_info import get_data, tickers_sp500, tickers_nasdaq, tickers_other, get_quote_table

taxRate = 0.25

apiKey = '38dd7a23359bf049cb3ade570d6ad53b'
TIKR = str(input("Please enter the TIKR of the stock you would like to get info on: "))

def get_jsonparsed_data(url):
    """
    Receive the content of ``url``, parse it as JSON and return the object.

    Parameters
    ----------
    url : str

    Returns
    -------
    dict
    """
    response = urlopen(url)
    data = response.read().decode("utf-8")
    return json.loads(data)

url_profile = 'https://financialmodelingprep.com/api/v3/profile/' + TIKR + '?apikey=38dd7a23359bf049cb3ade570d6ad53b'
url_fcf = 'https://financialmodelingprep.com/api/v3/cash-flow-statement/' + TIKR + '?apikey=' + apiKey + '&limit=120'

def getFCF(data):
    fcf = []
    for i in range(len(data)):
        fcf.append(data[i]['freeCashFlow'])
    return fcf

def get_fcf(TIKR):
    analysis = get_analysts_info(TIKR)
    fcf = getFCF(get_jsonparsed_data(url_fcf))
    fcfGrowthRate = analysis['Growth Estimates'][TIKR].to_numpy()[4]
    return fcfGrowthRate, fcf

def get_wacc(TIKR):
    ## Calculating Equity
    treasureYield10 = yf.Ticker("^TNX")
    risk_free_rate = treasureYield10.fast_info['last_price']/100
    
    ## We will assume 10% return on the rate of the market, average return of s&P500
    marketReturn = 0.1
    stock = yf.Ticker(TIKR)
    beta = stock.info['beta']
    
    ke = risk_free_rate + beta*(marketReturn - risk_free_rate)
    
    stock_bal = stock.balance_sheet
  
    equityWeight = stock_bal.loc['Stockholders Equity'][0]/ stock_bal.loc["Total Assets"][0]


    ## Calculating Debt
    stock_Fin = stock.financials

    kd = stock_Fin.loc["Interest Expense Non Operating"][0] *-1 / stock_bal.loc["Total Liabilities Net Minority Interest"][0]

    debtWeight = stock_bal.loc["Total Liabilities Net Minority Interest"][0]/ stock_bal.loc["Total Assets"][0]
    
    # Tax Rate
    tax_rate = stock_Fin.loc["Tax Provision"][0] / stock_Fin.loc["Pretax Income"][0]
    #print(tax_rate)
    
    ## Calculating the WACC
    WACC = (equityWeight * ke) + ((debtWeight * kd ) * (1-tax_rate))
    

    return WACC

def future_fcf(growthRate, fcf):
  futureFcf = []
  for i in range(5):
    futureFcf.append(fcf[0]*(1+growthRate)**i)
  return futureFcf

def get_terminal_value(fcf, wacc):
  perpetualGrowth = 0.02
  terminalValue = fcf[0]*(1+perpetualGrowth)/(wacc-perpetualGrowth)
  #print(terminalValue)
  return terminalValue

def intrinsic_value(wacc, futureFcf, terminal):
  intrinsicValue = 0
  for i in range(5):
    intrinsicValue += futureFcf[i]/(1+wacc)
  return intrinsicValue + terminal
  
    

def main():
    fcfGrowth, fcf = get_fcf(TIKR)
    fcfGrowth = float(fcfGrowth[:len(fcfGrowth)-1])/100
    wacc = get_wacc(TIKR)
    #print(wacc)

    #print(fcfGrowth)
    futureFcf = future_fcf(fcfGrowth, fcf)
    #print(futureFcf)
    terminalValue = get_terminal_value(fcf, wacc)
    intrinsicValue = intrinsic_value(wacc, futureFcf, terminalValue)
    numberShares = get_jsonparsed_data('https://financialmodelingprep.com/api/v3/enterprise-values/'+TIKR+'?limit=40&apikey=38dd7a23359bf049cb3ade570d6ad53b')[0]['numberOfShares']
    print("The current intrinsic value of this stock is: $" + str(round(intrinsicValue/numberShares, 2)))

if __name__ == "__main__":
    main()
  
'''
def percentChangeFcf(fcf):
    fcf.reverse()
    percentChange = []
    for i in range(len(fcf)):
        if i < len(fcf)-1:
            percentChange.append(((fcf[i]-fcf[i+1])/abs(fcf[i]))*100)
    return percentChange
'''