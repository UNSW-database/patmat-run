# PatMat

## Prerequisities

* OS: Debian 6.0.10,  Ubuntu 18.04+ and CentOS 7.6 fully tested, other Linux releases should also work but not fully tested.
* Software: GLIBC_2.18 or higher version, Python 3 or higher version, openssh-server is correctly configured (check if `ssh localhost` works), time(/usr/bin/time) is installed.

## Configurations

The configuration folder is "conf", where there are three files to configure:

### params.ini

* workdir: The **absolute** directory of the working folder. It is the root directory of the data and temporary files. After configuring the workdir, your data should be placed at: $workdir/$graph_name/DATA/$prefix.
* number_workers: number of workers in each machine.
* number_machines: number of machines used in cluster.

### hosts

The host file used in Timely dataflow. Each line is in the form of:
       `host:port`, where host can be either host name or ip_addr, port can be any available port.

### graph_conf.json

* storage
  * $workdir: The **absolute** directory of the working folder. It is the root directory of the data and temporary files.
  * $persist_data: the graph dataset's name, which is put under the $workdir, and maintain as $workdir/$persist_data/DATA.
  * $temp_data: the temporary folder relative to $workdir, by default it is set as "temp".
* $is_directed: specify if the graph is directed or not.
* $label_type: the label type of graph, choose "Void" (no labels), "Simple" (unsigned int32), or "String". We use "Simple"
                      by default for labelled pattern matching.
* $graph_type: the graph storage type, "StaticGraph" (CSR format) or "GraphMap" (BTreeMap for structures). We use "StaticGraph"
                      by default.
* $prefix: the prefix of the file of the partitioned graph data.
* $tri_prefix: the prefix of the file of the triangle partitioned graph data..

## Data Storage & Preprocessing

The storage hierarchy used in the experiment looks like the following.

$workdir

---- $persist_data

-------- DATA

------------ $prefix

***
Note!!! In the experiment, we treat all data graphs as undirected graphs.
***

### One-stand preprocessing

We offer a tool to preprocess a raw graph file (in csv format) into the formatted graph used in the experiment.
Consider a graph stored as "dir/to/sample.csv", in which each line is in the form of

`src_id<separator>dst_id[<separator>edge_label]`

where the label part is optional, depending on whether it is a labelled graph or not. If it is a labelled graph, you should further provide a node label file, suppose is "/dir/to/sample_nl.csv",
and each line is in the form of:

`node_id<separator>node_label`  —— separator should be the same as the edge file.

Then you call the following for preprocessing:

`python3 preprocessing.py <graph_name> <edge_file> <sep[tab|comma|space]> <has_headers> <buffer_size> [node_file]`

where the <edge_file> and [node_file] should be the **absolute file path**, \<sep> specifies the separator in csv files(we support tab, comma or space separators), <has_headers> specifies if there exist headers in csv files, <buffer_size> is the number of lines to read from csv files each time.

For example, we can parse the unlabelled sample graph data in "csv/unlabelled/" via

`python3 preprocessing.py sampleUnlabelled /your-current-dir/csv/unlabelled/sample.csv comma false 100`

or we can parse the labelled sample graph data in "csv/labelled/" via

`python3 preprocessing.py sampleLabelled /your-current-dir/csv/labelled/edges.csv comma true 100 /your-current-dir/csv/labelled/nodes.csv`

***
Note!!! The above <graph_name> is specified by yourself, but it should be consistent in the following.
***

This will generate the following files under the folder: "$workdir/<graph_name>/DATA":
h1w3                          -- The hash partitions of the formatted static graph.
h1w3t                         -- The triangle partitions of the formatted static graph.

***
Note!!! The partition's prefix name is according to the $number_machines and $number_workers you
specified in "conf/params.ini"
***

Optional: If it is a labelled graph, there will be some label-related metadata.

### Detailed preprocessing steps

If you are interested in detailed preprocessing, please read this part. Otherwise, go to [Join Plans].

