#include <iostream>
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <vector>
#include <time.h>
#include <sched.h>
#include <errno.h>
#include <string.h>
#include <map>
#include <unistd.h>
#include <math.h>
#include <sys/syscall.h>
#include <atomic>
#include <immintrin.h>
#include <vector>
#include <algorithm>
#include <fstream>
#include <chrono>

#include "cache_aligned_alloc.h"
#include "my_time.h"
#include "cmdline.hpp"

#include "platform_defs.h"
#include "atomic_ops.h"

#define NOP __asm__ __volatile__("")

unsigned long long now() {
    struct timespec t;
    clock_gettime(CLOCK_REALTIME, &t);
    return t.tv_sec * 1000000000LL + t.tv_nsec;
}

long long now_chrono() {
    auto now = std::chrono::system_clock::now();
    auto now_ms = std::chrono::time_point_cast<std::chrono::nanoseconds>(now);
    auto value = now_ms.time_since_epoch();
    return value.count();
}

struct cmd_line_args_t {
    unsigned time;
    unsigned threads_count;
    std::string pin_type;
    unsigned parallel_work;
    unsigned critical_work;
    std::string lock_type;
    bool arrival_time;
    unsigned iterations;
};

struct node {
    const int data;
    std::atomic<node *> next;

    explicit node(const int &data) : data(data), next(nullptr) {}
};

struct thread_data_t {
    unsigned tid;

    unsigned long iterations;

    std::atomic<bool> finish;
};

static void print_usage();
static void parse_cmd_line_args(cmd_line_args_t &args, int argc, char** argv);
static void* thread_fun(void* data);

void pin(pid_t t, int cpu);

unsigned (*pin_func) (unsigned );

static cmd_line_args_t args;

unsigned TIME;

std::vector<std::vector<long long>> arrivals;
std::atomic<node *> head;

int main(int argc, char **argv) {
    args.pin_type = "greedy";

    parse_cmd_line_args(args, argc, argv);

    thread_data_t** thread_data = (thread_data_t**) cache_size_aligned_alloc(
            sizeof(thread_data_t*) * args.threads_count);
    for (unsigned i = 0; i < args.threads_count; i++) {
        thread_data_t* td = (thread_data_t*) cache_size_aligned_alloc(sizeof(thread_data_t));

        td->tid = i;

        td->iterations = 0;

        td->finish = false;

        thread_data[i] = td;
    }

    if (args.arrival_time) {
        arrivals.assign(args.threads_count, std::vector<long long>(args.iterations));
    }

    pthread_t* threads = (pthread_t*) cache_size_aligned_alloc(sizeof(pthread_t) * args.threads_count);

    MEM_BARRIER;

    for (unsigned i = 0; i < args.threads_count; i++) {
        if (pthread_create(threads + i, NULL, thread_fun, (void*) thread_data[i])) {
            std::cerr << "Cannot create required threads. Exiting." << std::endl;
            exit(1);
        }
    }

    sleep_ms(TIME);

    for (unsigned i = 0; i < args.threads_count; i++) {
        thread_data[i]->finish.store(true, std::memory_order_relaxed);
    }

    for (unsigned i = 0; i < args.threads_count; i++) {
        pthread_join(threads[i], NULL);
    }

    MEM_BARRIER;

    unsigned long total_iterations = 0;

    for (int i = 0; i < args.threads_count; i++) {
        total_iterations += thread_data[i]->iterations;
    }

    std::cerr << total_iterations << " " << TIME << std::endl;

    printf("Throughput: %f op/sec\n", 1. * total_iterations / TIME);

    for (int i = 0; i < args.threads_count; i++) {
        cache_aligned_free(thread_data[i]);
    }

    cache_aligned_free(thread_data);
    cache_aligned_free(threads);

    return 0;
}

