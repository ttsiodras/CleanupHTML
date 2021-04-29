#!/usr/bin/env python3
import os
import re
import sys
import queue
import logging
import multiprocessing

from typing import List, Any

from bs4 import BeautifulSoup


def process_file(producer_Q, consumer_Q):
    while True:
        work_item = consumer_Q.get()
        level, filename = work_item
        if level == -1:
            return
        res_fname = "/var/tmp/used_files." + str(os.getpid())
        open(res_fname, "a+").write(
            os.path.abspath(
                os.path.realpath(os.getcwd()) + os.sep + filename) + "\n")
        full_path = filename
        logging.info("[-] Processing: %s", full_path)

        data = open(filename, "r").read()

        oldPath = os.getcwd()
        path, unused = os.path.split(filename)
        if path != '':
            os.chdir(path)

        already_done = set()
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
                        "[x] In %s, detected missing '%s'",
                        filename, filename_reference)
                # sys.exit(1)
            else:
                if filename_reference not in already_done:
                    already_done.add(filename_reference)
                    producer_Q.put((level+1, filename_reference))

        if path != '':
            os.chdir(oldPath)
        logging.info(
            "[-] End of processing: %s, remaining items: %d",
            full_path, consumer_Q.qsize())


def main():
    if '-v' in sys.argv:
        logging.basicConfig(level=logging.INFO)

    list_of_processes = []  # type: List[Any]
    producer_Q = multiprocessing.Queue()  # type: Any
    consumer_Q = multiprocessing.Queue()  # type: Any

    for unused in range(multiprocessing.cpu_count()):
        proc = multiprocessing.Process(
            target=process_file, args=(producer_Q, consumer_Q))
        list_of_processes.append(proc)
        proc.start()

    producer_Q.put((0, "index_filtered.html"))
    already_done = set()
    while True:
        try:
            work_item = producer_Q.get(timeout=15)
            level, filename = work_item
            if filename not in already_done:
                already_done.add(filename)
                logging.info(
                    "[-] Queued %s, remaining items: %d",
                    filename, consumer_Q.qsize())
                consumer_Q.put((level, filename))
        except queue.Empty:
            logging.info("[-] All done.")
            break

    for proc in list_of_processes:
        consumer_Q.put((-1, "N/A"))
    for proc in list_of_processes:
        proc.join()
        if proc.exitcode != 0:
            print("[x] Failure in one of the child processes...")
            sys.exit(1)


if __name__ == "__main__":
    main()