There are two steps of preprocessing, graph_part and tri_part, introduced as follows.

#### graph_part

After the preprocessing, we can call hash graph partition utility as:
`python3 graph_part.py <edge_file> <graph_name> <part_prefix> <sep> <buffer_size> <reorder> <has_headers> [node_file] [label_type]`

where the \<reorder> specifies if we reorder the node ids by their degree, we set this option by default to be true in our experiments, and the <part_prefix> can be specified with any easy-remembered name. We tend to use
h[$number_machines]w[$number_workers] as the $part_prefix.

For example, if you have 10 machines, and each runs 3 workers, and you specify $part_prefix as h10w3.
After <graph_part>, you should see that there are 10 partitions, each named h10w3 in the corresponding folders in each machine, that will be jointly accessed by all three workers in that machine.

#### tri_part

CliqueJoin(BinaryJoin using triangle indexing) relies on triangle partition, and <tri_part> does the job via:
`python3 tri_part.py <graph_name> <in_prefix> <out_prefix>`

Here, "h10w3" is the <in_prefix> you specified in `graph_part`, now there is an <out_prefix> and you should
set it differently from $prefix. For example, "h10w3t".

After <tri_part>, you should see that there are 10 partitions, each named h10w3t in the corresponding folders in each machine.

***
Note!!! In order to minimize memory usage, triangles will temporarily be stored on the disk under you "workdir/" before being merged into the triangle partition. It's safe to delete directories with names "temp.*" if the program exits unexpectedly.
***

## Join Plans

We offer the BinaryJoin and GenericJoin plans for all queries under `plans/` directory(generated by
compute_all_plans.py). You can generate all plans by calling:

`python3 compute_all_plans.py <is_labelled> <is_symm_break> <is_compress> <is_tri_indexing> [batches]`

where the <is_symm_break> specifies if the plan generates symmetry breaking (to assign partial order for query nodes), the <is_compress> specifies if the plan generates compression config, the <is_tri_indexing> specified if we want to generate join plans supporting triangle indexing (which is strongly recommended), and the [batches] specifies the batch size in each join.

We have already generated all join plans in `plans/BinaryJoin/` folder, they all support triangle indexing, compression and batching.

***
Note!!! Even you can generate plans with all optimizations: triangle indexing, compression and batching,
you can still configure whether to use them when running pattern matching in `patmat.py`.
***

We provide the query's json files in "query_json" folder. For the labelled queries, as we are using
label id instead of actual label in the data graph, we include a label_id map in "query_json/labelled".

The query's json file is quite straightforward, where you just need to specify nodes and edges. Please refer to the json files in "query_json" folder, take `query_json/labelled/q1.json` for example, we give some comments as follows:

```json
{
    "is_directed": false,
    "is_labelled": true,
    "vertices": [
        [0, 3], // node 0, label 3
        [1, 10],
        [2, 9]
    ],
    "edges": [
        [0, 1, null], // edge (0, 1), no label
        [1, 2, null]
    ],
    // currently you just set `partial_order` as null, you can generate it in join plan
    "partial_order": null
}
```

If you want to run other queries, you can generate the plan using the utilities we provided:
`bin/compute_join_plan <query_name> <query_file_path> <Algorithm[BinaryJoin|GenericJoin]> <output_dir>
<output_file> --is_compress <true|false> --trindex <true|false> --batches [batches]`

where $trindex specifies if we use triangle indexing(Again, we strongly recommend you to use triangle indexing to accelerate pattern matching). If [batches] is not specified, we set it to 128 by default. Note that even the batch size is set, you can always choose whether to use batching while running patmat.py.

We generate unlabelled query q8's BinaryJoin plan as an example. Note that the q8 can be replaced as any
query you want.

```bash
bin/compute_join_plan q8 query_json/unlabelled/q8.json BinaryJoin plans/BinaryJoin/unlabelled/ q8_plan.json
--batches 128 --compress true --trindex true
```

