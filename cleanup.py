import subprocess
import sys
import os

import configparser

from utils import sync_process, get_machine_list

if __name__ == "__main__":
    pool = list()
    if len(sys.argv) < 2:
        print("Usage: python cleanup.py <bin>")
        sys.exit(-1)

    binName = sys.argv[1]
    print("Clean up " + binName)
    config = configparser.ConfigParser()
    config.read("conf/params.ini")
    workdir = config['DEFAULT']['workdir']
    hostPath = os.path.join(os.getcwd(), 'conf', 'hosts')
    num_machines = int(config['DEFAULT']['number_machines'])
    machines = get_machine_list(hostPath)

    if num_machines > len(machines):
        print("Specify too many number of machines")
        sys.exit(-1)

    for i in range(num_machines):
        command = ["ssh", machines[i], "pkill " + binName]
        print(command)
        pool.append(subprocess.Popen(command))

    sync_process(pool)

    for i in range(num_machines):
        command = ["ssh", machines[i], "rm -rf " + workdir + "/temp*"]
        print(command)
        pool.append(subprocess.Popen(command))

    sync_process(pool)
