import operator

from auxillary_methods import *
from fallthrough_definition import *
from oc_process_trees import *

def evaluate_concurrent_fallthrough(local_data, global_data, part_one, part_two):

    precision_violation = 0
    precision_correct = 0

    for a in part_one:
        for b in part_two:
            for ot in global_data.related[a] & global_data.related[b]:
                if not local_data.dfgs[ot][0].get((a,b),0):
                    precision_violation += 1
                else:
                    precision_correct += 1
                if not local_data.dfgs[ot][0].get((b,a),0):
                    precision_violation += 1
                else:
                    precision_correct += 1

    try:
        return 1- (precision_violation / (precision_correct + precision_violation)), Operator.Concurrent
    except:
        return 1, Operator.Concurrent


def evaluate_xor_fallthrough(local_data, global_data, part_one, part_two):

    precision_violation = 0
    precision_correct = 0

    for a in part_one:
        for b in part_two:
            for ot in get_divergent_types(a,b,part_one+part_two,global_data):
                if not local_data.dfgs[ot][0].get((a, b), 0):
                    precision_violation += 1
                else:
                    precision_correct += 1
                if not local_data.dfgs[ot][0].get((b, a), 0):
                    precision_violation += 1
                else:
                    precision_correct += 1

    try:
        return 1- (precision_violation / (precision_correct + precision_violation)), Operator.Exclusive
    except:
        return 1, Operator.Exclusive


def evaluate_sequence_fallthrough(local_data, global_data, part_one, part_two):

    precision_violation = 0
    precision_correct = 0

    for a in part_one:
        for b in part_two:
            for ot in get_divergent_types(a,b,part_one+part_two,global_data):
                if not local_data.dfgs[ot][0].get((a, b), 0):
                    precision_violation += 1
                else:
                    precision_correct += 1
                if not local_data.dfgs[ot][0].get((b, a), 0):
                    precision_violation += 1
                else:
                    precision_correct += 1
            for ot in get_non_divergent_types(a,b,part_one+part_two,global_data):
                if not local_data.clos[ot].get((a, b), 0):
                    precision_violation += 1
                else:
                    precision_correct += 1

    try:
        return 1- (precision_violation / (precision_correct + precision_violation)), Operator.Sequence
    except:
        return 1, Operator.Sequence


def evaluate_loop_fallthrough(local_data, global_data, part_one, part_two):

    precision_violation = 0
    precision_correct = 0

    for a in part_one:
        for b in part_two:
            for ot in get_divergent_types(a,b,part_one+part_two,global_data):
                if not local_data.dfgs[ot][0].get((a, b), 0):
                    precision_violation += 1
                else:
                    precision_correct += 1
                if not local_data.dfgs[ot][0].get((b, a), 0):
                    precision_violation += 1
                else:
                    precision_correct += 1
    for a in part_one +part_two:
        for b in part_one + part_two:
            for ot in global_data.related[a] & global_data.related[b]:
                if not local_data.clos[ot][0].get((a, b), 0):
                    precision_violation += 1
                else:
                    precision_correct += 1

    try:
        return 1- (precision_violation / (precision_correct + precision_violation)), Operator.Loop
    except:
        return 1, Operator.Loop
