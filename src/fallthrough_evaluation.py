from auxillary_methods import *
from fallthrough_definition import *

def evaluate_concurrent_fallthrough(part_one, part_two, dfgs, clos, rel, div):

    precision_violation = 0
    precision_correct = 0

    for a in part_one:
        for b in part_two:
            for ot in rel[a] & rel[b]:
                if not dfgs[ot][0].get((a,b),0):
                    precision_violation += 1
                else:
                    precision_correct += 1
                if not dfgs[ot][0].get((b,a),0):
                    precision_violation += 1
                else:
                    precision_correct += 1

    try:
        return 1- (precision_violation / (precision_correct + precision_violation))
    except:
        return 1


def evaluate_xor_fallthrough(part_one, part_two, dfgs, clos, rel, div):

    precision_violation = 0
    precision_correct = 0

    for a in part_one:
        for b in part_two:
            for ot in get_divergent_types(a,b,part_one+part_two,div,rel):
                if not dfgs[ot][0].get((a, b), 0):
                    precision_violation += 1
                else:
                    precision_correct += 1
                if not dfgs[ot][0].get((b, a), 0):
                    precision_violation += 1
                else:
                    precision_correct += 1

    try:
        return 1- (precision_violation / (precision_correct + precision_violation))
    except:
        return 1


def evaluate_sequence_fallthrough(part_one, part_two, dfgs, clos, rel, div):

    precision_violation = 0
    precision_correct = 0

    for a in part_one:
        for b in part_two:
            for ot in get_divergent_types(a,b,part_one+part_two,div,rel):
                if not dfgs[ot][0].get((a, b), 0):
                    precision_violation += 1
                else:
                    precision_correct += 1
                if not dfgs[ot][0].get((b, a), 0):
                    precision_violation += 1
                else:
                    precision_correct += 1
            for ot in get_non_divergent_types(a,b,part_one+part_two,div,rel):
                if not clos[ot].get((a, b), 0):
                    precision_violation += 1
                else:
                    precision_correct += 1

    try:
        return 1- (precision_violation / (precision_correct + precision_violation))
    except:
        return 1


def evaluate_loop_fallthrough(part_one, part_two, dfgs, clos, rel, div):

    precision_violation = 0
    precision_correct = 0

    for a in part_one:
        for b in part_two:
            for ot in get_divergent_types(a,b,part_one+part_two,div,rel):
                if not dfgs[ot][0].get((a, b), 0):
                    precision_violation += 1
                else:
                    precision_correct += 1
                if not dfgs[ot][0].get((b, a), 0):
                    precision_violation += 1
                else:
                    precision_correct += 1
    for a in part_one +part_two:
        for b in part_one + part_two:
            for ot in rel[a] & rel[b]:
                if not clos[ot][0].get((a, b), 0):
                    precision_violation += 1
                else:
                    precision_correct += 1

    try:
        return 1- (precision_violation / (precision_correct + precision_violation))
    except:
        return 1