## Run the algorithms

After preparing everything above, it is easy to run the algorithms by calling:
`python3 patmat.py <algorithm> <query_name> <is_labelled> <plan_path> <graph_conf_path> <tri_index[true|false]> <is_compress[true|false]> [batches]`

Note that we only provide BinaryJoin and GenericJoin algorithms in the scripts. The others will be released
as source codes.

<plan_path> and <graph_conf_path> are provided in the form of relative path to current directory.

***
Note!!! Pay attention to $number_machines and $number_workers you specify in "conf/params.ini", you should use:
h[$number_machines]w[$number_workers] and h[$number_machines]w[$number_workers]t.

Also, the plan must be consistent with $trindex: if you set $trindex as true, you must use the plan generated
with $trindex as true. Further, if you do not specify $batches here, even it is configured in the join plan,
no batching will be applied.
***

Below we show the whole configurations of running our sample examples.
***
Note!!! Please change the following $workdir to your configured $workdir.
***

conf/hosts

```text
localhost:18888
```

conf/params.ini

```ini
[DEFAULT]
workdir=/your/dir/to/workdir
number_workers=3
number_machines=1
```

conf/graph_conf.json

```json
{
  "storage":{
    "workdir": "/your/dir/to/workdir",
    "persist_data": "sampleUnlabelled",
    "temp_data": "temp"
  },
  "is_directed": false,
  "label_type": "Simple",
  "graph_type": "StaticGraph",
  "prefix":"h1w3",
  "tri_prefix":"h1w3t"
}
```

If you want to run unlabelled query q5 using BinaryJoin algorithm with triangle indexing, compression and batching (for example, set batches to 128), just call:
`python3 patmat.py BinaryJoin q5 false plans/BinaryJoin/unlabelled/q5_plan.json conf/graph_conf.json true true 128`

The result of unlabelled q5 in unlabelled sample graph (data/sampleUnlabelled) should be 32679.

### Sample Graph Ground Truth

Unlabelled Sample Graph Ground Truth with symmetry breaking(we put it under data/sampleUnlabeleld):

|   q1   |   q2   |   q3   |   q4   |   q5   |   q6   |    q7    |   q8   |   q9   |
|--------|--------|--------|--------|--------|--------|----------|--------|--------|
|  7191  |  3975  |   170  | 121809 |  32679 |  4080  |  1353345 | 252699 | 126805 |

Labelled Sample Graph Ground Truth without symmetry breaking(we put it under data/sampleLabelled):

|   q1   |   q2   |   q3   |   q4   |    q5    |   q6   |   q7  |   q8   |   q9   |
|--------|--------|--------|--------|----------|--------|-------|--------|--------|
|  34445 |  40850 |  24632 |  22557 |  1789718 |  1076  |   6   |   16   |  2670  |

The queries (unlabelled and labelled) are listed according to our VLDB paper.

### Logs

All logs can be found in logs folder, with "logs/<algorithm>" and "logs/partition" indicate the algorithm running logs and partition logs respectively.

## Publications

* Longbin Lai et al., Distributed Subgraph Matching on Timely Dataflow. [VLDB 2019](http://www.vldb.org/pvldb/vol12/p1099-lai.pdf).
* Longbin Lai et al., A Survey and Experimental Analysis of Distributed Subgraph Matching in [arxiv](https://arxiv.org/abs/1906.11518). p.s. A full version of the VLDB submission

## Contributors

* "Longbin Lai <longbin.lai@gmail.com>",
* "Zhengyi Yang <yangzhengyi188@gmail.com>",
* "Zhu Qing <skullpirate.qing@gmail.com>",
* "Xin Jin <xinj.cs@gmail.com>",
* "Zhengmin Lai <zhengmin.lai@gmail.com>",
* "Ran Wang <wangranSEI@gmail.com>",
* "KongZhang Hao <haokongzhang@gmail.com>",

## Issues

Please send to <longbin.lai@gmail.com> for any further questions.
