#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, csv, heapq, shutil
from optparse import OptionParser


class CsvSortError(Exception):
    pass


def csvsort(input_filename, columns, output_filename='', max_size=100, has_header=True, delimiter=',', quoting=csv.QUOTE_MINIMAL, encoding='utf-8'):
    """Sort the CSV file on disk rather than in memory
    The merge sort algorithm is used to break the file into smaller sub files and

    :param input_filename: the CSV filename to sort
    :param columns: a list of column to sort on (can be 0 based indices or header keys)
    :param output_filename: optional filename for sorted file. If not given then input file will be overriden.
    :param max_size: the maximum size (in MB) of CSV file to load in memory at once
    :param has_header: whether the CSV contains a header to keep separated from sorting
    :param delimiter: character used to separate fields, default ','
    :param quoting: type of quoting used in the output
    :param encoding: file encoding used in input/output files
    """
    tmp_dir = '.csvsorter.{}'.format(os.getpid())
    os.makedirs(tmp_dir, exist_ok=True)

    try:
        with open(input_filename, 'r', encoding=encoding) as input_fp:
            reader = csv.reader(input_fp, delimiter=delimiter)
            if has_header:
                header = next(reader)
            else:
                header = None

            columns = parse_columns(columns, header)

            filenames = csvsplit(reader, max_size, encoding, tmp_dir)
            print('Merging {} splits'.format(len(filenames)))
            for filename in filenames:
                memorysort(filename, columns, encoding)
            sorted_filename = mergesort(filenames, columns, tmp_dir=tmp_dir, encoding=encoding)

        # XXX make more efficient by passing quoting, delimiter, and moving result
        # generate the final output file
        with open(output_filename or input_filename, 'w', newline='\n', encoding=encoding) as output_fp:
            writer = csv.writer(output_fp, delimiter=delimiter, quoting=quoting)
            if header:
                writer.writerow(header)
            with open(sorted_filename, 'r', encoding=encoding) as sorted_fp:
                rows = csv.reader(sorted_fp)
                writer.writerows(rows)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def parse_columns(columns, header):
    """check the provided column headers
    """
    for i, column in enumerate(columns):
        if isinstance(column, int):
            if (header and column >= len(header)):
                raise CsvSortError('Column index is out of range: "{}"'.format(column))
        else:
            # find index of column from header
            if header:
                if column in header:
                    columns[i] = header.index(column)
                else:
                    raise CsvSortError('Column name is not found in header: "{}"'.format(column))
            else:
                raise CsvSortError('CSV needs a header to find index of this column name: "{}"'.format(column))
    return columns


def csvsplit(reader, max_size, encoding, tmp_dir):
    """Split into smaller CSV files of maximum size and return the list of filenames
    """
    max_size = max_size * 1024 * 1024 # convert to bytes
    writer = None
    current_size = 0
    split_filenames = []

    # break CSV file into smaller merge files
    for row in reader:
        if not writer:
            filename = os.path.join(tmp_dir, 'split{}.csv'.format(len(split_filenames)))
            writer = csv.writer(open(filename, 'w', newline='\n', encoding=encoding))
            split_filenames.append(filename)

        writer.writerow(row)
        current_size += sys.getsizeof(row)
        if current_size > max_size:
            writer = None
            current_size = 0
    return split_filenames


def memorysort(filename, columns, encoding):
    """Sort this CSV file in memory on the given columns
    """
    with open(filename, encoding=encoding) as input_fp:
        rows = list(csv.reader(input_fp))
    rows.sort(key=lambda row: [row[column] for column in columns])
    with open(filename, 'w', newline='\n', encoding=encoding) as output_fp:
        writer = csv.writer(output_fp)
        writer.writerows(rows)


def yield_csv_rows(filename, columns, encoding):
    """Iterator to sort CSV rows
    """
    with open(filename, 'r', encoding=encoding) as fp:
        for row in csv.reader(fp):
            yield row


def mergesort(sorted_filenames, columns, nway=2, tmp_dir='', encoding='utf-8'):
    """Merge these 2 sorted csv files into a single output file
    """
    merge_n = 0
    while len(sorted_filenames) > 1:
        merge_filenames, sorted_filenames = sorted_filenames[:nway], sorted_filenames[nway:]

        output_filename = os.path.join(tmp_dir, 'merge{}.csv'.format(merge_n))
        with open(output_filename, 'w', newline='\n', encoding=encoding) as output_fp:
            writer = csv.writer(output_fp)
            merge_n += 1
            rows = (yield_csv_rows(filename, columns, encoding) for filename in merge_filenames)
            writer.writerows(heapq.merge(*rows))
        sorted_filenames.append(output_filename)

        for filename in merge_filenames:
            os.remove(filename)
    return sorted_filenames[0]


def main():
    parser = OptionParser()
    parser.add_option('-c', '--column', dest='columns', action='append', help='column of CSV to sort on')
    parser.add_option('-s', '--size', '-s', dest='max_size', type='float', default=100, help='maximum size of each split CSV file in MB (default 100)')
    parser.add_option('-n', '--no-header', dest='has_header', action='store_false', default=True, help='set CSV file has no header')
    parser.add_option('-d', '--delimiter', default=',', help='set CSV delimiter (default ",")')
    parser.add_option('-e', '--encoding', default='utf-8', help='encoding to use for input/output files')
    args, input_files = parser.parse_args()

    if not input_files:
        parser.error('What CSV file should be sorted?')
    elif not args.columns:
        parser.error('Which columns should be sorted on?')
    else:
        # escape backslashes
        args.columns = [int(column) if column.isdigit() else column for column in args.columns]
        csvsort(input_files[0], columns=args.columns, max_size=args.max_size, has_header=args.has_header, delimiter=args.delimiter, encoding=args.encoding)


if __name__ == '__main__':
    main()
