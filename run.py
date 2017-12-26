import os
import sys
from statistics import mean, stdev
from gplearn.genetic import SymbolicRegressor

keys = ["throughput"]

src = "./locking_scheme.{}"
lock = "ticket"

duration = 10000
parallel_points = [500, 1000, 5000, 10000, 50000, 100000]
critical_points = [100, 500, 1000, 5000, 10000, 50000, 100000]
parallel_factors = [0.1, 0.5, 1, 2, 4, 5, 10, 15, 20, 25, 30, 35, 40, 50, 80, 100]
critical_factors = [1. / 80, 1. / 50, 1. / 30, 1. / 10, 1. / 4, 1. / 2, 1, 2, 4] #[5, 10, 15, 20, 25, 30]
proc = [5, 10, 20, 30, 39]

def compile():
    command = "make {}".format(lock)
    print(command)
    os.system(command)

def log_file(duration, proc, critical, parallel, lock):
    return "out/log/d{}/{}_{}_{}_{}.txt".format(duration, proc, critical, parallel, lock)

def run_one(duration, proc, critical, parallel, lock):
    out = log_file(duration, proc, critical, parallel, lock)
    command = "{} -time {} -proc {} -critical {} -parallel {} -lock {} > {}".format(src, duration, proc, critical, parallel, lock, out)
    print(command)
    os.system(command)

def run():
    if not os.path.isdir("out/log/d{}".format(duration)):
        os.makedirs("out/log/d{}".format(duration))

    for p in proc:
        for first in ccritical_points:
            for factor in parallel_factors:
                # change parallel first
                run_one(duration, p, first, int(factor * first), lock)
 
        for first in parallel_points:
            for factor in critical_factors:
                # change critical
                run_one(duration, p, int(factor * first), first, lock)

def parse(filename):
    inf = open(filename, 'r')
    values = dict()
    for key in keys:
        values[key] = []
    for line in inf.readlines():
        ll = line.lower()
        good = None
        for key in keys:
            if key.lower() in ll:
                good = key
        if good == None:
            continue
        value = ll.strip().split(":")[1].strip().split(" ")[0]
        values[good].append(float(value))
    return values

def data_file(duration, key, t, proc, point, lock):
    return "data/d{}/{}/{}_{}_{}_{}.dat".format(duration, key, t, proc, point, lock)

throughputs = {}
def all_throughputs():
    for p in proc:
        for first in critical_points:
            for factor in parallel_factors:
                critical = first
                parallel = int(factor * first)
                t = mean(parse(log_file(duration, p, critical, parallel, lock))["throughput"])
                throughputs[(critical, parallel, p)] = t

        for first in parallel_points:
            for factor in critical_factors:
                critical = int(factor * first)
                parallel = first
                t = mean(parse(log_file(duration, p, critical, parallel, lock))["throughput"])
                throughputs[(critical, parallel, p)] = t
    return

def fit_throughput():
    alpha = get_alpha()
    X = []
    y = []
    for triple in throughputs:
        X.append([triple[0], triple[1], triple[2]])
#        X.append([1. * triple[1] / triple[0], triple[2]])
#        y.append(throughputs[triple])
        y.append(beta(triple[0], triple[1], triple[2], throughputs[triple], alpha))

    est = SymbolicRegressor(population_size=5000,
                            generations=30,
                            function_set=('add', 'sub', 'mul', 'div', 'max'),
#                            metric='mse',
                            parsimony_coefficient=10,
                            verbose=1
                           )
    est.fit(X, y)
    print(est._program)
    return

def get_alpha():
    Cinf = max(points)
    Pinf = int(max(parallel_factors) * Cinf)
    Tinf = max(proc)
    THRinf = mean(parse(log_file(duration, Tinf, Cinf, Pinf, lock))["throughput"])
    return THRinf * (Cinf + Pinf) / Tinf

def queue(C, P, T):
    return max(T - 1. * P / C, 1)

def theoretical_throughput(C, P, T, alpha):
#    return alpha * T / (C * queue(C, P, T) + P + 300 * T)
    B = 380
    return alpha * T / ((C + B) * queue(C + B, P, T) + P)
#    return alpha * T / max(C + P, C * T + 436 * (T - 1))

# THR = (alpha T) / (C * Q(P, C, T) + P + T beta)
def beta(C, P, T, THR, alpha):                  
#    return ((alpha * T) / THR - C * queue(C, P, T) - P) / T
    beta1 = 1. * alpha / THR - 1. * C
    if P < (T - 1) * (C + beta1):
        return beta1
    return alpha * T / THR - C - P

def data(key):
    if not os.path.isdir("data/d{}/{}".format(duration, key)):
        os.makedirs("data/d{}/{}".format(duration, key))
    if key == "theoretical_throughput":
        alpha = get_alpha()
        print(alpha)

#        for triplet in throughputs:
#            print(str(triplet[0]) + " " + str(triplet[1]) + " " + str(triplet[2]) + " " + str(throughputs[triplet]))

        for triplet in throughputs:
            print(str(triplet) + " " + str(beta(triplet[0], triplet[1], triplet[2], throughputs[triplet], alpha)))
            print(str(triplet) + " " + str(throughputs[triplet]) + " " + str(theoretical_throughput(triplet[0], triplet[1], triplet[2], alpha)))
                                     
        for p in proc:
            for first in critical_points:
                out = open(data_file(duration, key, "critical", p, first, lock), 'w')

                for factor in parallel_factors:
                    critical = first
                    parallel = int(factor * first)
                    t = theoretical_throughput(critical, parallel, p, alpha)

                    out.write("{} {}\n".format(parallel, t))
                out.close()

            for first in parallel_points:
                out = open(data_file(duration, key, "parallel", p, first, lock), 'w')
                for factor in critical_factors:
                    critical = int(factor * first)
                    parallel = first
                    t = theoretical_throughput(critical, parallel, p, alpha)

                    out.write("{} {}\n".format(critical, t))

                out.close()
    else:
        for p in proc:
            for first in critical_points:
                out = open(data_file(duration, key, "critical", p, first, lock), 'w')
                for factor in parallel_factors:
                    critical = first
                    parallel = int(factor * first)
                    res = parse(log_file(duration, p, critical, parallel, lock))[key]
                    out.write("{} {}\n".format(parallel, mean(res)))
                out.close()

            for first in parallel_points:
                out = open(data_file(duration, key, "parallel", p, first, lock), 'w')
                for factor in critical_factors:
                    critical = int(factor * first)
                    parallel = first
                    res = parse(log_file(duration, p, critical, parallel, lock))[key]
                    out.write("{} {}\n".format(critical, mean(res)))
                out.close()
    return

lock = sys.argv[2]
src = src.format(lock)

if sys.argv[1] == "run":
    compile()
    run()
if sys.argv[1] == "data":
    all_throughputs()
    for i in range(3, len(sys.argv)):
        data(sys.argv[i])
if sys.argv[1] == "fit":
    all_throughputs()
    fit_throughput()

