# CAMT Ofxer

[![MIT License](http://img.shields.io/badge/license-MIT-blue.svg?style=flat)](LICENSE)

<img src="./ofxer.png" width="400">

CSV CAMT to OFX converter tuned to German banking format.
A script for converting CSV CAMT files exported from your bank account.

> mostly using [csv2ofx](https://github.com/reubano/csv2ofx)

## Requirements
```sh
$ pip3 install -r requirements.txt
```

## Usage
### Terminal
```sh
$ python3 ofxer.py your_bank.csv -c 1 4 11 14
```

```
$ python3 ofxer.py --help
usage: ofxer.py [-h] [-p PARSER] [-o OUTPUT] [-s SKIPROWS] [-e ENCODING] -c USECOLS [USECOLS ...] csvfile

CSV CAMT to OFX converter tuned to German banking format.
A script for converting CSV CAMT files exported from your bank account.

positional arguments:
  csvfile               csv file exported from your credit or bank acount

options:
  -h, --help            show this help message and exit
  -p PARSER, --parser PARSER
                        specify the date format if special e.g. 'd/m/Y'
  -o OUTPUT, --output OUTPUT
                        path to write ofx file (default: output.ofx)
  -s SKIPROWS, --skiprows SKIPROWS
                        skipping number of csv file headers (incl. column name)
  -e ENCODING, --encoding ENCODING
                        file encoding
  -c USECOLS [USECOLS ...], --usecols USECOLS [USECOLS ...]
                        column index number of
                          date memo title amount
                          (e.g. --usecols 1 4 11 14)
                          Note: counting from ZERO
```

### Python
```python
from ofxer import Ofxer
options = {
    'credit1': {'skiprows': 10, 'usecols': [0, 1, 8, 13]   },
    'credit2': {'skiprows':  7, 'usecols': [0, 1, 2, 16]   },
    'bank':    {'skiprows':  1, 'usecols': [0, 1, 4, 3]},
    }
credit1 = Ofxer('data/credit1.csv', options['credit1'])
print(credit1._df)
credit1.write_ofx('credit1.ofx')
```

## License
This code is released under the MIT License, see [LICENSE](LICENSE)
