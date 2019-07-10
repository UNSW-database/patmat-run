'''
Triangle partition utility
'''

import sys
import os
from subprocess import Popen

import configparser

from utils import sync_process, get_machine_list

if __name__ == "__main__":
    pool = list()
    if len(sys.argv) < 4:
        print("Usage: python tri_part.py <graph_name> <in_prefix> <out_prefix>")
        sys.exit(-1)
    graph = sys.argv[1]
    in_prefix = sys.argv[2]
    out_prefix = sys.argv[3]
    is_skew_res = "false"

    config = configparser.ConfigParser()
    config.read("conf/params.ini")
    workdir = config['DEFAULT']['workdir']
    num_machines = int(config['DEFAULT']['number_machines'])
    num_workers = int(config['DEFAULT']['number_workers'])

    print("Triangle Partition " + graph + " into " + out_prefix)

    cur_dir = os.getcwd()

    binPath = os.path.join(cur_dir, 'bin', 'tri_part')
    hostPath = os.path.join(cur_dir, 'conf', 'hosts')
    machines = get_machine_list(hostPath)

    if num_machines > len(machines):
        print("Specify too many <number_machines> in conf/params.ini."
              " Should be <= " + str(len(machines)))
        sys.exit(-1)

    logPath = os.path.join(cur_dir, 'logs', 'partition', graph)

    if not os.path.exists(logPath):
        os.makedirs(logPath)

    for i in range(num_machines):
        run_params = "/usr/bin/time -v {} {} {} {} {}  -n {} -w {} -p {} -h {}" \
            .format(binPath, workdir, graph, in_prefix, out_prefix,
                    num_machines, num_workers, i, hostPath)

        if is_skew_res == "true":
            run_params += ' -R'
            logfile_name = os.path.join(logPath, 'tri_part_r_%d.log' % i)
        else:
            logfile_name = os.path.join(logPath, 'tri_part_%d.log' % i)

        with open(logfile_name, "w") as logfile:
            command = ["ssh", machines[i], run_params]
            print(command)
            pool.append(Popen(
                command,
                stdout=logfile,
                stderr=logfile
            ))

    sync_process(pool)
