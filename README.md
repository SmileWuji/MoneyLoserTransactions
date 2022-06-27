# Introduction

This is a tool for Canadian investors (tbh, money losers) to calculate (cumulative) realized gain and loss and book
costs given a spreadsheet of trade transactions. This tool should be useful when trade activities are spanning across
multiple brokers or accounts.

Usage: Download the spreadsheet as CSV and run the following command, assuming the spread sheet is called
`INVESTMENT_TRANSACTIONS - Transactions`.

```sh
python investment_transaction_csv_to_db.py --csv "INVESTMENT_TRANSACTIONS - Transactions" | python investment_transaction_db_summary.py
```

# Dependencies

```sh
python --version
pip install tabulate
```

# Usage

Expected data format in the spreadsheet:
* `Date` - date of the transaction
* `Symbol` - ticker symbol - recommended to fill in the RIC code
* `Action` - any of BUY SELL DIV FXFEE
* `Quantity` - (real number) quantity - always positive
* `Price` - (real number) price - always positive
* `Account` - the account associated with the transaction - recommended to be indexed by `<currency>-<account_type>`,
    eg. `USD-TFSA`
* `Fee CAD` - fee (and outstanding tax) associated with the transaction
* `Fee USD` - fee (and outstanding tax) associated with the transaction

It is also required to put a dummy transaction for each year.

Sample spreadsheet CSV (`INVESTMENT_TRANSACTIONS - Dummy.csv`):
```
Date,Symbol,Action,Quantity,Price,Account,USD-TFSA,Fee CAD,Fee USD
2021-06-01,SYMBOL-1,SELL,200,11.00,CAD-RRSP,9.99,
2021-02-01,SYMBOL-2,BUY,300,50.00,USD,,9.99
2021-01-01,SYMBOL-1,BUY,100,10.00,CAD-RRSP,9.99,
2021-01-01,DUMMY-TX,SELL,,,CAD,0,
2021-01-01,DUMMY-TX,SELL,,,CAD-RRSP,0,
2021-01-01,DUMMY-TX,SELL,,,CAD-TFSA,0,
2021-01-01,DUMMY-TX,SELL,,,CAD,,0
2021-01-01,DUMMY-TX,SELL,,,CAD-RRSP,,0
2021-01-01,DUMMY-TX,SELL,,,CAD-TFSA,,0
```

Sample output produced by the sample result:

```
$ python investment_transaction_csv_to_db.py --csv "INVESTMENT_TRANSACTIONS - Dummy" | python investment_transaction_db_summary.py
# Realized gain by year, symbol, account
  Year  Symbol    Account      CurrentTotalRealizedGain    CurrentTotalDividend
------  --------  ---------  --------------------------  ----------------------
  2021  SYMBOL-1  CAD-RRSP                         2000                       0

# Realized gain by year, account
  Year  Account      CurrentTotalRealizedGain    CurrentTotalDividend
------  ---------  --------------------------  ----------------------
  2021  CAD                                 0                       0
  2021  CAD-RRSP                         2000                       0
  2021  CAD-TFSA                            0                       0
  2021  USD                                 0                       0

# Fee by year
  Year  Account      Fee
------  ---------  -----
  2021  CAD         0
  2021  CAD-RRSP   39.98
  2021  CAD-TFSA    0
  2021  USD        19.99

# Holdings
Symbol    Account      Quantity    AverageCostBasis    BookValue  LastActivity
--------  ---------  ----------  ------------------  -----------  --------------
SYMBOL-2  USD              3000               49.99       149970  2021-02-01

Done.
```

The `BAD_SYMBOLS` variable in `investment_transaction_csv_to_db.py` contains a set of bad symbols which will be ignored
by this tool.

Run the following commands for more details:

```sh
python investment_transaction_csv_to_db.py --help
python investment_transaction_db_summary.py --help
```

# Important

PLEASE USE AT YOUR OWN RISK. THIS TOOL MAY CONTAIN BUGS OR MAY CONTAIN UNEXPECTED RESULT IF THE USER HAS A DIFFERENT
EXPECTATION OF THE WRITER OF THIS TOOL.

PLEASE REMEMBER TO DELETE SENSITIVE DATA AFTER USE. (eg. the sqlite db and the csv): Assuming the spreadsheet is called
`INVESTMENT_TRANSACTIONS - Transactions` and assuming on a windows machine:

```sh
del "INVESTMENT_TRANSACTIONS - Transactions*"
```