void pin(pid_t t, int cpu) {
    pthread_t thread;
    cpu_set_t cpuset;

    thread = pthread_self();

    CPU_ZERO(&cpuset);
    CPU_SET(cpu, &cpuset);

    if(pthread_setaffinity_np(thread, sizeof(cpuset), &cpuset) != 0) {
        printf("error setting affinity for %d %d\n", (int) t, (int) cpu);
    }

    int j, s;
    s = pthread_getaffinity_np(thread, sizeof(cpu_set_t), &cpuset);
    if (s != 0) {
        printf("error\n" );
    } else {
/*    printf("Set for %d:\n", t);
    for (j = 0; j < CPU_SETSIZE; j++)
      if (CPU_ISSET(j, &cpuset))
        printf("    CPU %d\n", j);*/
    }
}

static void parse_cmd_line_args(cmd_line_args_t &args, int argc, char **argv) {
    deepsea::cmdline::set(argc, argv);
    // set default

    args.threads_count = deepsea::cmdline::parse_or_default_int("proc", 1);
    args.time = deepsea::cmdline::parse_or_default_int("time", 1000);
    args.pin_type = deepsea::cmdline::parse_or_default_string("pin", "greedy");
    args.critical_work = deepsea::cmdline::parse_or_default_int("critical", 1000);
    args.parallel_work = deepsea::cmdline::parse_or_default_int("parallel", 1000);
    args.arrival_time = deepsea::cmdline::parse_or_default_bool("arrival", false);
    args.iterations = deepsea::cmdline::parse_or_default_int("iterations", 100000);

    // some argument checking, but not very extensive

    if(args.threads_count == 0) {
        std::cerr << "threads_count must be higher than 0" << std::endl;
        exit(0);
    }

    if(args.time <= 1) {
        std::cerr << "time must be higher than 1 millisecond" << std::endl;
        exit(0);
    }

    TIME = args.time;

    // print values
    std::cout << "Using parameters:\n" <<
              "\tthread count       = " << args.threads_count << "\n" <<
              "\ttime count         = " << args.time << "\n" <<
              "\tcritical           = " << args.critical_work << "\n" <<
              "\tparallel           = " << args.parallel_work << "\n";
}

unsigned greedy_pin(unsigned tid) {
    unsigned target = tid;

    return target;
}

unsigned socket_pin(unsigned tid) {
    unsigned cores = CORES_PER_SOCKET;
    unsigned target = (tid % cores) * NUMBER_OF_SOCKETS + tid / cores;

    return target;
}

static void* thread_fun(void* data) {
    thread_data_t* thread_data = (thread_data_t*) data;

    if (args.pin_type == "greedy") {
        pin(thread_data->tid, greedy_pin(thread_data->tid));
    } else if (args.pin_type == "socket") {
        pin(thread_data->tid, socket_pin(thread_data->tid));
    } else {
        printf( "wrong pin parameter!" );
        exit(0);
    }

    MEM_BARRIER;

    int P = args.parallel_work;
    int iterations = 0;
    int startup = now_chrono(); //now();

    while (args.arrival_time || !thread_data->finish.load(std::memory_order_relaxed)) {
        iterations++;
        if (args.arrival_time && iterations - 1 >= arrivals[thread_data->tid].size()) {
            break;
        }

        for (int i = 0; i < P; i++) {
            NOP;
        }
        if (args.arrival_time) {
            arrivals[thread_data->tid][iterations - 1] = now_chrono(); //now() - startup;
        }
        //don't keep in mind memory leaks and ABA problem, it's not necessary to measure our performance
        node *new_head = new node(5); //random int value
        node *old_head = head.load(std::memory_order_relaxed);//M
        do {
            new_head->next = old_head;//M
        } while (!head.compare_exchange_weak(old_head, new_head,
                                             std::memory_order_release,
                                             std::memory_order_acquire));//tries * W_i

    }

    thread_data->iterations = iterations;

    MEM_BARRIER;

    return NULL;
}
