import os
import sys
from math import sqrt
from statistics import mean, stdev
from gplearn.genetic import SymbolicRegressor

keys = ["throughput"]

src = "./locking_scheme.{}"
lock = "mcs"

duration = 10000
parallel_points = []  # 500, 1000, 5000, 10000, 50000, 100000]
critical_points =  [100,500, 1000, 5000,10000,15000] #[100, 500, 1000, 5000, 10000, 50000, 100000]
#parallel_factors = #[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27,
#28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49,
#50]  #
#[0.1,0.2,0.25,0.3,0.35,0.4,0.45,0.5,0.6,0.7,0.7,0.8,0.85,0.9,0.95,1,2,3,4,5]#6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]
parallel_factors = [0.1, 0.2, 0.25, 0.3, 0.4, 0.45, 0.5, 0.55, 0.6, 0.7, 0.8, 0.9, 1, 2,2.5, 3, 3.5, 4, 5, 5.5, 6, 6.5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,21, 22, 23, 24, 25, 30]#, 50, 80, 90, 100, 150, 180, 200, 400, 800, 1000, 1200, 1400, 1600, 1800, 2000]
critical_factors = []  # 1. / 80, 1. / 50, 1. / 30, 1. / 10, 1. / 4, 1. / 2, 1, 2, 4] #[5, 10, 15, 20, 25, 30]
proc = [5, 10, 15]  # [5, 10, 20, 30, 31]


def compile():
    command = "make {}".format(lock)
    print(command)
    os.system(command)

def log_file(duration, proc, critical, parallel, lock):
    return "out/log/d{}/{}_{}_{}_{}.txt".format(duration, proc, critical, parallel, lock)

def run_one(duration, proc, critical, parallel, lock):
    out = log_file(duration, proc, critical, parallel, lock)
    command = "{} -time {} -proc {} -critical {} -parallel {} -lock {} > {}".format(src, duration, proc, critical,
                                                                                    parallel, lock, out)
    print(command)
    os.system(command)


def run():
    if not os.path.isdir("out/log/d{}".format(duration)):
        os.makedirs("out/log/d{}".format(duration))

    for p in proc:
        for first in critical_points:
            for factor in parallel_factors:
                # change parallel first
                run_one(duration, p, first, int(factor * first), lock)

        for first in parallel_points:
            for factor in critical_factors:
                # change critical
                run_one(duration, p, int(factor * first), first, lock)


def exists(C, P, T, lock):
    return os.path.isfile(log_file(duration, T, C, P, lock))


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

                if not exists(critical, parallel, p, lock):
                    continue

                t = mean(parse(log_file(duration, p, critical, parallel, lock))["throughput"])
                throughputs[(critical, parallel, p)] = t

        for first in parallel_points:
            for factor in critical_factors:
                critical = int(factor * first)
                parallel = first

                if not exists(critical, parallel, p, lock):
                    continue

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
    Cinf = max(critical_points)
    Pinf = int(max(parallel_factors) * Cinf)
    Tinf = max(proc)
    print(Tinf, Cinf, Pinf);
    THRinf = mean(parse(log_file(duration, Tinf, Cinf, Pinf, lock))["throughput"])
    return THRinf * (Cinf + Pinf) / Tinf

def queue(C, P, T):
    return max(T - 1. * P / C, 1)

def get_W_and_R_and_X(alpha):
    filtered_throughputs = {}
    for setting in throughputs:
        if setting[0] != 500:
            continue
        filtered_throughputs[setting] = throughputs[setting]

    best = 1000000000000
    best_W = 0
    best_R = 0
    best_X = 0
    for W in range(0, 1000, 15):
        if W % 100 == 0:
            print("First loop " + str(W))
        for R in range(0, 1000, 15):
            if R % 100 == 0:
                print("Second loop " + str(R))
            for X in range(0, 1000, 15):
                error = 0
                for setting in filtered_throughputs:
                    real = throughputs[setting]
                    theory = theoretical_throughput_full_W_R_X(setting[0], setting[1], setting[2], alpha, W, R, X)
                    error += abs(real - theory) / real
                    if error > best:
                        break
                if error < best:
                    best = error
                    best_W = W
                    best_R = R
                    best_X = X
    print(best)
    return (best_W, best_R, best_X)


