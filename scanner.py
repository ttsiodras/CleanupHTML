#!/usr/bin/env python3
import os
import re
import sys
import logging

from bs4 import BeautifulSoup


def process_file(filename, cache=[set()]):
    if filename in cache[0]:
        return
    open("/var/tmp/used_files", "a+").write(
        os.path.abspath(
            os.path.realpath(os.getcwd()) + os.sep + filename) + "\n")
    full_path = filename
    logging.info("Begin processing: " + full_path)
    cache[0].add(filename)

    data = open(filename, "r").read()

    oldPath = os.getcwd()
    path, ext = os.path.split(filename)
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
                logging.warn(
                    "[" + filename + "] Missing '" + filename_reference + "'")
            # sys.exit(1)
        else:
            if filename_reference not in cache[0]:
                process_file(filename_reference)

    if path != '':
        os.chdir(oldPath)
    logging.info("End processing: " + full_path)


def main():
    if '-v' in sys.argv:
        logging.basicConfig(level=logging.INFO)
    process_file("index.html")


if __name__ == "__main__":
    main()
