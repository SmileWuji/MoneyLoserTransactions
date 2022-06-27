from optparse import OptionParser
import sqlite3
from tabulate import tabulate

def parse_options():
    parser = OptionParser()
    parser.add_option("-d", "--db", dest="db_name",
        help="The SQLite3 file name (without .db) of the investment transaction table; if missing read from STDIN")
    (opt, args) = parser.parse_args()
    return opt

FLOAT_EPS = 0.000000119

LATEST_AVERAGE_COST_BASIS_BY_YEAR_VIEW_1 = '''
DROP VIEW IF EXISTS LatestAverageCostBasisByYearSequenceNumber
'''

LATEST_AVERAGE_COST_BASIS_BY_YEAR_VIEW_2 = '''
CREATE VIEW LatestAverageCostBasisByYearSequenceNumber (SequenceNumber) AS
SELECT max(SequenceNumber) AS SequenceNumber
FROM AverageCostBasis
GROUP BY strftime("%Y", RecordDate), Symbol, Account
'''

LATEST_AVERAGE_COST_BASIS_BY_YEAR_VIEW_3 = '''
DROP VIEW IF EXISTS LatestAverageCostBasisByYear
'''

LATEST_AVERAGE_COST_BASIS_BY_YEAR_VIEW_4 = '''
CREATE VIEW LatestAverageCostBasisByYear(
    Year,
    Symbol,
    Account,
    RecordDate,
    CurrentQuantity,
    CurrentAverageCostBasis,
    CurrentTotalFee,
    CurrentTotalRealizedGain,
    CurrentTotalDividend) AS
SELECT
    strftime("%Y", RecordDate) AS Year,
    Symbol,
    Account,
    RecordDate,
    CurrentQuantity,
    CurrentAverageCostBasis,
    CurrentTotalFee,
    CurrentTotalRealizedGain,
    CurrentTotalDividend
FROM AverageCostBasis NATURAL JOIN LatestAverageCostBasisByYearSequenceNumber
'''

LATEST_REALIZED_GAIN_VIEW_1 = '''
DROP VIEW IF EXISTS LatestRealizedGain
'''

LATEST_REALIZED_GAIN_VIEW_2 = '''
CREATE VIEW LatestRealizedGain(
    Year,
    Symbol,
    Account,
    CurrentTotalRealizedGain,
    CurrentTotalDividend) AS
SELECT
    Year,
    Symbol,
    Account,
    CurrentTotalRealizedGain,
    CurrentTotalDividend
FROM LatestAverageCostBasisByYear
'''

LATEST_REALIZED_GAIN_QUERY_1 = '''
SELECT *
FROM LatestRealizedGain
WHERE abs(CurrentTotalRealizedGain) > {} OR abs(CurrentTotalDividend) > {}
ORDER BY Year, Symbol, Account
'''.format(FLOAT_EPS, FLOAT_EPS)

LATEST_REALIZED_GAIN_QUERY_2 = '''
SELECT
    Year,
    Account,
    sum(CurrentTotalRealizedGain) AS NonCumulativeTotalRealizedGain,
    sum(CurrentTotalDividend) AS NonCumulativeTotalDividend
FROM LatestRealizedGain
GROUP BY Year, Account
ORDER BY Year, Account
'''

FEE_BY_YEAR_QUERY = '''
SELECT
    Year,
    Account,
    sum(CurrentTotalFee) AS Fee
FROM LatestAverageCostBasisByYear
GROUP BY Year, Account
ORDER BY Year, Account;
'''

HOLDINGS_QUERY = '''
SELECT
    Symbol,
    Account,
    max(CurrentQuantity) AS Quantity,
    max(CurrentAverageCostBasis) AS AverageCostBasis,
    max(CurrentQuantity) * max(CurrentAverageCostBasis) AS BookValue,
    max(RecordDate) AS LastActivity
FROM AverageCostBasis
GROUP BY Symbol, Account
HAVING SequenceNumber >= max(SequenceNumber) AND CurrentQuantity > {}
ORDER BY Symbol, Account
'''.format(FLOAT_EPS)

if __name__ == '__main__':
    opt = parse_options()

    db_path = None
    if opt.db_name is None:
        db_path = input().strip()
    else:
        db_path = opt.db_name + '.db'

    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        cur.execute(LATEST_AVERAGE_COST_BASIS_BY_YEAR_VIEW_1)
        cur.execute(LATEST_AVERAGE_COST_BASIS_BY_YEAR_VIEW_2)
        cur.execute(LATEST_AVERAGE_COST_BASIS_BY_YEAR_VIEW_3)
        cur.execute(LATEST_AVERAGE_COST_BASIS_BY_YEAR_VIEW_4)
        cur.execute(LATEST_REALIZED_GAIN_VIEW_1)
        cur.execute(LATEST_REALIZED_GAIN_VIEW_2)

        print('# Realized gain by year, symbol, account')
        it = cur.execute(LATEST_REALIZED_GAIN_QUERY_1)
        print(tabulate(it.fetchall(), headers=[
            'Year', 'Symbol', 'Account', 'CurrentTotalRealizedGain', 'CurrentTotalDividend'
        ]))
        print()

        print('# Realized gain by year, account')
        it = cur.execute(LATEST_REALIZED_GAIN_QUERY_2)
        print(tabulate(it.fetchall(), headers=[
            'Year', 'Account', 'CurrentTotalRealizedGain', 'CurrentTotalDividend'
        ]))
        print()

        print('# Fee by year')
        it = cur.execute(FEE_BY_YEAR_QUERY)
        print(tabulate(it.fetchall(), headers=['Year', 'Account', 'Fee']))
        print()

        print('# Holdings')
        it = cur.execute(HOLDINGS_QUERY)
        print(tabulate(it.fetchall(), headers=[
            'Symbol', 'Account', 'Quantity', 'AverageCostBasis', 'BookValue', 'LastActivity']))
        print()
    print('Done.')
