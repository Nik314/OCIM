from OCIM.src.fallthrough_definition import *
from OCIM.src.fallthrough_evaluation import *
import more_itertools as mit
import itertools







def detect_fallthrough_fitness_brute_force(relations, dfgs, clos, rel, div):

    print("Fall Through Detection Triggered")
    alphabet = list(set(sum([list(frame["ocel:activity"].unique()) for frame in relations],[])))
    best_score,best_partition, best_operator = 0.00, None, None

    for partition in mit.set_partitions(alphabet, 2):
        for check in [evaluate_xor_fallthrough,evaluate_concurrent_fallthrough]:

            if check == evaluate_xor_fallthrough and not is_exclusive_fallthrough_valid(relations,partition,dfgs,clos,rel,div):
                continue
            if check == evaluate_concurrent_fallthrough and not is_concurrent_fallthrough_valid(relations,partition,dfgs,clos,rel,div):
                continue

            score = check(partition[0],partition[1],dfgs,clos,rel,div)
            if score >= best_score:
                best_score, best_partition, best_operator = score, partition, check


        for check in [evaluate_sequence_fallthrough, evaluate_loop_fallthrough]:

            if check == evaluate_sequence_fallthrough and not is_sequence_fallthrough_valid(relations, partition, dfgs,clos, rel, div):
                continue
            if check == evaluate_loop_fallthrough and not is_loop_fallthrough_valid(relations, partition,dfgs, clos, rel, div):
                continue

            score = check(partition[0],partition[1],dfgs,clos,rel,div)
            if score >= best_score:
                best_score, best_partition, best_operator = score, partition, check

        partition = list(reversed(partition))
        for check in [evaluate_sequence_fallthrough, evaluate_loop_fallthrough]:

                if check == evaluate_sequence_fallthrough and not is_sequence_fallthrough_valid(relations, partition, dfgs, clos, rel, div):
                    continue
                if check == evaluate_loop_fallthrough and not is_loop_fallthrough_valid(relations, partition, dfgs,clos, rel, div):
                    continue

                score = check(partition[0], partition[1], dfgs, clos, rel, div)
                if score >= best_score:
                    best_score, best_partition, best_operator = score, partition, check

    return best_partition,best_operator






