import time
from asyncio import get_event_loop_policy

from src.auxillary_methods import *
from src.interaction_patterns import *
from src.cut_definition import *
from src.follows_relations import *
from src.cut_detection import *
from src.fallthrough_detection import *
from src.tau_cases import *
from src.oc_process_trees import *
from src.log_splitting import *
from src.common_data import *
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

        sizes = {ot:[log[log["ocel:type"] == ot].groupby("ocel:oid").apply(lambda frame: frame.shape[0]).max() > 1 for log in
         local_data.oc_log_list if log[log["ocel:type"] == ot].shape[0]] for ot in global_data.related[local_data.alphabet[0]] }
        loops = {ot for ot in global_data.related[local_data.alphabet[0]] if any(sizes[ot])}
        loops = {ot for ot in loops if any([ot in global_data.related[a] and ot not in global_data.divergence[a]
                            for a in local_data.alphabet])}
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


def apply(file_path, input_log = None):

    if input_log is None:
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



