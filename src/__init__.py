from OCIM.src.auxillary_methods import *
from OCIM.src.interaction_patterns import *
from OCIM.src.cut_definition import *
from OCIM.src.follows_relations import *
from OCIM.src.cut_detection import *
from OCIM.src.fallthrough_detection import *
from OCIM.src.tau_cases import *
from OCIM.src.oc_process_trees import *
import warnings
import numpy as np
warnings.filterwarnings("ignore", category=np.VisibleDeprecationWarning)
warnings.filterwarnings("ignore", category=pandas.errors.SettingWithCopyWarning)




def split_log(relation, partition):
    return [relation[relation["ocel:activity"].isin(part)] for part in partition]



def object_centric_inductive_miner(oc_log_list, div, rel, object_set):

    alphabet = list(set(sum([list(log["ocel:activity"].unique()) for log in oc_log_list],[])))
    dfgs = get_cummulative_directly_follows_relation(oc_log_list)
    clos = get_transitive_closure_follows_relation(oc_log_list)

    if len(alphabet) == 1:
        return alphabet[0]

    result = find_strict_cut(oc_log_list,dfgs,clos,rel,div)
    if result is None:
        result = detect_fallthrough_fitness_polynomial(oc_log_list,dfgs,clos,rel,div)

    print(result)
    print("##############################################################################")

    sublogs = split_log(oc_log_list[0],result[0])
    subtrees = [object_centric_inductive_miner([log], div, rel, object_set) for log in sublogs]
    return (str(result[1]), subtrees)




def print_result(result, depth = 0):

    indent = ""
    for i in range(0,depth):
        indent += "\t"

    if isinstance(result,tuple):

        print(indent + result[0].split(" ")[1].split("_")[1] + "\n")
        for entry in result[1]:
            print_result(entry, depth+1)

    else:
        print(indent + result + "\n")



if __name__ == "__main__":
    import time
    print("Start Miner")
    start = time.time()
    relations = pm4py.read_ocel("../data/p2p.jsonocel").relations
    div, con, rel = get_interaction_patterns([relations])
    result = object_centric_inductive_miner([relations], div, rel, relations["ocel:oid"].unique())
    print_result(result)
    print(time.time()-start)