def get_W_and_M_and_X(alpha):
    filtered_throughputs = {}
    for setting in throughputs:
        if setting[0] != 500:
            continue
        filtered_throughputs[setting] = throughputs[setting]

    best = 1000000000000
    best_W = 0
    best_M = 0
    best_X = 0
    for W in range(0, 1000, 15):
        if W % 100 == 0:
            print("First loop " + str(W))
        for M in range(0, 1000, 15):
            if M % 100 == 0:
                print("Second loop " + str(M))
            for X in range(0, 1000, 15):
                error = 0
                for setting in filtered_throughputs:
                    real = throughputs[setting]
                    theory = theoretical_throughput_full_W_M_X(setting[0], setting[1], setting[2], alpha, W, M, X)
                    error += abs(real - theory) / real
                    if error > best:
                        break
                if error < best:
                    best = error
                    best_W = W
                    best_M = M
                    best_X = X
    print(best)
    return (best_W, best_M, best_X)


def get_M1_and_M2_and_X(alpha):
    filtered_throughputs = {}
    for setting in throughputs:
        if setting[0] != 500:
            continue
        filtered_throughputs[setting] = throughputs[setting]

    best = 1000000000000
    best_M1 = 0
    best_M2 = 0
    best_X = 0
    for M1 in range(0, 1000, 15):
        if M1 % 100 == 0:
            print("First loop " + str(M1))
        for M2 in range(0, 1000, 15):
            if M2 % 100 == 0:
                print("Second loop " + str(M2))
            for X in range(0, 1000, 15):
                error = 0
                for setting in filtered_throughputs:
                    real = throughputs[setting]
                    theory = theoretical_throughput_full(setting[0], setting[1], setting[2], alpha, M1, M2, X)
                    error += abs(real - theory) / real
                    if error > best:
                        break
                if error < best:
                    best = error
                    best_M1 = M1
                    best_M2 = M2
                    best_X = X
    print(best)
    return (best_M1, best_M2, best_X)

#W, M, X 15, 55, 70
def theoretical_throughput_full_W_M_X(C, P, T, alpha, W, M, X):
    if (T-1) * (M + W) > P:
        return alpha /(M + W)
    else:
        return alpha * T/(P+W+M)


def theoretical_throughput_full_W_R_X(C, P, T, alpha, W, R, X):
    Cc = C + 2 * W + R
    Pp = P + W
    if X > Cc:
        if (T - 1) * X > Pp + Cc:
            return alpha / X
        else:
            return alpha * T / (Pp + Cc + X)
    else:
        if (T - 1) * Cc > Pp + X:
            return alpha / (Cc + R + X)
        else:
            return alpha * T / (Pp + Cc + X)


def theoretical_throughput_full(C, P, T, alpha, M1, M2, X):
    Cc = C + M1
    Pp = P + M2
    if X > Cc:
        if (T - 1) * X > Pp + Cc:
            return alpha / X
        else:
            return alpha * T / (Pp + Cc + X)
    else:
        if (T - 1) * Cc > Pp + X:
            return alpha / Cc
        else:
            return alpha * T / (Pp + Cc + X)


def theoretical(C, P, T, alpha, W, R, X):
    return theoretical_throughput_full_W_R_X(C, P, T, alpha, W, R, X)


def theoretical_treiber(P, T, alpha, W, M, X):
    return theoretical_throughput_full_W_M_X(0, P, T, alpha, W, M, X)


