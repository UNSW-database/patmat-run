import sys
import os
from subprocess import Popen

'''This is to generate all algorithms' join plans of all queries, 
the algorithms include BinaryJoin, GenericJoin and MultiwayJoin'''

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print(
            "usage: python3 compute_all_plans.py <is_labelled> <is_symm_break> <is_compress> <is_tri_indexing> [batches]")
        exit(-1)
    is_labelled = sys.argv[1].lower()
    is_symm_break = sys.argv[2].lower()
    is_compress = sys.argv[3].lower()
    is_tri_indexing = sys.argv[4].lower()

    if len(sys.argv) >= 6:
        batches = sys.argv[5]
    else:
        batches = 128

    algorithms = ['BinaryJoin', 'GenericJoin']
    plan_bin = os.getcwd() + "/bin/compute_join_plan"

    plan_suffix = "plan.json"
    if is_tri_indexing == "false":
        plan_suffix = "notri_plan.json"

    for alg in algorithms:
        if is_labelled == "true":
            plan_dir = "plans/%s/labelled" % (alg)
            query_dir = "query_json/labelled"
        else:
            plan_dir = "plans/%s/unlabelled" % (alg)
            query_dir = "query_json/unlabelled"

        Popen(["mkdir", "-p", plan_dir]).wait()

        prefix = 'q'
        queries = range(1, 10)

        for i in queries:
            query = prefix + str(i)
            try:
                command = "%s %s %s/%s.json %s %s %s_%s --symmetry_break %s --batches %d --compress %s --trindex %s" % (
                    plan_bin, query, query_dir, query, alg, plan_dir, query, plan_suffix, is_symm_break, int(
                        batches),
                    is_compress,
                    is_tri_indexing)
                print(command)
                os.system(command)
            except:
                continue
