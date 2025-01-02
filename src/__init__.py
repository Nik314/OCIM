from OCIM.src.auxillary_methods import *
from OCIM.src.interaction_patterns import *
from OCIM.src.cut_definition import *
from OCIM.src.follows_relations import *
from OCIM.src.cut_detection import *
from OCIM.src.fall_throughs import *
import warnings
import numpy as np
warnings.filterwarnings("ignore", category=np.VisibleDeprecationWarning)
warnings.filterwarnings("ignore", category=pandas.errors.SettingWithCopyWarning)




def split_log(relation, partition):
    return [relation[relation["ocel:activity"].isin(part)] for part in partition]


def find_strict_cut(relation_frames, dfgs, clos, rel, div):

    print("Check Concurrent")
    concurrent = detect_concurrent_cut(relation_frames,dfgs,clos,rel,div)
    if concurrent:
        return (concurrent, is_concurrent_cut_valid)

    print("Check Exclusive")
    exclusive = detect_exclusive_cut(relation_frames, dfgs, clos, rel, div)
    if exclusive:
        return (exclusive, is_exclusive_cut_valid)

    print("Check Sequence")
    sequence = detect_sequence_cut(relation_frames, dfgs, clos, rel, div)
    if sequence:
        return (sequence, is_sequence_cut_valid)

    print("Check Loop")
    loop = detect_loop_cut(relation_frames, dfgs, clos, rel, div)
    if loop:
        return (loop, is_loop_cut_valid)

    return None

def object_centric_inductive_miner(relation_frames, div, rel):

    alphabet = list(set(sum([list(frame["ocel:activity"].unique()) for frame in relation_frames],[])))
    dfgs = get_cummulative_directly_follows_relation(relation_frames)
    clos = get_transitive_closure_follows_relation(relation_frames)

    if len(alphabet) == 1:
        return alphabet[0]

    result = find_strict_cut(relation_frames,dfgs,clos,rel,div)
    if result is None:
        result = detect_fallthrough_optimized(relation_frames,dfgs,clos,rel,div)

    print(result)
    print("##############################################################################")

    sublogs = split_log(relation_frames[0],result[0])
    subtrees = [object_centric_inductive_miner([log], div, rel) for log in sublogs]
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
    relations = pm4py.read_ocel("../OCIM/data/running-example.jsonocel").relations
    div, con, rel = get_interaction_patterns([relations])
    print("Start Miner")
    start = time.time()
    result = object_centric_inductive_miner([relations], div, rel)
    print_result(result)
    print(time.time()-start)




