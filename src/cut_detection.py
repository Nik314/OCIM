from cut_definition import *
from follows_relations import *
from oc_process_trees import *
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
import networkx

"""Methods to detect cuts for the object-centric inductive miner in polynomial runtime. Methods are not optimized but 
rather a 1:1 reflection of the papers section 3.2. Each of the methods below correspond to the pseudocode function 
with the same name in the paper (Algorithm 4,5,6,7 for concurrent, choice, sequence and loop operator). """




def find_strict_cut(local_data, global_data):
    for check in [find_cut_sequence,find_cut_exclusive,find_cut_concurrent,find_cut_loop]:
        partition,operator = check(local_data, global_data)
        if partition:
            global_data.quality_info["cuts"].append((partition, operator))
            return partition, operator
    return None, None



def check_concurrent(local_data, global_data, a,b):
    for ot in global_data.related[a] & global_data.related[b]:
        if not (local_data.dfgs[ot][0].get((a,b),0) and local_data.dfgs[ot][0].get((b,a),0)):
            return True
        if (local_data.dfgs[ot][1].get(a,0) and not local_data.dfgs[ot][1].get(b,0) and
                b in get_projected_start(local_data,[c for c in local_data.alphabet if c != a])[ot]):
            return True
        if (local_data.dfgs[ot][2].get(a,0) and not local_data.dfgs[ot][2].get(b,0) and
                b in get_projected_end(local_data,[c for c in local_data.alphabet if c != a])[ot]):
            return True
    return False


def find_cut_concurrent(local_data, global_data):

    edges = [[1 if a==b or check_concurrent(local_data, global_data, a,b)
                   or check_concurrent(local_data, global_data, b,a)
              else 0 for a in local_data.alphabet] for b in local_data.alphabet]

    n_components, labels = connected_components(csgraph=csr_matrix(edges), directed=False, return_labels=True)
    partition = [[local_data.alphabet[i] for i in range(0,len(local_data.alphabet)) if labels[i] == n] for n in range(0,n_components)]

    if len(partition) == 1:
        return None, None

    while True:
        if is_concurrent_cut_valid(local_data,global_data,partition):
            return partition, Operator.PARALLEL
        else:

            start_problems = {}

            for i in range(len(partition)):
                for a in partition[i]:
                    for ot in global_data.related[a]:
                        if a in get_projected_start(local_data, partition[i])[ot] and not local_data.dfgs[ot][
                            1].get(a, 0):
                            start_problems[i] = []

            for problem in start_problems.keys():
                for j in range(len(partition)):
                    if j == problem:
                        continue

                    check = True
                    for a in partition[problem]:
                        for ot in global_data.related[a]:
                            if a in get_projected_start(local_data, partition[problem] + partition[j])[ot] and not local_data.dfgs[ot][
                                1].get(a, 0):
                                check = False

                    if check:
                        start_problems[problem].append(j)

            end_problem = {}

            for i in range(len(partition)):
                for a in partition[i]:
                    for ot in global_data.related[a]:
                        if a in get_projected_end(local_data, partition[i])[ot] and not local_data.dfgs[ot][2].get(
                                a, 0):
                            end_problem[i] = []

            for problem in end_problem.keys():
                for j in range(len(partition)):
                    if j == problem:
                        continue

                    check = True
                    for a in partition[problem]:
                        for ot in global_data.related[a]:
                            if a in get_projected_end(local_data, partition[problem]+ partition[j])[ot] and not local_data.dfgs[ot][2].get(
                                    a, 0):
                                check = False

                    if check:
                        end_problem[problem].append(j)

            print("TODO Edge Case For Start & End Activities For The COncurrent Operator")
            print(start_problems)
            print(end_problem)
            break

    print("Invalid Concurrent Cut Found (Proven To Not be Possible, So Go Find The Bug!) ")
    return None, None



