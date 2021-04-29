#!/usr/bin/env python3
import os
import re
import sys
import logging

from bs4 import BeautifulSoup


def process_file(level, filename, cache=[set()]):  # pylint: disable=W0102
    if filename in cache[0]:
        return
    if level > 1:
        return
    open("/var/tmp/used_files", "a+").write(
        os.path.abspath(
            os.path.realpath(os.getcwd()) + os.sep + filename) + "\n")
    full_path = filename
    logging.info("Begin processing: %s", full_path)
    cache[0].add(filename)

    data = open(filename, "r").read()

    oldPath = os.getcwd()
    path, unused = os.path.split(filename)
    if path != '':
        os.chdir(path)

    soup = BeautifulSoup(data, 'html.parser')
    for link in soup.find_all("a"):
        filename_reference = link.get('href')
        if filename_reference is None or filename_reference == '':
            continue
        filename_reference = re.sub(r'#.*$', r'', filename_reference)
        if filename_reference == '':
            continue
        if not os.path.exists(filename_reference):
            if all(x not in filename_reference
                   for x in ['x86_64-linux-gnu', 'gcc-config']) and \
               all(x not in filename
                   for x in ['x86_64-linux-gnu', 'gcc-config']):
                logging.warning(
                    "[%s] Missing '%s'",
                    filename, filename_reference)
            # sys.exit(1)
        else:
            if filename_reference not in cache[0]:
                process_file(level+1, filename_reference)

    if path != '':
        os.chdir(oldPath)
    logging.info("End processing: %s", full_path)


def main():
    if '-v' in sys.argv:
        logging.basicConfig(level=logging.INFO)
    process_file(0, "index_filtered.html")


if __name__ == "__main__":
    main()
