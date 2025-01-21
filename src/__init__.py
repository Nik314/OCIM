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



def object_centric_inductive_miner(local_data, global_data):

    result = find_strict_cut(local_data, global_data)
    if result is None:
        result = detect_fallthrough_fitness_polynomial(local_data,global_data)

    print(result)
    print("##############################################################################")

    sublogs = split_log(oc_log_list[0],result[0])
    subtrees = [object_centric_inductive_miner([log], div, rel, object_set) for log in sublogs]
    return (str(result[1]), subtrees)



def apply(file_path):
    input_log = pm4py.read_ocel(file_path).relations
    global_data = GlobalData([input_log])
    local_data = LocalData([input_log])
    return object_centric_inductive_miner(local_data, global_data)





if __name__ == "__main__":
    apply("../data/running-example.jsonocel")