def check_exclusive_1(local_data, global_data, a, b):
    for ot in global_data.related[a] & global_data.related[b]:
        if (local_data.dfgs[ot][0].get((a,b),0) or local_data.dfgs[ot][0].get((b,a),0) and
                ot not in global_data.divergence[a] & global_data.divergence[b]):
            return True
        if (bool(local_data.dfgs[ot][0].get((a,b),0)) != bool(local_data.dfgs[ot][0].get((b,a),0))
                and ot in global_data.divergence[a] & global_data.divergence[b]):
            return True
        if (local_data.dfgs[ot][1].get(a,0) and not local_data.dfgs[ot][1].get(b,0) and
                b in get_projected_start(local_data,[c for c in local_data.alphabet if c != a])[ot]):
            return True
        if (local_data.dfgs[ot][2].get(a,0) and not local_data.dfgs[ot][2].get(b,0) and
                b in get_projected_end(local_data,[c for c in local_data.alphabet if c != a])[ot]):
            return True
    return False


def check_exclusive_2(local_data, global_data, sigma_i, sigma_j):

    for a in sigma_i:
        for b in sigma_j:
            for ot in get_divergent_types(a,b,sigma_j+sigma_i,global_data):
                if not local_data.dfgs[ot][0].get((a,b),0) or not local_data.dfgs[ot][0].get((b,a),0):
                    return True

    if all(len(get_non_divergent_types(a,b,sigma_j+sigma_i,global_data)) == 0 for a in sigma_i for b in sigma_j):
        return True

    return False


def find_cut_exclusive(local_data,global_data):

    edges = [[1 if a==b or check_exclusive_1(local_data,global_data,a,b) or check_exclusive_1(local_data,global_data,b,a)
              else 0 for a in local_data.alphabet] for b in local_data.alphabet]
    n_components, labels = connected_components(csgraph=csr_matrix(edges), directed=False, return_labels=True)
    partition = [[local_data.alphabet[i] for i in range(0,len(local_data.alphabet)) if labels[i] == n] for n in range(0,n_components)]

    if len(partition) == 1:
        return None, None

    edges = [[1 if a==b or check_exclusive_1(local_data,global_data,a,b) or check_exclusive_1(local_data,global_data,b,a)
            or check_exclusive_2(local_data,global_data,
            [p for p in partition if a in p][0], [p for p in partition if b in p][0])
            else 0 for a in local_data.alphabet] for b in local_data.alphabet]
    n_components, labels = connected_components(csgraph=csr_matrix(edges), directed=False, return_labels=True)
    partition = [[local_data.alphabet[i] for i in range(0,len(local_data.alphabet)) if labels[i] == n] for n in range(0,n_components)]

    if len(partition) == 1:
        return None, None

    if is_exclusive_cut_valid(local_data,global_data,partition):
        return partition, Operator.XOR

    print("Invalid Exclusive Cut Found (Proven To Not be Possible, So Go Find The Bug!) ")
    return None, None



def check_sequence_1(local_data, global_data, a, b):
    for ot in get_non_divergent_types(a,b,[a,b],global_data):
        if local_data.clos[ot].get((a,b),0) and local_data.clos[ot].get((b,a),0):
            return True
        if not local_data.clos[ot].get((a,b),0) and not local_data.clos[ot].get((b,a),0):
            return True
    return False


def check_sequence_2(partition_closure, i, j):
    if not (i,j) in partition_closure and not (j,i) in partition_closure:
        return True
    if (i,j) in partition_closure and (j,i) in partition_closure:
        return True
    return False


def check_sequence_3(local_data, global_data, partition, i, j):
    if i > j:
        j,i = i,j
    for a in partition[i]:
        for b in partition[j]:
            for ot in get_divergent_types(a,b,sum([partition[k] for k in range(i,j+1)],[]),global_data):
                if not local_data.dfgs[ot][0].get((a,b),0) or not local_data.dfgs[ot][0].get((b,a),0):
                    return True
    return False


