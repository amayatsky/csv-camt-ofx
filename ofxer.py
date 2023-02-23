#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2023 MXXIV.net, Alexander Mayatsky
#
# This software is released under the MIT License.
# http://opensource.org/licenses/mit-license.php

"""
CSV CAMT to OFX converter tuned to German banking format.
A script for converting CSV CAMT files exported from your bank account.
"""

import csv
import os
import itertools as it
import pandas as pd
from csv2ofx import utils
from csv2ofx.ofx import OFX
from io import StringIO
from meza.io import read_csv, IterStringIO
from operator import itemgetter

import argparse
import textwrap


class Ofxer:
    """ OFX Converter """
    def __init__(self, csvfile, option):
        """
        load csvfile using option

        :param string csvfile: path of csvfile
        :param dict option: loading options
        """
        if not os.path.exists(csvfile):
            raise FileNotFoundError

        # options you must have
        for k in ['skiprows', 'usecols']:
            if k not in option:
                raise AttributeError("option['{}'] missing.".format(k))
        # options you might have
        for k in ['parser', 'encoding']:
            if k not in option:
                option[k] = None

        col_num = len(option['usecols'])
        if col_num != 4:
            raise AttributeError("length of option['usecols'] must be 4")

        self._df = self.__load_csv(csvfile, option)

    def __load_csv(self, csvfile, option):

        colnames = ['date', 'memo', 'title', 'amount']
        
        df = pd.read_csv(csvfile, index_col=0, sep=';',
                         skiprows=option['skiprows'],
                         usecols=option['usecols'],
                         encoding=option['encoding'],
                         names=colnames)

        # parse datetime and remove invalid rows
        def __try_todate(text):
            try:
                pd.to_datetime(text, format=option['parser'])
                return True
            except Exception:
                return False
        df = df[df.index.map(lambda x: __try_todate(x))]
        df.index = pd.to_datetime(df.index, format=option['parser'])

        # make missing value to empty string
        df['title'].fillna('', inplace=True)
        df['memo'].fillna('', inplace=True)
        df['amount'].fillna(0, inplace=True)
        df = df[~df.isnull().any(axis=1)]

        # trim special characters
        def __to_num(df):
            if df.dtype == 'object':
                df = df.str.replace('.', '', regex=False) # 1.890,41 -> 1890,41
                df = df.str.replace(',', '.', regex=False) # 1890,41 -> 1890.41
                df = df.astype(float)
            return df
        
        # trim whitespaces to single spaces
        def __trim(df):
            if df.dtype == 'object':
                df = df.str.replace(r'\s+', ' ', regex=True)
            return df
        
        df['amount'] = __to_num(df['amount'])
        df['title'] = __trim(df['title'])
        df['memo'] = __trim(df['memo'])
        
        return df

    def write_ofx(self, ofxfile, debug=False):
        """ write out ofxfile from DataFrame """
        mapping = {
            'account': 'account',
            'date': itemgetter('date'),
            'payee': itemgetter('title'),
            'amount': itemgetter('amount'),
            'desc': itemgetter('memo')
            }

        ofx = OFX(mapping)
        data = self._df.to_csv(quoting=csv.QUOTE_ALL)
        if debug:
            print(self._df)
        records = read_csv(StringIO(data))
        groups = ofx.gen_groups(records)
        cleaned_trxns = ofx.clean_trxns(groups)
        data = utils.gen_data(cleaned_trxns)
        content = it.chain([ofx.header(), ofx.gen_body(data), ofx.footer()])

        with open(ofxfile, 'wb') as f:
            for line in IterStringIO(content):
                f.write(line)


def col_act():
    # Note: https://stackoverflow.com/questions/4194948/python-argparse-is-there-a-way-to-specify-a-range-in-nargs
    class ColumnAction(argparse.Action):
        def __call__(self, parser, args, values, option_string=None):
            nmin = 4
            nmax = 4
            if not nmin <= len(values) <= nmax:
                msg = 'argument "{f}" requires between {nmin} and {nmax} arguments'.format(
                    f=self.dest, nmin=nmin, nmax=nmax)
                raise argparse.ArgumentTypeError(msg)
            # check duplication
            if len(values) != len(set(values)):
                msg = 'argument "{f} {v}" duplicated'.format(
                    f=self.dest, v=values)
                raise argparse.ArgumentTypeError(msg)

            setattr(args, self.dest, values)
    return ColumnAction


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                prog='ofxer.py',
                description='CSV CAMT to OFX converter tuned to German banking format.\nA script for converting CSV CAMT files exported from your bank account.',
                formatter_class=argparse.RawTextHelpFormatter,
                epilog='-------------------------------------------------------------------------------',
                add_help=True,
                )

    parser.add_argument('csvfile',          action='store',   nargs=None,                          help='csv file exported from your credit or bank acount')
    parser.add_argument('-p', '--parser',   action='store',   nargs=None, default='%d.%m.%y',      help="specify the date format if special e.g. 'y/m/d")
    parser.add_argument('-o', '--output',   action='store',   nargs=None, default='output.ofx',    help='path to write ofx file (default: output.ofx)')
    parser.add_argument('-s', '--skiprows', action='store',   nargs=None, default=1, type=int,     help='skipping number of csv file headers (incl. column name)')
    parser.add_argument('-e', '--encoding', action='store',   nargs=None, default='unicode_escape',help='file encoding')
    parser.add_argument('-c', '--usecols',  action=col_act(), nargs='+',  required=True, type=int, help=textwrap.dedent('''\
                                                                                                        column index number of
                                                                                                          date memo title amount
                                                                                                          (e.g. --usecols 1 4 11 14)
                                                                                                          Note: counting from ZERO
                                                                                                        '''))

    args = parser.parse_args()

    options = {'parser': args.parser,
               'skiprows': args.skiprows,
               'usecols': args.usecols,
               'encoding': args.encoding}

    ofxer = Ofxer(args.csvfile, options)
    ofxer.write_ofx(args.output, True)

    print('Successfully converted to {}'.format(args.output))
