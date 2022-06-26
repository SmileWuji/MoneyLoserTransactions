from optparse import OptionParser
import csv
import sqlite3

def parse_options():
    parser = OptionParser()
    parser.add_option("-c", "--csv", dest="csv_name",
        help="The CSV file name (without .csv) of the investment transaction spreadsheet")
    (opt, args) = parser.parse_args()
    if opt.csv_name is None:
        parser.error("Missing csv_name")
    return opt

FLOAT_EPS = 0.000000119

# The following symbols will be ignored by this tool
BAD_SYMBOLS = {'DLR.TO', 'DLR.TO-U'}

# Note: the table schema in SQL is different from the spreadsheet
# (1) The Quantity column will be negative when Action is SELL
INVESTMENT_TRANSACTION_TABLE_SCHEMA = '''
CREATE TABLE InvestmentTransactions (
    RecordDate DATE NOT NULL,
    Symbol VARCHAR(16) NOT NULL,
    Action VARCHAR(16) NOT NULL,
    Quantity FLOAT(53) NOT NULL,
    Price FLOAT(53) NOT NULL,
    Account VARCHAR(16) NOT NULL,
    Fee FLOAT(53) NOT NULL)
'''

INVESTMENT_TRANSACTION_TABLE_INSERT = '''
INSERT INTO InvestmentTransactions (RecordDate,Symbol,Action,Quantity,Price,Account,Fee)
VALUES (?, ?, ?, ?, ?, ?, ?)
'''

HISTORICAL_HOLDINGS_QUERY = '''
SELECT Symbol, Account
FROM InvestmentTransactions
GROUP BY Symbol, Account
'''

TRANSACTIONS_PER_SYMBOL_QUERY = '''
SELECT *
FROM InvestmentTransactions
WHERE Symbol = ? AND Account = ?
ORDER BY RecordDate
'''

# Note: the average cost basis here would be the amount before dividends, distributions and fees
AVERAGE_COST_BASIS_SCHEMA = '''
CREATE TABLE AverageCostBasis (
    SequenceNumber INTEGER PRIMARY KEY,
    RecordDate DATE NOT NULL,
    Symbol VARCHAR(16) NOT NULL,
    Account VARCHAR(16) NOT NULL,
    Action VARCHAR(16) NOT NULL,
    CurrentQuantity FLOAT(53) NOT NULL,
    CurrentAverageCostBasis FLOAT(53) NOT NULL,
    CurrentTotalFee FLOAT(53) NOT NULL,
    CurrentTotalRealizedGain FLOAT(53) NOT NULL,
    CurrentTotalDividend FLOAT(53) NOT NULL)
'''

AVERAGE_COST_BASIS_INSERT = '''
INSERT INTO AverageCostBasis (
    SequenceNumber,
    RecordDate,
    Symbol,
    Account,
    Action,
    CurrentQuantity,
    CurrentAverageCostBasis,
    CurrentTotalFee,
    CurrentTotalRealizedGain,
    CurrentTotalDividend)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
'''

