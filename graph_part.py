'''
A graph partition utility
'''

import sys
import os
from subprocess import Popen

import configparser

from utils import sync_process, get_machine_list

if __name__ == "__main__":
    pool = list()
    if len(sys.argv) < 8:
        print(
            "Usage: python3 graph_part.py <edge_file> <graph_name> <part_prefix> <sep> <buffer_size> <reorder> <has_headers> [node_file] [label_type]")
        sys.exit(-1)
    edge_file = sys.argv[1]
    graph = sys.argv[2]
    prefix = sys.argv[3]
    sep = sys.argv[4]
    buffer = sys.argv[5]
    reorder = sys.argv[6].lower()
    has_headers = sys.argv[7].lower()

    cur_dir = os.getcwd()

    if len(sys.argv) >= 9:
        node_file = sys.argv[8]

    label_type = "Simple"
    if len(sys.argv) >= 10:
        label_type = sys.argv[9]

    config = configparser.ConfigParser()
    config.read("conf/params.ini")
    workdir = config['DEFAULT']['workdir']
    num_machines = int(config['DEFAULT']['number_machines'])
    num_workers = int(config['DEFAULT']['number_workers'])

    print("Partition " + graph + " into " + prefix)

    binPath = os.path.join(cur_dir, 'bin', 'graph_part')
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
        run_params = "/usr/bin/time -v {} {} {} {} {} --sep {} -b {} -t {} -n {} -w {} -p {} -h {}" \
            .format(binPath, edge_file, workdir, graph, prefix, sep, buffer, label_type, num_machines, num_workers, i,
                    hostPath)

        if len(sys.argv) >= 9:
            run_params = "/usr/bin/time -v {} {} {} {} {} --sep {} --node {} -b {} -t {} -n {} -w {} -p {} -h {}" \
                .format(binPath, edge_file, workdir, graph, prefix, sep, node_file, buffer, label_type, num_machines, num_workers,
                        i, hostPath)

        if reorder == "true":
            run_params += ' -r'
        if has_headers == "true":
            run_params += ' --headers'

        logfile_name = os.path.join(logPath, 'graph_part_%d.log' % i)

        with open(logfile_name, "w") as logfile:
            command = ["ssh", machines[i], run_params]
            print(command)
            pool.append(Popen(
                command,
                stdout=logfile,
                stderr=logfile
            ))

    sync_process(pool)
