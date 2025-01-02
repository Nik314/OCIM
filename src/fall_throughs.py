from OCIM.src.cut_definition import *
import more_itertools as mit
import itertools




def detect_fallthrough_fitness(relations, dfgs, clos, rel, div):

    print("Fall Through Detection Triggered")
    alphabet = list(set(sum([list(frame["ocel:activity"].unique()) for frame in relations],[])))
    best_partition = [[a] for a in alphabet]
    best_violations = evaluate_concurrent(relations,best_partition,dfgs,clos,rel,div)[0]
    best_operator = is_concurrent_cut_valid

    for partition in mit.set_partitions(alphabet, 2):
        for check in [evaluate_xor,evaluate_concurrent]:
            prec,fit,vio = check(relations,partition,dfgs,clos,rel,div)

            if fit == 0.00 and prec < best_violations:
                best_operator = check
                best_partition = partition
                best_violations = prec
                print(f"Violations Remaining :{best_violations}")
                print(best_partition,best_operator)

        for cut in itertools.permutations(partition, len(partition)):
            prec,fit,vio = evaluate_sequence(relations,cut,dfgs,clos,rel,div)
            if fit == 0.00 and prec < best_violations:
                best_operator = evaluate_sequence
                best_partition = cut
                best_violations = prec
                print(f"Violations Remaining :{best_violations}")
                print(best_partition,best_operator)

    return best_partition,best_operator






