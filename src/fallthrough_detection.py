from OCIM.src.fallthrough_definition import *
from OCIM.src.fallthrough_evaluation import *
from OCIM.src.auxillary_methods import *
from OCIM.src.follows_relations import *
import more_itertools as mit
import itertools
import numpy
from sklearn.cluster import KMeans
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
import networkx


def detect_distance_concurrent(a,b,dfgs,rel):
    if a == b: return 0.0
    total = sum([2 for ot in rel[a] & rel[b]])
    correct = sum([1 if dfgs[ot][0].get((a,b),0) else 0 for ot in rel[a] & rel[b]])
    correct += sum([1 if dfgs[ot][0].get((b,a),0) else 0 for ot in rel[a] & rel[b]])
    try:
        return correct / total
    except:
        return 1


def detect_fallthrough_concurrent(relations, dfgs, clos, rel, div):

    alphabet = list(set(sum([list(frame["ocel:activity"].unique()) for frame in relations],[])))
    distances = [[detect_distance_concurrent(a,b,dfgs,rel) for a in alphabet] for b in alphabet]
    kmeans = KMeans(n_clusters=2, random_state=0).fit(numpy.array(distances))
    part_one = [alphabet[i] for i in range(0,len(alphabet)) if kmeans.labels_[i] == 0]
    part_two = [alphabet[i] for i in range(0,len(alphabet)) if kmeans.labels_[i] == 1]
    return evaluate_concurrent_fallthrough(part_one,part_two,dfgs,clos,rel,div),[part_one, part_two]



def detect_distance_exclusive(part_one,part_two,dfgs,rel,div):
    if part_one == part_two: return 0.0
    total = sum([2 for a in part_one for b in part_two for ot in get_divergent_types(a,b,part_one+part_two,div,rel)])
    correct = sum([1 if dfgs[ot][0].get((a,b),0) else 0 for a in part_one for b in part_two for ot in get_divergent_types(a,b,part_one+part_two,div,rel) ])
    correct += sum([1 if dfgs[ot][0].get((b,a),0) else 0 for a in part_one for b in part_two for ot in get_divergent_types(a,b,part_one+part_two,div,rel)])
    return correct / total


def detect_fallthrough_exclusive(relations, dfgs, clos, rel, div):

    alphabet = list(set(sum([list(frame["ocel:activity"].unique()) for frame in relations],[])))
    edges = [[1 if a==b or any(dfgs[ot][0].get((a,b),0) or dfgs[ot][0].get((b,a),0)
            for ot in get_non_divergent_types(a,b,alphabet,div, rel))
            else 0 for a in alphabet] for b in alphabet]
    n_components, labels = connected_components(csgraph=csr_matrix(edges), directed=False, return_labels=True)
    if n_components == 1:
        return -1, None
    partition = [[alphabet[i] for i in range(0,len(alphabet)) if labels[i] == n] for n in range(0,n_components)]
    distances = [[detect_distance_exclusive(p1,p2,dfgs,rel,div) for p1 in partition] for p2 in partition]
    kmeans = KMeans(n_clusters=2, random_state=0).fit(numpy.array(distances))
    part_one = sum([partition[i] for i in range(0,len(partition)) if kmeans.labels_[i] == 0],[])
    part_two = sum([partition[i] for i in range(0,len(partition)) if kmeans.labels_[i] == 1],[])
    return evaluate_xor_fallthrough(part_one,part_two,dfgs,clos,rel,div),[part_one, part_two]



def detect_fallthrough_sequence(relations, dfgs, clos, rel, div):

    alphabet = list(set(sum([list(frame["ocel:activity"].unique()) for frame in relations],[])))
    edges = [[1 if a==b or any((clos[ot].get((a,b),0) and clos[ot].get((b,a),0))
            for ot in get_non_divergent_types(a,b,alphabet,div, rel))
            else 0 for a in alphabet] for b in alphabet]
    n_components, labels = connected_components(csgraph=csr_matrix(edges), directed=False, return_labels=True)
    if n_components == 1:
        return -1, None

    partition = [[alphabet[i] for i in range(0,len(alphabet)) if labels[i] == n] for n in range(0,n_components)]
    partition_follows = get_transitive_closure_partition_relations(partition,dfgs,div,rel)
    edges = [[1 if a==b or edges[alphabet.index(b)][alphabet.index(a)] or any([(i,j) in partition_follows and (j,i) in partition_follows
            for i in range(0,len(partition)) for j in range(0,len(partition)) if a in partition[i] and b in partition[j]])
            else 0 for a in alphabet] for b in alphabet]
    n_components, labels = connected_components(csgraph=csr_matrix(edges), directed=False, return_labels=True)
    if n_components == 1:
        return -1, None

    partition = [[alphabet[i] for i in range(0,len(alphabet)) if labels[i] == n] for n in range(0,n_components)]
    partition = [partition[i] for i in networkx.topological_sort(networkx.DiGraph(get_partition_follows_relations(partition,dfgs,div,rel)))]
    best_score, best_partition = -1, None

    for i in range(1, len(partition)-1):
        part_one = sum(partition[j] for j in range(0,i))
        part_two = sum(partition[j] for j in range(i,len(partition)))
        score = evaluate_sequence_fallthrough(part_one,part_two,dfgs,clos,rel,div)
        if score >= best_score:
            best_score = score
            best_partition = [part_one,part_two]

    return best_score,best_partition





