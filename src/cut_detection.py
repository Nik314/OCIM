from OCIM.src.cut_definition import *
from OCIM.src.follows_relations import *
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
import networkx
import more_itertools as mit

"""Methods to detect cuts for the object-centric inductive miner in polynomial runtime. Methods are not optimized but 
rather a 1:1 reflection of the papers section 3.2. Each of the methods below correspond to the pseudocode function 
with the same name in the paper (Algorithm 4,5,6,7 for concurrent, choice, sequence and loop operator). """




def find_strict_cut(relation_frames, dfgs, clos, rel, div):

    sequence = find_cut_sequence(relation_frames, dfgs, clos, rel, div)
    if sequence:
        return (sequence, is_sequence_cut_valid)

    exclusive = find_cut_exclusive(relation_frames, dfgs, clos, rel, div)
    if exclusive:
        return (exclusive, is_exclusive_cut_valid)

    loop = find_cut_loop(relation_frames, dfgs, clos, rel, div)
    if loop:
        return (loop, is_loop_cut_valid)

    concurrent = find_cut_concurrent(relation_frames,dfgs,clos,rel,div)
    if concurrent:
        return (concurrent, is_concurrent_cut_valid)


    return None



def check_concurrent(relation_frames, dfgs, rel, a, b, alphabet):
    for ot in rel[a] & rel[b]:
        if not (dfgs[ot][0].get((a,b),0) and dfgs[ot][0].get((b,a),0)):
            return True
        if (dfgs[ot][1].get(a,0) and not dfgs[ot][1].get(b,0) and
                b in get_projected_start(relation_frames,[c for c in alphabet if c != a])[ot]):
            return True
        if (dfgs[ot][2].get(a,0) and not dfgs[ot][2].get(b,0) and
                b in get_projected_end(relation_frames,[c for c in alphabet if c != a])[ot]):
            return True
    return False


def find_cut_concurrent(relation_frames, dfgs, clos, rel, div):

    alphabet = list(set(sum([list(frame["ocel:activity"].unique()) for frame in relation_frames],[])))
    edges = [[1 if a==b or check_concurrent(relation_frames,dfgs,rel,a,b,alphabet)
                   or check_concurrent(relation_frames,dfgs,rel,b,a,alphabet)
              else 0 for a in alphabet] for b in alphabet]
    n_components, labels = connected_components(csgraph=csr_matrix(edges), directed=False, return_labels=True)
    partition = [[alphabet[i] for i in range(0,len(alphabet)) if labels[i] == n] for n in range(0,n_components)]

    if len(partition) == 1:
        return None

    if is_concurrent_cut_valid(relation_frames,partition,dfgs,clos,rel,div):
        return partition

    print("Invalid Concurrent Cut Found (Proven To Not be Possible, So Go Find The Bug!) ")



def check_exclusive_1(relation_frames, dfgs, rel, div, a, b, alphabet):
    for ot in rel[a] & rel[b]:
        if dfgs[ot][0].get((a,b),0) or dfgs[ot][0].get((b,a),0) and ot not in div[a] & div[b]:
            return True
        if bool(dfgs[ot][0].get((a,b),0)) != bool(dfgs[ot][0].get((b,a),0)) and ot in div[a] & div[b]:
            return True
        if (dfgs[ot][1].get(a,0) and not dfgs[ot][1].get(b,0) and
                b in get_projected_start(relation_frames,[c for c in alphabet if c != a])[ot]):
            return True
        if (dfgs[ot][2].get(a,0) and not dfgs[ot][2].get(b,0) and
                b in get_projected_end(relation_frames,[c for c in alphabet if c != a])[ot]):
            return True
    return False

def check_exclusive_2(dfgs, rel, div, sigma_i, sigma_j):

    for a in sigma_i:
        for b in sigma_j:
            for ot in get_divergent_types(a,b,sigma_j+sigma_i,div,rel):
                if not dfgs[ot][0].get((a,b),0) or not dfgs[ot][0].get((b,a),0):
                    return True

    if all(len(get_non_divergent_types(a,b,sigma_j+sigma_i,div,rel)) == 0 for a in sigma_i for b in sigma_j):
        return True

    return False


def find_cut_exclusive(relation_frames, dfgs, clos, rel, div):

    alphabet = list(set(sum([list(frame["ocel:activity"].unique()) for frame in relation_frames],[])))
    edges = [[1 if a==b or check_exclusive_1(relation_frames,dfgs,rel,div,a,b,alphabet)
              else 0 for a in alphabet] for b in alphabet]
    n_components, labels = connected_components(csgraph=csr_matrix(edges), directed=False, return_labels=True)
    partition = [[alphabet[i] for i in range(0,len(alphabet)) if labels[i] == n] for n in range(0,n_components)]

    edges = [[1 if a==b or check_exclusive_1(relation_frames,dfgs,rel,div,a,b,alphabet)
            or check_exclusive_2(dfgs,rel,div, [p for p in partition if a in p][0],[p for p in partition if b in p][0])
            else 0 for a in alphabet] for b in alphabet]
    n_components, labels = connected_components(csgraph=csr_matrix(edges), directed=False, return_labels=True)
    partition = [[alphabet[i] for i in range(0,len(alphabet)) if labels[i] == n] for n in range(0,n_components)]

    if len(partition) == 1:
        return None

    if is_exclusive_cut_valid(relation_frames,partition,dfgs,clos,rel,div):
        return partition

    print("Invalid Exclusive Cut Found (Proven To Not be Possible, So Go Find The Bug!) ")




