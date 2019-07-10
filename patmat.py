import sys
import os
import time
from subprocess import Popen

import configparser

from utils import get_machine_list, sync_process


def terminate_when_one_end(pool):
    while True:
        time.sleep(5)
        for _p in pool:
            if _p.poll() != None:
                del pool[:]
                return
    return


if __name__ == "__main__":
    if len(sys.argv) < 8:
        print(
            "Usage: python3 patmat.py <algorithm> <query_name> <is_labelled> <plan_path> <graph_conf_path> <tri_index> <is_compress> [batches]")
        sys.exit(-1)

    algorithm = sys.argv[1]
    qname = sys.argv[2]
    is_labelled = sys.argv[3].lower()
    query_plan_path = sys.argv[4]
    data_config_path = sys.argv[5]
    tri_index = sys.argv[6].lower()
    is_compress = sys.argv[7].lower()

    if len(sys.argv) == 9:
        batches = sys.argv[8]
    else:
        batches = 18446744073709551615

    config = configparser.ConfigParser()
    config.read("conf/params.ini")
    workdir = config['DEFAULT']['workdir']
    num_machines = int(config['DEFAULT']['number_machines'])
    num_workers = int(config['DEFAULT']['number_workers'])

    cur_dir = os.getcwd()
    binDir = os.path.join(cur_dir, 'bin')
    hostPath = os.path.join(cur_dir, 'conf', 'hosts')
    query_plan_path = os.path.join(cur_dir, query_plan_path)
    data_config_path = os.path.join(cur_dir, data_config_path)
    machines = get_machine_list(hostPath)

    if num_machines > len(machines):
        print("Specify too many <number_machines> in conf/params.ini."
              " Should be <= " + str(len(machines)))
        sys.exit(-1)

    binPath = os.path.join(binDir, "patmat")

    if is_labelled == "true":
        log_path = "logs/%s/labelled/%s" % (algorithm, qname)
    else:
        log_path = "logs/%s/unlabelled/%s" % (algorithm, qname)

    Popen(["python3", "cleanup.py", "patmat"]).wait()
    Popen(["mkdir", "-p", log_path]).wait()

    pool = list()

    for _i in range(num_machines):
        logfile_name = log_path + "/%02d_out" % _i
        logfile = open(logfile_name, "w")

        run_params = "/usr/bin/time -v timeout 3h %s %s %s %s -w %d -n %d -h %s -p %d --trindex %s --batches %d --compress %s" \
                     % (
                         binPath, query_plan_path, data_config_path, algorithm, num_workers,
                         num_machines,
                         hostPath, _i, tri_index, int(batches), is_compress)

        command = ["ssh", machines[_i], run_params]

        print(command)
        pool.append(Popen(command, stdout=logfile, stderr=logfile))

        logfile.close()

    terminate_when_one_end(pool)
