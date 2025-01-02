from OCIM.src.cut_definition import *
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
import networkx
import more_itertools as mit

"""Methods to detect"""





def detect_concurrent_cut(relation_frames, dfgs, clos, rel, div):


    #if two activities do share a type but are not fully connected, they need to be in the same partition part
    #hence, we can perform a connected component analysis on that property
    alphabet = list(set(sum([list(frame["ocel:activity"].unique()) for frame in relation_frames],[])))
    matrix = csr_matrix([[1 if a==b or any([not(dfgs[ot][0].get((a,b),0) and dfgs[ot][0].get((b,a),0))
            for ot in rel[a] & rel[b]]) else 0 for b in alphabet ] for a in alphabet])
    n_components, labels = connected_components(csgraph=matrix, directed=False, return_labels=True)
    partition = [[alphabet[i] for i in range(0,len(alphabet)) if labels[i] == n] for n in range(0,n_components)]

    #if the result is only one connected component, there can not be a valid concurrent cut
    if len(partition) == 1:
        return None

    #check if any partition creates a new start / end event
    trouble_parts = [i for i in range(len(partition)) if len([a for a in partition[i] if
        any([a in get_projected_start(relation_frames, partition[i])[ot] and not dfgs[ot][1].get(a,0) or
            a in get_projected_end(relation_frames, partition[i])[ot] and not dfgs[ot][2].get(a, 0)
             for ot in rel[a]])]) >0]

    good_parts = [i for i in range(len(partition)) if i not in trouble_parts]
    if len(good_parts) <= 1:
        return None

    #merge the broken parts into the good parts and see if the problem gets solved
    #this requires len(broken) * len(good) and is not exponential
    merges = {i:[] for i in good_parts}
    for trouble in trouble_parts:
        for good in good_parts:
            if not any([a in get_projected_start(relation_frames,partition[trouble] + partition[good])[ot] and not dfgs[ot][1].get(a, 0) or
                    a in get_projected_end(relation_frames, partition[trouble] + partition[good])[ot] and not dfgs[ot][2].get(a, 0)
                    for a in partition[trouble] + partition[good] for ot in rel[a]]):
                merges[good].append(trouble)
        return None

    #final (hopefully redundant) check for the validity of the cut
    partition = [partition[good_parts[i]] + sum([partition[j] for j in merges[i]],[]) for i in range(len(good_parts))]
    if is_concurrent_cut_valid(relation_frames,partition,dfgs,clos,rel,div):
        return partition




def detect_exclusive_cut(relation_frames, dfgs, clos, rel, div):

    #if two activities do share a non diverging type and have any connection, they need to be in the same partition part
    alphabet = list(set(sum([list(frame["ocel:activity"].unique()) for frame in relation_frames],[])))
    matrix = csr_matrix([[1 if (a==b or any([(dfgs[ot][0].get((a,b),0) or dfgs[ot][0].get((b,a),0)) and ot not in (div[a] & div[b]) for ot in
        rel[a] & rel[b]])) else 0 for b in alphabet] for a in alphabet])
    n_components, labels = connected_components(csgraph=matrix, directed=False, return_labels=True)
    partition = [[alphabet[i] for i in range(0,len(alphabet)) if labels[i] == n] for n in range(0,n_components)]

    if len(partition) == 1:
        return None

    #check if any partition creates a new start / end event
    trouble_parts = [i for i in range(len(partition)) if len([a for a in partition[i] if
        any([a in get_projected_start(relation_frames, partition[i])[ot] and not dfgs[ot][1].get(a,0) or
            a in get_projected_end(relation_frames, partition[i])[ot] and not dfgs[ot][2].get(a, 0)
             for ot in rel[a]])]) >0]

    good_parts = [i for i in range(len(partition)) if i not in trouble_parts]
    if len(good_parts) <= 1:
        return None

    #merge the broken parts into the good parts and see if the problem gets solved
    #this requires len(broken) * len(good) and is not exponential
    merges = {i:[] for i in good_parts}
    for trouble in trouble_parts:
        for good in good_parts:
            if not any([a in get_projected_start(relation_frames,partition[trouble] + partition[good])[ot] and not dfgs[ot][1].get(a, 0) or
                    a in get_projected_end(relation_frames, partition[trouble] + partition[good])[ot] and not dfgs[ot][2].get(a, 0)
                    for a in partition[trouble] + partition[good] for ot in rel[a]]):
                merges[good].append(trouble)
        return None

    #final (hopefully redundant) check for the validity of the cut
    partition = [partition[good_parts[i]] + sum([partition[j] for j in merges[i]],[]) for i in range(len(good_parts))]
    if is_exclusive_cut_valid(relation_frames,partition,dfgs,clos,rel,div):
        return partition


def detect_sequence_cut(relation_frames, dfgs, clos, rel, div):

    #if two activities do share a non diverging type and have a fully
    #bi-directional connection, they need to be in the same partition part
    alphabet = list(set(sum([list(frame["ocel:activity"].unique()) for frame in relation_frames],[])))
    types = list(set(sum([list(frame["ocel:activity"].unique()) for frame in relation_frames],[])))
    matrix = csr_matrix([[1 if (a==b or any([(bool(dfgs[ot][0].get((a,b),0)) and bool(dfgs[ot][0].get((b,a),0)))
        and ot not in (div[a] & div[b]) for ot in rel[a] & rel[b]]) ) else 0 for b in alphabet] for a in alphabet])
    n_components, labels = connected_components(csgraph=matrix, directed=False, return_labels=True)
    partition = [[alphabet[i] for i in range(0,len(alphabet)) if labels[i] == n] for n in range(0,n_components)]

    if len(partition) == 1:
        return None


    while True:

        # check which non-diverging object types are shared between partition parts and which order they induce
        # check if there are any cycles in this order, if yes, you need to merge them
        shared_types = {(i, j): set(sum([get_non_divergent_types(a, b, partition[i] + partition[j], div, rel)
                                         for a in partition[i] for b in partition[j]], [])) for i in
                        range(len(partition)) for j in range(len(partition)) if i != j}
        edges = [(i, j) for (i, j), ots in shared_types.items() if
                 any([clos[ot].get((a, b), 0) for a in partition[i] for b in partition[j] for ot in ots])]

        try:
            cycle = networkx.find_cycle(networkx.DiGraph(edges), orientation="original")
            partition = ([partition[i] for i in range(len(partition)) if i not in set(sum([[a,b] for a,b,d in cycle],[]))]
                    + [sum([partition[i] for i in set(sum([[a,b] for a,b,d in cycle],[]))],[])])
            if len(partition) == 1:
                return None

        except networkx.NetworkXNoCycle:
            partition = [partition[i] for i in networkx.topological_sort(networkx.DiGraph(edges))]
            break


    if is_sequence_cut_valid(relation_frames,partition,dfgs,clos,rel,div):
        return partition





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

    for partition in mit.set_partitions(alphabet, 2):
        for cut in itertools.permutations(partition, len(partition)):
            for check in [is_loop_cut_valid]:
                if check(relation_frames, cut, dfgs, clos, rel, div):
                    return cut

