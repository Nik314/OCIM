import numpy
from conformance.log_abstraction import get_log_abstraction
from conformance.tree_abstraction import get_tree_abstraction,dfg_recursion
import pm4py

def determine_conformance(ocpt, file_path,timeout):
    try:
        input_log = pm4py.read_ocel2(file_path).relations
    except:
        input_log = pm4py.read_ocel(file_path).relations

    log_abstraction = get_log_abstraction(input_log)
    tree_abstraction = get_tree_abstraction(ocpt)
    fitness = get_fitness(log_abstraction,tree_abstraction)
    precision = get_precision(log_abstraction,tree_abstraction)
    return fitness, precision

def determine_conformance_pt_collection(pts,file_path):
    try:
        input_log = pm4py.read_ocel2(file_path).relations
    except:
        input_log = pm4py.read_ocel(file_path).relations

    log_abstraction = get_log_abstraction(input_log)
    dfgs = {key:dfg_recursion(pt)[:3] for key,pt in pts.items()}
    rel,div,con,defi,opt = log_abstraction[1:]
    defi = {a:set() for a in rel.keys()}
    div = {a:set([ot for ot in dfgs.keys() if (a,a) in dfgs[ot][0].keys()]) for a in rel.keys()}
    tree_abstraction = dfgs,rel,div,con,defi,opt
    fitness = get_fitness(log_abstraction,tree_abstraction)
    precision = get_precision(log_abstraction,tree_abstraction)
    return fitness, precision





def get_fitness(log_abstraction, tree_abstraction):

    log_dfgs,log_rel,log_div,log_con,log_defi,log_opt = log_abstraction
    tree_dfgs,tree_rel,tree_div,tree_con,tree_defi,tree_opt = tree_abstraction
    total_activities = list(log_rel.keys()) + list(tree_rel.keys())

    log_start = {a:[ot for ot,(dfg,start,end) in log_dfgs.items() if a in start] for a in total_activities}
    log_end = {a:[ot for ot,(dfg,start,end) in log_dfgs.items() if a in end] for a in total_activities}
    log_dfgs = {key:value[0] for key,value in log_dfgs.items()}

    tree_start = {a:[ot for ot,(dfg,start,end) in tree_dfgs.items() if a in start] for a in total_activities}
    tree_end = {a:[ot for ot,(dfg,start,end) in tree_dfgs.items() if a in end] for a in total_activities}
    tree_dfgs = {key:value[0] for key,value in tree_dfgs.items()}

    activity_fitness = []
    for a in log_rel.keys():
        if a not in tree_rel.keys():
            print("Missing Activity In Tree ",a)
            activity_fitness.append(0)
        else:
            sub_fitness = []
            for log_pat,tree_pat in [(log_rel,tree_rel),(log_div,tree_div),(log_con,tree_con),(log_defi,tree_defi),(log_opt,tree_opt),
                        (log_start,tree_start),(log_end,tree_end)]:
                if not len(log_pat[a]):
                    continue
                else:
                    sub_fitness.append(len(set(log_pat[a]) & set(tree_pat[a])) / len(set(log_pat[a])))
                    if sub_fitness[-1] != 1.0:
                        print("Pattern Missmatch For Activity ",a)
                        print([(log_rel, tree_rel), (log_div, tree_div), (log_con, tree_con), (log_defi, tree_defi),
                             (log_opt, tree_opt),(log_start, tree_start), (log_end, tree_end)].index((log_pat,tree_pat)))
                        print(log_pat[a])
                        print(tree_pat[a])
            activity_fitness.append(numpy.mean(sub_fitness))

    relation_fitness = []
    for a in log_rel.keys():
        for b in log_rel.keys():
            log_part = {ot for ot in log_dfgs.keys() if (a,b) in log_dfgs[ot]}
            if not log_part:
                continue
            else:
                tree_part = {ot for ot in tree_dfgs.keys() if (a,b) in tree_dfgs[ot]}
                relation_fitness.append(len(log_part&tree_part) / len(log_part))
                if relation_fitness[-1] != 1.0:
                    print("Relation Missmatch For  ", a,b)
                    print(log_part)
                    print(tree_part)
    return numpy.mean([numpy.mean(activity_fitness), numpy.mean(relation_fitness)])






def get_precision(log_abstraction, tree_abstraction):

    log_dfgs,log_rel,log_div,log_con,log_defi,log_opt = log_abstraction
    tree_dfgs,tree_rel,tree_div,tree_con,tree_defi,tree_opt = tree_abstraction
    total_activities = list(log_rel.keys()) + list(tree_rel.keys())

    log_start = {a:[ot for ot,(dfg,start,end) in log_dfgs.items() if a in start] for a in total_activities}
    log_end = {a:[ot for ot,(dfg,start,end) in log_dfgs.items() if a in end] for a in total_activities}
    log_dfgs = {key:value[0] for key,value in log_dfgs.items()}

    tree_start = {a:[ot for ot,(dfg,start,end) in tree_dfgs.items() if a in start] for a in total_activities}
    tree_end = {a:[ot for ot,(dfg,start,end) in tree_dfgs.items() if a in end] for a in total_activities}
    tree_dfgs = {key:value[0] for key,value in tree_dfgs.items()}

    activity_precision= []
    for a in tree_rel.keys():
        if a not in log_rel.keys():
            activity_precision.append(0)
        else:
            sub_precision = []
            for log_pat,tree_pat in [(log_rel,tree_rel),(log_div,tree_div),(log_con,tree_con),(log_defi,tree_defi),(log_opt,tree_opt),
                        (log_start,tree_start),(log_end,tree_end)]:
                if not len(tree_pat[a]):
                    continue
                else:
                    sub_precision.append(len(set(log_pat[a]) & set(tree_pat[a])) / len(set(tree_pat[a])))
            activity_precision.append(numpy.mean(sub_precision))

    relation_precision = []
    for a in tree_rel.keys():
        for b in tree_rel.keys():
            tree_part = {ot for ot in tree_dfgs.keys() if (a, b) in tree_dfgs[ot]}
            if not tree_part:
                continue
            else:
                log_part = {ot for ot in log_dfgs.keys() if (a, b) in log_dfgs[ot]}
                relation_precision.append(len(log_part&tree_part) / len(tree_part))
    return numpy.mean([numpy.mean(activity_precision), numpy.mean(relation_precision)])


