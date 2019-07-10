'''
A preprocessing utility
'''

import sys
import os
import configparser

if __name__ == '__main__':
    if len(sys.argv) < 6:
        print(
            "usage: python3 preprocessing.py <graph_name> <edge_file> <sep[tab|comma|space]> <has_headers> <buffer_size> [node_file] [label_type]"
        )
        exit(-1)

    is_labelled = "false"

    if len(sys.argv) >= 7:
        is_labelled = "true"
        node_file = sys.argv[6]

    if len(sys.argv) >= 8:
        label_type = sys.argv[7]

    graph = sys.argv[1]
    edge_file = sys.argv[2]
    splitter = sys.argv[3]
    has_headers = sys.argv[4].lower()
    buffer = sys.argv[5]

    config = configparser.ConfigParser()
    config.read("conf/params.ini")
    workdir = config['DEFAULT']['workdir']
    num_machines = config['DEFAULT']['number_machines']
    num_workers = config['DEFAULT']['number_workers']

    cur_dir = os.getcwd()

    graph_loc = "%s/%s/DATA/%s.static" % (workdir, graph, graph)
    graph_prefix = "%s/%s/DATA/%s" % (workdir, graph, graph)

    part_prefix = "h%sw%s" % (num_machines, num_workers)
    tpart_prefix = part_prefix + "t"

    # Graph hash partition
    command = "python3 graph_part.py %s %s %s %s %s true %s" % (
        edge_file, graph, part_prefix, splitter, buffer, has_headers)

    if len(sys.argv) >= 7:
        command = "python3 graph_part.py %s %s %s %s %s true %s %s" % (
            edge_file, graph, part_prefix, splitter, buffer, has_headers, node_file)

    if len(sys.argv) >= 8:
        command = "python3 graph_part.py %s %s %s %s %s true %s %s %s" % (
            edge_file, graph, part_prefix, splitter, buffer, has_headers, node_file, label_type)

    print(command)
    os.system(command)
    print("")

    # Triangle partition
    command = "python3 tri_part.py %s %s %s" % (graph, part_prefix,
                                                tpart_prefix)

    print(command)
    os.system(command)
    print("")
