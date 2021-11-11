#!/usr/bin/env pypy3
import os
import re
import sys
import time
import queue
import multiprocessing
from collections import defaultdict
import pickle

from typing import List, Any


def process_file(producer_Q, consumer_Q):
    t = re.compile(r'^.*?href="([^"]*)"(.*)')
    u = re.compile(r'^(.*)/[^/]*$')
    v = re.compile(r'^(.*)#.*$')

    references = defaultdict(set)
    while True:
        work_item = consumer_Q.get()
        filename = ""  # Appease pylint
        for filename in work_item:
            if filename == "":
                # print("\n[-] Worker instructed to abort. Exiting...")
                break
            folder = u.match(filename).group(1)
            for line in open(filename):
                if 'href' not in line:
                    continue
                m = t.match(line)
                while m:
                    link = m.group(1)
                    if link.startswith('#'):
                        m = t.match(m.group(2))
                        continue
                    q = v.match(link)
                    if q:
                        link = q.group(1)
                    realp = os.path.realpath(folder + os.sep + link)
                    if os.path.exists(realp):
                        references[filename].add(realp)
                    m = t.match(m.group(2))
            print("\r[-] Remaining batches: %d " % consumer_Q.qsize(), end='')
        if filename == "":
            break
    producer_Q.put(references)


def main():
    if len(sys.argv) != 2:
        print("Usage: " + sys.argv[0] + " <folderWithHTML>")
        sys.exit(1)

    print("[-] Scanning for HTML files...")
    all_html_files = []
    for root, unused_dirs, files in os.walk(sys.argv[1]):
        for f in files:
            if any(f.endswith(x) for x in ['.html', '.htm']):
                all_html_files.append(os.path.abspath(root + os.sep + f))

    list_of_processes = []  # type: List[Any]
    producer_Q = multiprocessing.Queue()  # type: Any
    consumer_Q = multiprocessing.Queue()  # type: Any

    total = len(all_html_files)

    cores = multiprocessing.cpu_count()
    for unused in range(cores):
        proc = multiprocessing.Process(
            target=process_file, args=(producer_Q, consumer_Q))
        list_of_processes.append(proc)

    # Trade-off between too many and too few context-switches.
    #
    # In theory, spliting the list exactly by number-of-cores,
    # creates a perfect workload for each of the 'cores'.
    # Sadly, that's not the case - because the .html files
    # may or may not have 'href's; meaning that one task may
    # finish quite quickly, and have nothing to do.
    #
    # On the other end, if we split by too much, we waste
    # time in the workers context-switching (to read from the
    # consumer_Q) instead of processing HTML hrefs!
    batch = []
    batch_size = total / (10*cores)

    for f in all_html_files:
        batch.append(f)
        if len(batch) >= batch_size:
            consumer_Q.put(batch)
            batch = []
    if batch:
        consumer_Q.put(batch)
    print("[-] Queueing %d HTML files as %d batches..." % (
        total, consumer_Q.qsize()))

    # Put markers signifying "no more data" for all workers
    for proc in list_of_processes:
        consumer_Q.put([""])

    # Start them all!
    for proc in list_of_processes:
        proc.start()

    set_of_all_htmls = set(all_html_files)
    references = defaultdict(set)

    for proc in list_of_processes:
        while True:
            try:
                references_computed = producer_Q.get()
                for k, v_list in references_computed.items():
                    for v in v_list:
                        references[k].add(v)
                break
            except queue.Empty:
                time.sleep(1)
    for proc in list_of_processes:
        proc.join()
        if proc.exitcode != 0:
            print("[x] Failure in one of the child processes...")
            sys.exit(1)
    print("\n[-] Dumping set_of_all_htmls and references...")
    pickle.dump(set_of_all_htmls, open("set_of_all_htmls", "wb"))
    pickle.dump(references, open("references", "wb"))
    print("[-] All done.")


if __name__ == "__main__":
    main()
