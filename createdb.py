#!/usr/bin/env pypy3
import os
import re
import sys
from collections import defaultdict
import pickle


def main():
    if len(sys.argv) != 2:
        print("Usage: " + sys.argv[0] + " <folderWithHTML>")
        sys.exit(1)

    s = re.compile(r'^([^:]*):(.*)')
    t = re.compile(r'^.*?href="([^"].*?)"(.*)')
    u = re.compile(r'^(.*)/[^/]*$')
    v = re.compile(r'^(.*)#.*$')

    set_of_all_htmls = set()
    references = defaultdict(set)
    cmd = "grep href $(find \"" + sys.argv[1] + "\" -type f -iname '*.html')"
    print("[-] Counting links...")
    total = os.popen(cmd + " | wc -l").readlines()[0].strip()
    print("[-] Processing links...")
    for idx, line in enumerate(os.popen(cmd).readlines()):
        line = line.strip()
        if idx & 16383 == 16383:
            print("[-] Processed:", idx, "/", total)
            sys.stdout.flush()
        m = s.match(line)
        if m:
            source = m.group(1)
            if not os.path.exists(source):
                continue
            source = os.path.realpath(source)
            set_of_all_htmls.add(source)
            folder = re.match(u, source).group(1)
            m = t.match(m.group(2))
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
                    set_of_all_htmls.add(realp)
                    references[source].add(realp)
                m = t.match(m.group(2))
    print("[-] Dumping set_of_all_htmls and references...")
    pickle.dump(set_of_all_htmls, open("set_of_all_htmls", "wb"))
    pickle.dump(references, open("references", "wb"))
    print("[-] All done.")


if __name__ == "__main__":
    main()