def find_cut_sequence(local_data, global_data):

    edges = [[1 if a==b or check_sequence_1(local_data, global_data, a,b)
              else 0 for a in local_data.alphabet] for b in local_data.alphabet]
    n_components, labels = connected_components(csgraph=csr_matrix(edges), directed=False, return_labels=True)
    partition = [[local_data.alphabet[i] for i in range(0,len(local_data.alphabet)) if labels[i] == n] for n in range(0,n_components)]

    if len(partition) == 1:
        return None, None

    partition_closure = get_transitive_closure_partition_relations(local_data,global_data,partition)
    edges = [[1 if a==b or check_sequence_1(local_data, global_data, a, b) or check_sequence_2(partition_closure,
            [i for i in range(0,len(partition)) if a in partition[i]][0],
            [i for i in range(0,len(partition)) if b in partition[i]][0])
              else 0 for a in local_data.alphabet] for b in local_data.alphabet]
    n_components, labels = connected_components(csgraph=csr_matrix(edges), directed=False, return_labels=True)
    partition = [[local_data.alphabet[i] for i in range(0,len(local_data.alphabet)) if labels[i] == n] for n in range(0,n_components)]

    if len(partition) == 1:
        return None, None

    partition = [partition[i] for i in networkx.topological_sort(networkx.DiGraph(get_partition_follows_relations(local_data,global_data,partition)))]
    partition_closure = get_transitive_closure_partition_relations(local_data,global_data,partition)
    edges = [[1 if a==b or check_sequence_1(local_data,global_data,a,b) or check_sequence_2(partition_closure,
            [i for i in range(0,len(partition)) if a in partition[i]][0],
            [i for i in range(0,len(partition)) if b in partition[i]][0]) or check_sequence_3(local_data,global_data, partition,
            [i for i in range(0,len(partition)) if a in partition[i]][0],
            [i for i in range(0,len(partition)) if b in partition[i]][0])
              else 0 for a in local_data.alphabet] for b in local_data.alphabet]
    n_components, labels = connected_components(csgraph=csr_matrix(edges), directed=False, return_labels=True)
    partition = [[local_data.alphabet[i] for i in range(0,len(local_data.alphabet)) if labels[i] == n] for n in range(0,n_components)]
    partition = [partition[i] for i in networkx.topological_sort(networkx.DiGraph(get_partition_follows_relations(local_data,global_data,partition)))]

    if len(partition) == 1:
        return None, None

    if is_sequence_cut_valid(local_data,global_data,partition):
        return partition, Operator.SEQUENCE

    print("Invalid Sequence Cut Found (Proven To Not be Possible, So Go Find The Bug!) ")
    return None, None


def check_loop(local_data, global_data, a,b):
    for ot in global_data.related[a] & global_data.related[b]:
        if (not local_data.dfgs[ot][0].get((a,b),0) or not local_data.dfgs[ot][0].get((b,a),0) and
                ot not in get_divergent_types(a,b, local_data.alphabet, global_data)):
            return True
        if (local_data.dfgs[ot][1].get(a,0) or local_data.dfgs[ot][2].get(a,0)) and (local_data.dfgs[ot][1].get(b,0) or local_data.dfgs[ot][2].get(b,0)):
            return True
        if (local_data.dfgs[ot][0].get((a, b), 0) and not local_data.dfgs[ot][2].get(a,0) and not local_data.dfgs[ot][1].get(b,0)
            and ot not in get_divergent_types(a, b, local_data.alphabet, global_data)):
            return True

    return False


def find_cut_loop(local_data, global_data):

    for a in local_data.alphabet:
        for b in local_data.alphabet:
            for ot in get_non_divergent_types(a,b,local_data.alphabet,global_data):
                if not local_data.clos[ot].get((a,b),0) or not local_data.clos[ot].get((b,a),0):
                    return None, None

    edges = [[1 if a==b or check_loop(local_data, global_data, a, b)
              else 0 for a in local_data.alphabet] for b in local_data.alphabet]
    n_components, labels = connected_components(csgraph=csr_matrix(edges), directed=False, return_labels=True)
    partition = [[local_data.alphabet[i] for i in range(0,len(local_data.alphabet)) if labels[i] == n] for n in range(0,n_components)]

    if len(partition) == 1:
        return None, None

    body,redo = set(),set()

    for ot in local_data.object_types:
        if not any(ot in global_data.related[a] and ot not in global_data.divergence[a] for a in local_data.alphabet):
            continue

        i = 0
        for i in range(0,n_components):
            if any(local_data.dfgs[ot][1].get(a,0) or local_data.dfgs[ot][2].get(a,0) for a in partition[i]):
                body = partition[i]
                break

        for j in range(0,n_components):
            if i != j and any([ot in global_data.related[a] for a in partition[j]]):
                redo = sum([partition[k] for k in range(0,n_components) if k != i],[])

                if is_loop_cut_valid(local_data, global_data, [body,redo]):
                    return [body,redo], Operator.LOOP

                print("Invalid Loop Cut Found (Proven To Not be Possible, So Go Find The Bug!) ")
                return None, None

