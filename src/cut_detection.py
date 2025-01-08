from OCIM.src.cut_definition import *
from OCIM.src.follows_relations import *
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
import networkx
import more_itertools as mit

"""Methods to detect"""




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


def detect_concurrent_cut(relation_frames, dfgs, clos, rel, div):

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


def detect_exclusive_cut(relation_frames, dfgs, clos, rel, div):

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




def detect_sequence_cut(relation_frames, dfgs, clos, rel, div):

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




def detect_loop_cut(relation_frames, dfgs, clos, rel, div):

    alphabet = list(set(sum([list(frame["ocel:activity"].unique()) for frame in relation_frames],[])))

    #check for the full transitive closure of the alphabet
    for a in alphabet:
        for b in alphabet:
            for ot in get_non_divergent_types(a,b,alphabet,div,rel):
                if not clos[ot].get((a,b),0) or not clos[ot].get((b,a),0):
                    return None

    print("Potential Loop Cut Skipped!")
    print("Switching To Brute Force For Loops (TODO) ")

    #check which object types are fully divergent
    #if they do not have a full dfg connection, no loop cut is possible




    #check which object types are not fully divergent
    #check each type if it is that one by checking if you can split the start and ends correctly
    #then see if the other types can be adjusted to any of that existing partition


    #or just go brute force for the two partition parts :D
    for partition in mit.set_partitions(alphabet, 2):
        for cut in itertools.permutations(partition, len(partition)):
            for check in [is_loop_cut_valid]:
                if check(relation_frames, cut, dfgs, clos, rel, div):
                    return cut

