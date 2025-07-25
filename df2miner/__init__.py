import pm4py
import time
import pandas
import warnings
warnings.simplefilter(action="ignore", category=pandas.errors.SettingWithCopyWarning)
from df2miner.interaction_properties import get_interaction_patterns
from df2miner.divergence_free_graph import get_divergence_free_graph
from src.oc_process_trees import OperatorNode,LeafNode
from df2miner.identity_relations import get_extended_ocpt


def load_from_pt(process_tree, related, divergence, convergence, deficiency):

    if process_tree.children:
        return OperatorNode(process_tree.operator, [load_from_pt(sub,related,divergence,convergence,deficiency) for sub in process_tree.children])
    elif process_tree.label:
        activity = process_tree.label
        return LeafNode(activity,related[activity],divergence[activity],convergence[activity],deficiency[activity])
    else:
        all_types = set(sum([list(v) for v in related.values()],[]))
        return LeafNode("",all_types,all_types,all_types,all_types)


def df2_miner_apply(log_path):

    try:
        input_log = pm4py.read_ocel2(log_path).relations
    except:
        input_log = pm4py.read_ocel(log_path).relations

    div, con, rel, defi = get_interaction_patterns(input_log)
    print("Interacting Properties Done")
    df2_graph = get_divergence_free_graph(input_log,div,rel)
    print("DF2 Graph Done")
    process_tree = pm4py.discover_process_tree_inductive(df2_graph, noise_threshold=0.2)
    print("Traditional Process Tree Done")
    ocpt = load_from_pt(process_tree,rel,div,con,defi)
    return ocpt






