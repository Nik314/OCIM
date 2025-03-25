import time

from sympy.assumptions import global_assumptions

from auxillary_methods import *
from interaction_patterns import *
from cut_definition import *
from follows_relations import *
from cut_detection import *
from fallthrough_detection import *
from tau_cases import *
from oc_process_trees import *
from log_splitting import *
from common_data import *

import warnings
warnings.filterwarnings("ignore", category=pandas.errors.SettingWithCopyWarning)
warnings.filterwarnings("ignore",category=DeprecationWarning)


def object_centric_inductive_miner(local_data, global_data, brute_force = False, noise = False):

    start = time.time()
    partition, operator = detect_tau_cases(local_data,global_data)
    global_data.runtime_info["taus"].append(time.time()-start)

    if operator:
        start = time.time()
        sublogs = split_log(local_data, partition,operator,global_data)
        global_data.runtime_info["splits"].append(time.time()-start)

        subtrees = [object_centric_inductive_miner(sublogs[0], global_data, brute_force, noise),
            LeafNode("",local_data.object_types,local_data.object_types,local_data.object_types,local_data.object_types)]
        return OperatorNode(operator, subtrees)

    if len(local_data.alphabet) == 1:
        total = pandas.concat(local_data.oc_log_list)
        info = {ot:total[total["ocel:type"] == ot].groupby("ocel:oid").apply(lambda frame:frame["ocel:eid"].nunique()).max() for ot in global_data.related[local_data.alphabet[0]]}
        loops = {ot for ot in info.keys() if info[ot] > 1}

        if loops:
            return OperatorNode(Operator.LOOP,subtrees=[LeafNode(local_data.alphabet[0], global_data.related[local_data.alphabet[0]],
                            (global_data.divergence[local_data.alphabet[0]]),
                            global_data.convergence[local_data.alphabet[0]],
                            global_data.deficiency[local_data.alphabet[0]]),
            LeafNode("",local_data.object_types,local_data.object_types,local_data.object_types,local_data.object_types)])
        else:
            return LeafNode(local_data.alphabet[0],global_data.related[local_data.alphabet[0]],
            (global_data.divergence[local_data.alphabet[0]]),global_data.convergence[local_data.alphabet[0]],
                        global_data.deficiency[local_data.alphabet[0]])

    start = time.time()
    partition, operator = find_strict_cut(local_data, global_data)
    global_data.runtime_info["cuts"].append(time.time()-start)

    if operator is None:
        start = time.time()
        if not brute_force:
            partition, operator = detect_fallthrough_fitness_polynomial(local_data,global_data)
        else:
            partition, operator = detect_fallthrough_fitness_brute_force(local_data,global_data)
        global_data.runtime_info["fallthroughs"].append(time.time()-start)

    start = time.time()
    sublogs = split_log(local_data,partition,operator,global_data)
    global_data.runtime_info["splits"].append(time.time() - start)
    subtrees = [object_centric_inductive_miner(split_local_data, global_data,brute_force,noise) for split_local_data in sublogs]

    return OperatorNode(operator, subtrees)




def apply(file_path):
    input_log = pm4py.read_ocel2(file_path).relations
    global_data = GlobalData([input_log])
    local_data = LocalData([input_log])
    return object_centric_inductive_miner(local_data, global_data),global_data.runtime_info, global_data.quality_info



if __name__ == "__main__":

    from evaluation_util import *
    determine_runtime_demands("../data","../logs", "../ocpns","../ocpts", apply)