def detect_loop_pair(relation_frames, dfgs, clos, rel,div, a,b):

    alphabet = list(set(sum([list(frame["ocel:activity"].unique()) for frame in relation_frames],[])))

    for ot in rel[a] & rel[b]:
        if (dfgs[ot][1].get(a,0) or dfgs[ot][2].get(a,0)) and (dfgs[ot][1].get(b,0) or dfgs[ot][2].get(b,0)):
            return True
        if (dfgs[ot][0].get((a, b), 0) and not dfgs[ot][2].get(a,0) and not dfgs[ot][1].get(b,0)
            and ot not in get_divergent_types(a, b, alphabet, div, rel)):
            return True

    return False


def detect_fallthrough_loop(relations, dfgs, clos, rel, div):

    alphabet = list(set(sum([list(frame["ocel:activity"].unique()) for frame in relations],[])))
    object_types = list(set(sum([list(frame["ocel:type"].unique()) for frame in relations],[])))

    edges = [[1 if a==b or detect_loop_pair(relations, dfgs, clos, rel, div, a,b)
            else 0 for a in alphabet] for b in alphabet]
    n_components, labels = connected_components(csgraph=csr_matrix(edges), directed=False, return_labels=True)
    if n_components == 1:
        return -1, None

    best_partition, best_score = None, -1
    body,redo = set(), set()

    partition = [[alphabet[i] for i in range(0,len(alphabet)) if labels[i] == n] for n in range(0,n_components)]
    for ot in object_types:
        if not any(ot in rel[a] and ot not in div[a] for a in alphabet):
            continue

        i = 0
        for i in range(0,n_components):
            if any(dfgs[ot][1].get(a,0) or dfgs[ot][2].get(a,0) for a in partition[i]):
                body = partition[i]
                break

        for j in range(0,n_components):
            if i != j and any([ot in rel[a] for a in partition[j]]):
                redo = sum([partition[k] for k in range(0,n_components) if k != i],[])

                if is_loop_fallthrough_valid(relations,[body,redo],dfgs,clos,rel,div) and body and redo:
                    if evaluate_loop_fallthrough(body,redo, dfgs,clos,rel,div) > best_score:
                        best_score = evaluate_loop_fallthrough(body,redo, dfgs,clos,rel,div)
                        best_partition = [body,redo]

                print("Invalid Loop Cut Found (Proven To Not be Possible, So Go Find The Bug!) ")
    return best_score, best_partition





def detect_fallthrough_fitness_polynomial(relations, dfgs, clos, rel, div):

    print("Fall Through Detection Triggered")
    alphabet = list(set(sum([list(frame["ocel:activity"].unique()) for frame in relations],[])))
    best_score,best_partition, best_operator = 0.00, None, None

    score, partition = detect_fallthrough_concurrent(relations,dfgs,clos,rel,div)
    print(score,partition)
    if score >= best_score:
        best_score, best_partition, best_operator = score, partition, evaluate_concurrent_fallthrough

    score, partition = detect_fallthrough_exclusive(relations,dfgs,clos,rel,div)
    print(score,partition)
    if score >= best_score:
        best_score, best_partition, best_operator = score, partition, evaluate_xor_fallthrough

    score, partition = detect_fallthrough_sequence(relations,dfgs,clos,rel,div)
    print(score,partition)
    if score >= best_score:
        best_score, best_partition, best_operator = score, partition, evaluate_sequence_fallthrough

    score, partition = detect_fallthrough_loop(relations,dfgs,clos,rel,div)
    print(score,partition)
    if score >= best_score:
        best_score, best_partition, best_operator = score, partition, evaluate_loop_fallthrough

    return best_partition, best_operator






def detect_fallthrough_fitness_brute_force(relations, dfgs, clos, rel, div):

    print("Fall Through Detection Triggered (Brute Force)")
    alphabet = list(set(sum([list(frame["ocel:activity"].unique()) for frame in relations],[])))
    best_score,best_partition, best_operator = 0.00, None, None

    for partition in mit.set_partitions(alphabet, 2):

        for check in [evaluate_xor_fallthrough, evaluate_concurrent_fallthrough]:

            if check == evaluate_concurrent_fallthrough and not is_exclusive_fallthrough_valid(relations, partition, dfgs,clos, rel, div):
                continue
            if check == evaluate_concurrent_fallthrough and not is_concurrent_fallthrough_valid(relations, partition,dfgs, clos, rel, div):
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






