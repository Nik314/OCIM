from OCIM.src.auxillary_methods import *
from OCIM.src.interaction_patterns import *
from OCIM.src.cut_definition import *
from OCIM.src.follows_relations import *
from OCIM.src.cut_detection import *
from OCIM.src.fallthrough_detection import *
from OCIM.src.tau_cases import *
from OCIM.src.oc_process_trees import *
from OCIM.src.log_splitting import *
from OCIM.src.common_data import *

import warnings
import numpy as np
warnings.filterwarnings("ignore", category=np.VisibleDeprecationWarning)
warnings.filterwarnings("ignore", category=pandas.errors.SettingWithCopyWarning)



def object_centric_inductive_miner(local_data, global_data, brute_force = False, noise = False):

    partition, operator = detect_tau_cases(local_data,global_data)
    if operator:
        print(partition, operator)
        print("##############################################################################")

        sublogs = split_log(local_data, partition,operator)
        subtrees = [object_centric_inductive_miner(sublogs[0], global_data, brute_force, noise),
            LeafNode("tau",local_data.object_types,set(),set(),local_data.object_types)]
        return OperatorNode(operator, subtrees)

    if len(local_data.alphabet) == 1:
        return LeafNode(local_data.alphabet[0],global_data.related[local_data.alphabet[0]],
            global_data.divergence[local_data.alphabet[0]],global_data.convergence[local_data.alphabet[0]],
                        global_data.deficiency[local_data.alphabet[0]])

    partition, operator = find_strict_cut(local_data, global_data)
    if operator is None:
        if not brute_force:
            partition, operator = detect_fallthrough_fitness_polynomial(local_data,global_data)
        else:
            partition, operator = detect_fallthrough_fitness_brute_force(local_data,global_data)

    print(partition,operator)
    print("##############################################################################")

    sublogs = split_log(local_data,partition,operator)
    subtrees = [object_centric_inductive_miner(split_local_data, global_data,brute_force,noise) for split_local_data in sublogs]
    return OperatorNode(operator, subtrees)



def apply(file_path):
    input_log = pm4py.read_ocel(file_path).relations
    global_data = GlobalData([input_log])
    local_data = LocalData([input_log])
    return object_centric_inductive_miner(local_data, global_data)





if __name__ == "__main__":
    apply("../data/running-example.jsonocel")



