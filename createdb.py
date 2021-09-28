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
    t = re.compile(r'^.*?href="([^"].*?)"(.*)')
    u = re.compile(r'^(.*)/[^/]*$')
    v = re.compile(r'^(.*)#.*$')

    references = defaultdict(set)
    while True:
        work_item = consumer_Q.get()
        filename = work_item
        if filename == "":
            # print("\n[-] Worked instructed to abort. Worker exiting...")
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
        print("\r[-] Remaining: %6d" % consumer_Q.qsize(), end='')
    producer_Q.put(references)


def main():
    if len(sys.argv) != 2:
        print("Usage: " + sys.argv[0] + " <folderWithHTML>")
        sys.exit(1)

    all_html_files = []
    for root, unused_dirs, files in os.walk(sys.argv[1]):
        for f in files:
            if any(f.endswith(x) for x in ['.html', '.htm']):
                all_html_files.append(os.path.abspath(root + os.sep + f))

    list_of_processes = []  # type: List[Any]
    producer_Q = multiprocessing.Queue()  # type: Any
    consumer_Q = multiprocessing.Queue()  # type: Any

    total = len(all_html_files)
    print("[-] Queueing %d HTML files..." % total)

    for unused in range(multiprocessing.cpu_count()):
        proc = multiprocessing.Process(
            target=process_file, args=(producer_Q, consumer_Q))
        list_of_processes.append(proc)
        proc.start()

    for idx, f in enumerate(all_html_files):
        consumer_Q.put(f)

    for proc in list_of_processes:
        consumer_Q.put("")

    set_of_all_htmls = set(all_html_files)
    references = defaultdict(set)

    for idx, proc in enumerate(list_of_processes):
        while True:
            try:
                references_computed = producer_Q.get()
                if idx == 0:
                    print("")
                print("[-] Obtained result from worker %d" % idx)
                for k, v_list in references_computed.items():
                    for v in v_list:
                        references[k].add(v)
                break
            except queue.Empty:
                time.sleep(1)
    for idx, proc in enumerate(list_of_processes):
        proc.join()
        if proc.exitcode != 0:
            print("[x] Failure in one of the child processes...")
            sys.exit(1)
    print("[-] Dumping set_of_all_htmls and references...")
    pickle.dump(set_of_all_htmls, open("set_of_all_htmls", "wb"))
    pickle.dump(references, open("references", "wb"))
    print("[-] All done.")


if __name__ == "__main__":
    main()
