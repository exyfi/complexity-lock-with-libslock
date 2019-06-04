import subprocess
import sys
import os
import matplotlib.pyplot as plt

proc = 8
critical = 2000000
parallel_factors = [0.1, 0.5, 1, 2, 4, 8, 12, 16]

def gen_triples():
    return [(proc, critical, int(critical * x)) for x in parallel_factors] + [
#        (8, 20000000, 20000000),
    ]

ranges = {
    (8, 2000000, 16000000): (1860000, 1910000),
    (8, 2000000, 24000000): (1865000, 1920000),
    (8, 2000000, 32000000): (1860000)
}

def log_file(proc, critical, parallel):
    return "logs/arrivals-%d-%d-%d.txt" % (proc, critical, parallel)

def plot_file(proc, critical, parallel):
    return "plots/plot-%d-%d-%d.png" % (proc, critical, parallel)

def run():
    if not os.path.exists("logs"):
        os.mkdir("logs")

    triples = gen_triples()
    print(triples)
    for triple in triples:
        command = "./locking_scheme.clh -proc %d -critical %d -parallel %d -arrival 1 -iterations 10000" % triple
        print(command)
        subprocess.call(command, shell=True)

def plot():
    if not os.path.exists("plots"):
        os.mkdir("plots")

    triples = gen_triples()
    for triple in triples:
        log = log_file(triple[0], triple[1], triple[2])
        if not os.path.exists(log):
            continue
        f = open(log, 'r')
        x = [int(line) for line in f.readlines()]

        x.sort()
        margin = int(0.025 * len(x))
        x = x[margin:len(x) - margin]

        r = (x[0], x[-1])
        if triple in ranges:
            r = ranges[triple]

        plt.clf()
        n, bits, patches = plt.hist(x, 100, range=r)
        plt.savefig(plot_file(triple[0], triple[1], triple[2]))

if sys.argv[1] == "run":
    run()
if sys.argv[1] == "plot":
    plot()