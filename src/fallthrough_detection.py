from OCIM.src.fallthrough_definition import *
from OCIM.src.fallthrough_evaluation import *
import more_itertools as mit
import itertools
import numpy
from sklearn.cluster import KMeans




def detect_distance_concurrent(a,b,dfgs,rel):
    if a == b: return 0.0
    total = sum([2 for ot in rel[a] & rel[b]])
    correct = sum([1 if dfgs[ot][0].get((a,b),0) else 0 for ot in rel[a] & rel[b]])
    correct += sum([1 if dfgs[ot][0].get((b,a),0) else 0 for ot in rel[a] & rel[b]])
    return correct / total


def detect_fallthrough_concurrent(relations, dfgs, clos, rel, div):

    alphabet = list(set(sum([list(frame["ocel:activity"].unique()) for frame in relations],[])))
    distances = [[detect_distance_concurrent(a,b,dfgs,rel) for a in alphabet] for b in alphabet]
    kmeans = KMeans(n_clusters=2, random_state=0).fit(numpy.array(distances))
    part_one = [alphabet[i] for i in range(0,len(alphabet)) if kmeans.labels_[i] == 0]
    part_two = [alphabet[i] for i in range(0,len(alphabet)) if kmeans.labels_[i] == 1]
    return evaluate_concurrent_fallthrough(part_one,part_two,dfgs,clos,rel,div),[part_one, part_two]





def detect_fallthrough_fitness_brute_force(relations, dfgs, clos, rel, div):

    print("Fall Through Detection Triggered")
    alphabet = list(set(sum([list(frame["ocel:activity"].unique()) for frame in relations],[])))
    best_score,best_partition, best_operator = 0.00, None, None

    score, partition = detect_fallthrough_concurrent(relations,dfgs,clos,rel,div)
    if score >= best_score:
        best_score, best_partition, best_operator = score, partition, evaluate_concurrent_fallthrough


    for partition in mit.set_partitions(alphabet, 2):
        for check in [evaluate_xor_fallthrough]:

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