if __name__ == '__main__':
    opt = parse_options()
    csv_path = opt.csv_name + '.csv'
    db_path = opt.csv_name + '.db'
    with open(db_path, 'w') as fs:
        pass
    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        cur.execute(INVESTMENT_TRANSACTION_TABLE_SCHEMA)
        # Compute transactions
        with open(csv_path, 'r') as fs:
            transaction_csv = csv.DictReader(fs)
            for row in transaction_csv:
                csv_date = row['Date']
                csv_symbol = row['Symbol']
                csv_action = row['Action']
                csv_quantity = row['Quantity'].replace(',', '')
                csv_price = row['Price'].replace(',', '')
                csv_account = row['Account']
                csv_fee_cad = row['Fee CAD'].replace(',', '')
                csv_fee_usd = row['Fee USD'].replace(',', '')

                # sanity check: either csv_fee_cad or csv_fee_usd could have value
                assert csv_fee_cad == '' or csv_fee_usd == '', "Invalid CSV fee values: {}".format(row)

                # sanity check: when csv_action is FXFEE csv_price must be None
                if csv_action == 'FXFEE':
                    assert csv_price == '', "Invalid CSV FXFEE row: {}".format(row)

                csv_fee_resolved = csv_fee_cad if csv_fee_cad != '' else csv_fee_usd

                db_record_date = csv_date
                db_symbol = csv_symbol
                db_action = csv_action
                db_quantity = float(csv_quantity) if csv_quantity != '' else 0
                db_price = float(csv_price) if csv_price != '' else 0
                db_account = csv_account
                db_fee = float(csv_fee_resolved) if csv_fee_resolved != '' else 0

                if db_action == 'SELL':
                    db_quantity = -db_quantity

                db_row = (db_record_date, db_symbol, db_action, db_quantity, db_price, db_account, db_fee)
                cur.execute(INVESTMENT_TRANSACTION_TABLE_INSERT, db_row)
        con.commit()
        # Compute average cost basis
        cur.execute(AVERAGE_COST_BASIS_SCHEMA)
        symbol_account_to_cost_basis = dict()
        it = cur.execute(HISTORICAL_HOLDINGS_QUERY)
        for db_row in it:
            row_symbol = db_row[0]
            row_account = db_row[1]
            if row_symbol in BAD_SYMBOLS:
                continue
            k = row_symbol + ':' + row_account
            symbol_account_to_cost_basis[k] = {
                'RecordDate': None,
                'Symbol': row_symbol,
                'Account': row_account,
                'Action': None,
                'CurrentQuantity': 0.0,
                'CurrentAverageCostBasis': 0.0,
                'CurrentTotalFee': 0.0,
                'CurrentTotalRealizedGain': 0.0,
                'CurrentTotalDividend': 0.0,
            }
        # Sequence number is used to break-even when multiple transactions occur at the same date
        sequence_number = 0
        ro_cur = con.cursor()
        for k in symbol_account_to_cost_basis:
            symbol_account_row = symbol_account_to_cost_basis[k]
            it = ro_cur.execute(TRANSACTIONS_PER_SYMBOL_QUERY, (
                symbol_account_row['Symbol'],
                symbol_account_row['Account']))
            for transaction_row in it:
                row_record_date = transaction_row[0]
                row_symbol = transaction_row[1]
                row_action = transaction_row[2]
                row_quantity = transaction_row[3]
                row_price = transaction_row[4]
                row_account = transaction_row[5]
                row_fee = transaction_row[6]

                prev_quantity = symbol_account_row['CurrentQuantity']
                prev_average_cost_basis = symbol_account_row['CurrentAverageCostBasis']
                prev_total_fee = symbol_account_row['CurrentTotalFee']
                prev_realized_gain = symbol_account_row['CurrentTotalRealizedGain']
                prev_total_dividend = symbol_account_row['CurrentTotalDividend']
                prev_total_book = (prev_quantity * prev_average_cost_basis)

                symbol_account_row['RecordDate'] = row_record_date
                symbol_account_row['Action'] = row_action
                symbol_account_row['CurrentQuantity'] += row_quantity

                curr_total_book = None
                if symbol_account_row['CurrentQuantity'] > FLOAT_EPS:
                    if row_action == 'BUY':
                        curr_total_book = prev_total_book + (row_quantity * row_price)
                        symbol_account_row['CurrentAverageCostBasis'] = \
                            curr_total_book / symbol_account_row['CurrentQuantity']
                    elif row_action == 'SELL':
                        curr_total_book = prev_total_book + (row_quantity * prev_average_cost_basis)
                        symbol_account_row['CurrentAverageCostBasis'] = prev_average_cost_basis
                else:
                    curr_total_book = 0.0
                    symbol_account_row['CurrentAverageCostBasis'] = 0.0

                symbol_account_row['CurrentTotalFee'] += row_fee

                if row_action == 'SELL':
                    # Update CurrentTotalRealizedGain
                    realized_gain = (row_quantity * prev_average_cost_basis) - (row_quantity * row_price)
                    symbol_account_row['CurrentTotalRealizedGain'] += realized_gain
                elif row_action == 'DIV':
                    # Update CurrentTotalDividend
                    symbol_account_row['CurrentTotalDividend'] += row_price

                db_row = (
                    sequence_number,
                    symbol_account_row['RecordDate'],
                    symbol_account_row['Symbol'],
                    symbol_account_row['Account'],
                    symbol_account_row['Action'],
                    symbol_account_row['CurrentQuantity'],
                    symbol_account_row['CurrentAverageCostBasis'],
                    symbol_account_row['CurrentTotalFee'],
                    symbol_account_row['CurrentTotalRealizedGain'],
                    symbol_account_row['CurrentTotalDividend'],
                )
                sequence_number += 1
                cur.execute(AVERAGE_COST_BASIS_INSERT, db_row)
    print(db_path)
