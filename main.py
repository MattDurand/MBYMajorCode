import math
import requests
import calendar
from datetime import datetime, timedelta, date
from pytrends.request import TrendReq
import matplotlib.pyplot as plt

CRYPTO_CURRENCIES = {
    'BITCOIN': 'BTC',
    'ETHEREUM': 'ETH',
    'DOGECOIN': 'DOGE',
    'LITECOIN': 'LTC'
}


def get_historical_data(ticker: str, start_date: datetime, end_date: datetime):
    url = f'https://query1.finance.yahoo.com/v7/finance/download/{ticker}'

    params = {
        'period1': int(start_date.timestamp()),
        'period2': int(end_date.timestamp()),
        'interval': '1d',
        'events': 'history'
    }

    results = {}
    print(f'Getting historical price data for {ticker}')
    with requests.get(url, params) as res:
        # HTTP error checking
        if res.status_code == 404:
            raise ValueError(f'Currency pair "{ticker}" not found!')
        elif res.status_code != 200:
            raise ValueError(f'Error receiving historical price data (Status Code: {res.status_code})')

        # Generator expression
        lines = (ln.decode().split(',') for ln in res.iter_lines())
        headers = next(lines)

        # Parses data returned from Yahoo and populates the results dictionary
        for ln in lines:
            data = dict(zip(headers, ln))
            results[data['Date']] = data
            del data['Date']

    return results


def get_trend_data(term: str, start_date: datetime, end_date: datetime):
    results = {}

    print(f'Getting trend data for "{term}": ')

    # Calculates how many years are between the end date and the start date
    for i in range(math.ceil((end_date - start_date).days / 365)):
        year = (start_date + timedelta(days=365 * i)).year + 1

        for month in range(1, 13):
            timeframe = date(year, month, 1), min(date(year, month, calendar.monthrange(year, month)[-1]),
                                                  end_date.date())

            if timeframe[0] > end_date.date():
                break

            # Building query to get Google Trends fine data for the timeframe
            trend = TrendReq()
            trend.build_payload(kw_list=[term], timeframe=f'{str(timeframe[0])} {str(timeframe[1])}')
            print(f'... Downloading trend data from {str(timeframe[0])} to {str(timeframe[1])}')

            # Parse the trend data and populate the results dictionary
            for d, e in trend.interest_over_time().iterrows():
                results[d.date()] = e[0]

    return results


if __name__ == '__main__':

    for currency in CRYPTO_CURRENCIES:
        epoch = datetime.now()
        time_period = timedelta(days=365 * 1)

        date_range = ((epoch - time_period).date(), epoch.date())
        print(f'Getting data for {currency}')
        print(f'Getting coarse trend data for "{currency}"')
        trend = TrendReq()

        # Building query to get Google Trends coarse data for the timeframe
        trend.build_payload(kw_list=[currency.capitalize()], timeframe=f'{str(date_range[0])} {str(date_range[1])}')

        # Coarse data is a list of tuples that contain the date and the Google Trends score for those dates
        coarse_data = []
        for d, e in trend.interest_over_time().iterrows():
            coarse_data.append((d.date(), e[0]))

        # Gets price data for a given cryptocurrency e.g. Bitcoin -> BTC-EUR
        price_data = get_historical_data(f'{CRYPTO_CURRENCIES[currency.upper()]}-EUR', epoch - time_period, epoch)

        # Gets Google Trends data for a given search term
        trending_data = get_trend_data(currency.capitalize(), epoch - time_period, epoch)

        # Graph axes
        x, y1, y2 = [], [], []

        # Enriching the fine Trending data with the trending scores from the coarse data
        for d, popularity in trending_data.items():
            trending_data[d] += coarse_data[([i for i, data in enumerate(coarse_data) if data[0] > d] + [-1])[0]][1]

        # Adding the data to the graphs axes
        for d, popularity in trending_data.items():
            price = price_data[str(d)]['Open']

            # Catch cases where no price data is available
            if price != 'null':
                x.append(d)
                y1.append(popularity)
                y2.append(float(price))

        fig, ax1 = plt.subplots()
        fig.canvas.manager.set_window_title(currency)
        fig.suptitle(f'{currency} versus search frequency', fontsize=16)
        ax2 = ax1.twinx()
        ax1.plot(x, y1, 'tab:blue')
        ax2.plot(x, y2, 'tab:red')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Relative Search Popularity', color='tab:blue')
        ax2.set_ylabel('Price (€)', color='tab:red')

        # Prevents data being drawn outside the figure
        fig.tight_layout()
        print()
    plt.show()