def theoretical_throughput(C, P, T, alpha, M1, M2, X):
    return theoretical_throughput_full(C, P, T, alpha, 95, M2, X)  # 380 0 500


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

        (M1, M2, X) = get_W_and_R_and_X(alpha)
        print(str(M1) + " " + str(M2) + " " + str(X))

        for p in proc:
            for first in critical_points:
                dfile = data_file(duration, key, "critical", p, first, lock)
                out = open(dfile, 'w')

                for factor in parallel_factors:
                    critical = first
                    parallel = int(factor * first)

                    if not exists(critical, parallel, p, lock):
                        continue

                    t = theoretical(critical, parallel, p, alpha, M1, M2, X)

                    out.write("{} {}\n".format(parallel, t))
                out.close()

            for first in parallel_points:
                out = open(data_file(duration, key, "parallel", p, first, lock), 'w')
                for factor in critical_factors:
                    critical = int(factor * first)
                    parallel = first

                    if not exists(critical, parallel, p, lock):
                        continue

                    t = theoretical_throughput(critical, parallel, p, alpha)

                    out.write("{} {}\n".format(critical, t))

                out.close()
    else:
        # p and critical are fixed
        for p in proc:
            for first in critical_points:
                out = open(data_file(duration, key, "critical", p, first, lock), 'w')
                for factor in parallel_factors:
                    critical = first
                    parallel = int(factor * first)

                    if not exists(critical, parallel, p, lock):
                        continue

                    res = parse(log_file(duration, p, critical, parallel, lock))[key]
                    out.write("{} {}\n".format(parallel, mean(res)))
                out.close()

        # p and parallel are fixed
        for p in proc:
            for first in parallel_points:
                out = open(data_file(duration, key, "parallel", p, first, lock), 'w')
                for factor in critical_factors:
                    critical = int(factor * first)
                    parallel = first

                    if not exists(critical, parallel, p, lock):
                        continue

                    res = parse(log_file(duration, p, critical, parallel, lock))[key]
                    out.write("{} {}\n".format(critical, mean(res)))
                out.close()

        # critical and parallel are fixed
        for first in critical_points:
            for factor in parallel_factors:
                critical = first
                parallel = int(factor * first)
                out = open(data_file(duration, key, "processes", first, factor, lock), 'w')
                for p in proc:
                    if not exists(critical, parallel, p, lock):
                        continue

                    res = parse(log_file(duration, p, critical, parallel, lock))[key]
                    out.write("{} {}\n".format(p, mean(res)))
    return


def data_treiber(key):
    if not os.path.isdir("data/d{}/{}".format(duration, key)):
        os.makedirs("data/d{}/{}".format(duration, key))
    if key == "theoretical_throughput":
        alpha = get_alpha()
        print("Alpha: ", alpha)
        (W, M, X) = get_W_and_M_and_X(alpha)
        print("W, M, X: ", str(W) + " " + str(M) + " " + str(X))

        for p in proc:
            for first in critical_points:
                dfile = data_file(duration, key, "critical", p, first, lock)
                out = open(dfile, 'w')

                for factor in parallel_factors:
                    critical = first
                    parallel = int(factor * first)

                    if not exists(critical, parallel, p, lock):
                        continue

                    t = theoretical_treiber(parallel, p, alpha, W, M, X)

                    out.write("{} {}\n".format(parallel, t))
                out.close()

            for first in parallel_points:
                out = open(data_file(duration, key, "parallel", p, first, lock), 'w')
                for factor in critical_factors:
                    critical = int(factor * first)
                    parallel = first

                    if not exists(critical, parallel, p, lock):
                        continue

                    t = theoretical_treiber(parallel, p, alpha, W, M, X)

                    out.write("{} {}\n".format(critical, t))

                out.close()
    else:
        # p and critical are fixed
        for p in proc:
            for first in critical_points:
                out = open(data_file(duration, key, "critical", p, first, lock), 'w')
                for factor in parallel_factors:
                    critical = first
                    parallel = int(factor * first)

                    if not exists(critical, parallel, p, lock):
                        continue

                    res = parse(log_file(duration, p, critical, parallel, lock))[key]
                    out.write("{} {}\n".format(parallel, mean(res)))
                out.close()

        # p and parallel are fixed
        for p in proc:
            for first in parallel_points:
                out = open(data_file(duration, key, "parallel", p, first, lock), 'w')
                for factor in critical_factors:
                    critical = int(factor * first)
                    parallel = first

                    if not exists(critical, parallel, p, lock):
                        continue

                    res = parse(log_file(duration, p, critical, parallel, lock))[key]
                    out.write("{} {}\n".format(critical, mean(res)))
                out.close()

        # critical and parallel are fixed
        for first in critical_points:
            for factor in parallel_factors:
                critical = first
                parallel = int(factor * first)
                out = open(data_file(duration, key, "processes", first, factor, lock), 'w')
                for p in proc:
                    if not exists(critical, parallel, p, lock):
                        continue

                    res = parse(log_file(duration, p, critical, parallel, lock))[key]
                    out.write("{} {}\n".format(p, mean(res)))
    return


lock = sys.argv[2]
src = src.format(lock)

if sys.argv[1] == "run":
    compile()
    run()
if sys.argv[1] == "data":
    print("len of sys.argv: ", len(sys.argv))
    all_throughputs()
    for i in range(3, len(sys.argv)):
        print(sys.argv[i])
        if lock == "treiber":
            data_treiber(sys.argv[i])
        else:
            data(sys.argv[i])
if sys.argv[1] == "fit":
    all_throughputs()
    fit_throughput()