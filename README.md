# Introduction

This is a tool for Canadian investors (tbh, money losers) to calculate (cumulative) realized gain and loss and book
costs given a spread sheet of trade transactions. This tool should be useful when trade activities are spanning across
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

Expected data format in the spread sheet:
* `Date` - date of the transaction
* `Symbol` - ticker symbol - recommended to fill in the RIC code
* `Action` - any of BUY SELL DIV FXFEE
* `Quantity` - (real number) quantity - always positive
* `Price` - (real number) price - always positive
* `Account` - the account associated with the transaction - recommended to be indexed by `<currency>-<account_type>`,
    eg. `USD-TFSA`
* `Fee CAD` - fee (and outstanding tax) associated with the transaction
* `Fee USD` - fee (and outstanding tax) associated with the transaction

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

PLEASE REMEMBER TO DELETE SENSITIVE DATA AFTER USE. (eg. the sqlite db and the csv): Assuming the spread sheet is called
`INVESTMENT_TRANSACTIONS - Transactions` and assuming on a windows machine:

```sh
del "INVESTMENT_TRANSACTIONS - Transactions*"
```
