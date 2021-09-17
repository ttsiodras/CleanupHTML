#!/usr/bin/env pypy3
import os
import sys
import pickle


def main():
    if len(sys.argv) != 2:
        print("Usage: " + sys.argv[0] +
              " <folderWithHTML/index.final.html>")
        sys.exit(1)

    set_of_all_htmls = pickle.load(open("set_of_all_htmls", "rb"))
    references = pickle.load(open("references", "rb"))
    set_of_remaining_htmls = set([os.path.realpath(sys.argv[1])])
    worker_set = set_of_remaining_htmls.copy()
    seen = set()
    while worker_set:
        source = worker_set.pop()
        if source not in seen:
            seen.add(source)
            for r in references[source]:
                worker_set.add(r)
    for f in set_of_all_htmls-seen:
        print("rm \"" + f + "\"")


if __name__ == "__main__":
    main()
