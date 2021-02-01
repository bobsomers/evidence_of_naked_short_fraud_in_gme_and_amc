#!/usr/bin/env python3

import bisect
import dateparser
from datetime import datetime

import sys

FAILS_DATA = [
    'cnsfails201901a.txt',
    'cnsfails201901b.txt',
    'cnsfails201902a.txt',
    'cnsfails201902b.txt',
    'cnsfails201903a.txt',
    'cnsfails201903b.txt',
    'cnsfails201904a.txt',
    'cnsfails201904b.txt',
    'cnsfails201905a.txt',
    'cnsfails201905b.txt',
    'cnsfails201906a.txt',
    'cnsfails201906b.txt',
    'cnsfails201907a.txt',
    'cnsfails201907b.txt',
    'cnsfails201908a.txt',
    'cnsfails201908b.txt',
    'cnsfails201909a.txt',
    'cnsfails201909b.txt',
    'cnsfails201910a.txt',
    'cnsfails201910b.txt',
    'cnsfails201911a.txt',
    'cnsfails201911b.txt',
    'cnsfails201912a.txt',
    'cnsfails201912b.txt',
    'cnsfails202001a.txt',
    'cnsfails202001b.txt',
    'cnsfails202002a.txt',
    'cnsfails202002b.txt',
    'cnsfails202003a.txt',
    'cnsfails202003b.txt',
    'cnsfails202004a.txt',
    'cnsfails202004b.txt',
    'cnsfails202005a.txt',
    'cnsfails202005b.txt',
    'cnsfails202006a.txt',
    'cnsfails202006b.txt',
    'cnsfails202007a.txt',
    'cnsfails202007b.txt',
    'cnsfails202008a.txt',
    'cnsfails202008b.txt',
    'cnsfails202009a.txt',
    'cnsfails202009b.txt',
    'cnsfails202010a.txt',
    'cnsfails202010b.txt',
    'cnsfails202011a.txt',
    'cnsfails202011b.txt',
    'cnsfails202012a.txt',
    'cnsfails202012b.txt',
]

OUTSTANDING_DATA = {
    'GME': 'gme_shares.txt',
    'AMC': 'amc_shares.txt',
    'BB': 'bb_shares.txt',
    'M': 'm_shares.txt',
    'NOK': 'nok_shares.txt',
    'AAPL': 'aapl_shares.txt',
    'MSFT': 'msft_shares.txt',
    'AMZN': 'amzn_shares.txt',
    'FB': 'fb_shares.txt',
    'TSLA': 'tsla_shares.txt',
    'GOOGL': 'googl_shares.txt',
    'GOOG': 'goog_shares.txt',
    'BRKB': 'brk.b_shares.txt',
    'JNJ': 'jnj_shares.txt',
    'JPM': 'jpm_shares.txt',
    'GE': 'ge_shares.txt',
}


def load_fails_data(data_files):
    by_date = {}
    by_ticker = {}

    for filename in data_files:
        print('Loading {}'.format(filename))

        with open(filename, encoding='latin-1') as f:
            content = f.readlines()

            for line in content[1:-2]:
                try:
                    (settlement_date, cusip, ticker, fails, name, price) = line.strip().split('|', 6)
                except Exception as e:
                    print(line)
                    print(e)

                settlement_date = datetime(int(settlement_date[0:4]),
                                           int(settlement_date[4:6]),
                                           int(settlement_date[6:8]))

                fails = int(fails)

                try:
                    price = float(price)
                except:
                    price = 0.0

                if settlement_date not in by_date:
                    by_date[settlement_date] = {}
                if ticker not in by_ticker:
                    by_ticker[ticker] = {}
                data = {
                    'fails': fails,
                    'price': price,
                }
                by_date[settlement_date][ticker] = data
                by_ticker[ticker][settlement_date] = data

    return by_date, by_ticker


def load_outstanding_data(data_files):
    outstanding_by_ticker = {}

    for ticker, filename in data_files.items():
        print('Loading {}'.format(filename))
        with open(filename) as f:
            content = f.readlines()
            for line in content:
                (month, day, year, shares) = line.strip().split()
                date = dateparser.parse('{} {} {}'.format(month, day, year))

                share_unit = shares[-1]
                if share_unit == 'M':
                    shares = int(float(shares[:-1]) * 1000000)
                elif share_unit == 'B':
                    shares = int(float(shares[:-1]) * 1000000000)

                if ticker not in outstanding_by_ticker:
                    outstanding_by_ticker[ticker] = {}
                outstanding_by_ticker[ticker][date] = shares

    return outstanding_by_ticker


def compute_fails_as_percent_outstanding(outstanding_by_ticker, fails_by_ticker):

    for ticker in outstanding_by_ticker.keys():
        outst_dates = []
        outst_shares = []
        for key in sorted(outstanding_by_ticker[ticker].keys()):
            outst_dates.append(key)
            outst_shares.append(outstanding_by_ticker[ticker][key])

        for date, data in fails_by_ticker[ticker].items():
            idx = bisect.bisect_right(outst_dates, date) - 1
            total_shares = outst_shares[idx]
            data['fails_percent'] = float(data['fails']) * 100 / float(total_shares)


def aggregate_into_months(fails_by_ticker, tickers):
    aggregated = {}

    for ticker in tickers:
        current_month = 0
        failed_shares_as_pct = 0.0
        for key in sorted(fails_by_ticker[ticker].keys()):
            if key.month != current_month:
                current_month = key.month
                failed_shares_as_pct = 0.0

            failed_shares_as_pct += fails_by_ticker[ticker][key]['fails_percent']

            month = datetime(key.year, key.month, 1)
            if month not in aggregated:
                aggregated[month] = {}
            aggregated[month][ticker] = failed_shares_as_pct

    return aggregated


def output_aggregated_ticker_fails(monthly, tickers, filename):
    header = ['DATE']
    for ticker in tickers:
        header.append(ticker)
    output = [','.join(header)]

    for key in sorted(monthly.keys()):
        line = ['{}-{}'.format(key.year, key.month)]
        for ticker in tickers:
            failed_pct = monthly[key][ticker]
            line.append(str(failed_pct))
        output.append(','.join(line))

    with open(filename, 'w') as f:
        f.writelines('{}\n'.format(line) for line in output)


if __name__ == '__main__':
    print('Loading outstanding shares data')
    outstanding_by_ticker = load_outstanding_data(OUTSTANDING_DATA)

    print('Loading SEC failed to deliver data')
    fails_by_date, fails_by_ticker = load_fails_data(FAILS_DATA)

    print('Normalizing failed to deliver shares by outstanding shares')
    compute_fails_as_percent_outstanding(outstanding_by_ticker, fails_by_ticker)

    print('Aggregating into monthly amounts')
    monthly = aggregate_into_months(fails_by_ticker, outstanding_by_ticker.keys())

    print('Writing ticker fails by date to ticker_fails.csv')
    output_aggregated_ticker_fails(monthly, outstanding_by_ticker.keys(), 'ticker_fails.csv')
