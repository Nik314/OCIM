import time

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
import random
import warnings
warnings.filterwarnings("ignore", category=pandas.errors.SettingWithCopyWarning)
warnings.filterwarnings("ignore",category=DeprecationWarning)
random.seed = 367450


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

        info = [{ot:log[log["ocel:type"] == ot].groupby("ocel:oid").apply(lambda frame:frame["ocel:eid"].nunique()).max() for ot in global_data.related[local_data.alphabet[0]]} for log in local_data.oc_log_list]
        loops = {ot for ot in global_data.related[local_data.alphabet[0]] if any([sub[ot] > 1 for sub in info if isinstance(sub, numpy.int64)] + [False]) and ot not in global_data.divergence[local_data.alphabet[0]]}

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
    try:
        input_log = pm4py.read_ocel2(file_path).relations
    except:
        input_log = pm4py.read_ocel(file_path).relations

    start = time.time()
    global_data = GlobalData([input_log])
    local_data = LocalData([input_log])
    result = object_centric_inductive_miner(local_data, global_data),global_data.runtime_info, global_data.quality_info
    global_data.runtime_info["total"] = time.time() -start
    return result



if __name__ == "__main__":

    from evaluation_util import *
    experiment_3("../data","../logs", "../ocpts", apply)
    #plot_experiment_1()
    #plot_experiment_2()
    #experiment_1_and_2("../data", apply)