def check_sequence_1(clos, rel, div, a, b):
    for ot in get_non_divergent_types(a,b,[a,b],div,rel):
        if clos[ot].get((a,b),0) and clos[ot].get((b,a),0):
            return True
        if not clos[ot].get((a,b),0) and not clos[ot].get((b,a),0):
            return True
    return False


def check_sequence_2(partition_closure, i, j):
    if not (i,j) in partition_closure and not (j,i) in partition_closure:
        return True
    return False


def check_sequence_3(partition, i, j,div, rel, dfgs):
    if i > j:
        j,i = i,j
    for a in partition[i]:
        for b in partition[j]:
            for ot in get_divergent_types(a,b,sum([partition[k] for k in range(i,j+1)],[]),div,rel):
                if not dfgs[ot][0].get((a,b),0) or not dfgs[ot][0].get((b,a),0):
                    print(ot,a,b)
                    return True
    return False


def find_cut_sequence(relation_frames, dfgs, clos, rel, div):

    alphabet = list(set(sum([list(frame["ocel:activity"].unique()) for frame in relation_frames],[])))
    edges = [[1 if a==b or check_sequence_1(clos,rel,div,a,b)
              else 0 for a in alphabet] for b in alphabet]
    n_components, labels = connected_components(csgraph=csr_matrix(edges), directed=False, return_labels=True)
    partition = [[alphabet[i] for i in range(0,len(alphabet)) if labels[i] == n] for n in range(0,n_components)]

    if len(partition) == 1:
        return None

    partition_closure = get_transitive_closure_partition_relations(partition,dfgs,div,rel)
    edges = [[1 if a==b or check_sequence_1(clos,rel,div,a,b) or check_sequence_2(partition_closure,
            [i for i in range(0,len(partition)) if a in partition[i]][0],
            [i for i in range(0,len(partition)) if b in partition[i]][0])
              else 0 for a in alphabet] for b in alphabet]
    n_components, labels = connected_components(csgraph=csr_matrix(edges), directed=False, return_labels=True)
    partition = [[alphabet[i] for i in range(0,len(alphabet)) if labels[i] == n] for n in range(0,n_components)]

    if len(partition) == 1:
        return None

    partition = [partition[i] for i in networkx.topological_sort(networkx.DiGraph(get_partition_follows_relations(partition,dfgs,div,rel)))]
    partition_closure = get_transitive_closure_partition_relations(partition,dfgs,div,rel)
    edges = [[1 if a==b or check_sequence_1(clos,rel,div,a,b) or check_sequence_2(partition_closure,
            [i for i in range(0,len(partition)) if a in partition[i]][0],
            [i for i in range(0,len(partition)) if b in partition[i]][0]) or check_sequence_3(partition,
            [i for i in range(0,len(partition)) if a in partition[i]][0],
            [i for i in range(0,len(partition)) if b in partition[i]][0], div, rel, dfgs)
              else 0 for a in alphabet] for b in alphabet]
    n_components, labels = connected_components(csgraph=csr_matrix(edges), directed=False, return_labels=True)
    partition = [[alphabet[i] for i in range(0,len(alphabet)) if labels[i] == n] for n in range(0,n_components)]
    partition = [partition[i] for i in networkx.topological_sort(networkx.DiGraph(get_partition_follows_relations(partition,dfgs,div,rel)))]

    if len(partition) == 1:
        return None

    if is_sequence_cut_valid(relation_frames,partition,dfgs,clos,rel,div):
        return partition

    print("Invalid Seqeunce Cut Found (Proven To Not be Possible, So Go Find The Bug!) ")
    print(partition)



def check_loop(relation_frames, dfgs, clos, rel,div, a,b):

    alphabet = list(set(sum([list(frame["ocel:activity"].unique()) for frame in relation_frames],[])))

    for ot in rel[a] & rel[b]:
        if (not dfgs[ot][0].get((a,b),0) or not dfgs[ot][0].get((b,a),0) and
                ot not in get_divergent_types(a,b,alphabet,div,rel)):
            return True
        if (dfgs[ot][1].get(a,0) or dfgs[ot][2].get(a,0)) and (dfgs[ot][1].get(b,0) or dfgs[ot][2].get(b,0)):
            return True
        if (dfgs[ot][0].get((a, b), 0) and not dfgs[ot][2].get(a,0) and not dfgs[ot][1].get(b,0)
            and ot not in get_divergent_types(a, b, alphabet, div, rel)):
            return True

    return False

def find_cut_loop(relation_frames, dfgs, clos, rel, div):


    alphabet = list(set(sum([list(frame["ocel:activity"].unique()) for frame in relation_frames],[])))
    object_types = list(set(sum([list(frame["ocel:type"].unique()) for frame in relation_frames],[])))

    for a in alphabet:
        for b in alphabet:
            for ot in get_non_divergent_types(a,b,alphabet,div,rel):
                if not clos[ot].get((a,b),0) or not clos[ot].get((b,a),0):
                    return None

    edges = [[1 if a==b or check_loop(relation_frames,dfgs,clos,rel,div,a,b)
              else 0 for a in alphabet] for b in alphabet]
    n_components, labels = connected_components(csgraph=csr_matrix(edges), directed=False, return_labels=True)
    partition = [[alphabet[i] for i in range(0,len(alphabet)) if labels[i] == n] for n in range(0,n_components)]

    if len(partition) == 1:
        return None

    body,redo = set(),set()

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

                if is_loop_cut_valid(relation_frames,[body,redo],dfgs,clos,rel,div):
                    return [body,redo]

                print("Invalid Loop Cut Found (Proven To Not be Possible, So Go Find The Bug!) ")
                print([body,redo])


