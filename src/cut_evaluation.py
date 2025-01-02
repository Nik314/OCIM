from auxillary_methods import *



def evaluate_concurrent(relations, partition_list, dfgs, clos, rel, div):

    precision_violation = 0
    precision_correct = 0
    violation_list = []

    for i in range(0,len(partition_list)):
        local_start = get_projected_start(relations, partition_list[i])
        local_end = get_projected_end(relations, partition_list[i])
        for ot in dfgs.keys():
            dfg, start, end = dfgs[ot]
            dfg = {key:value for key,value in dfg.items() if value}
            start = {key:value for key,value in start.items() if value}
            end = {key:value for key,value in end.items() if value}

            #skip the check if the object type is not related
            #to the partition part with index i at all
            if all(ot not in rel[a] for a in partition_list[i]):
                continue

            for j in range(0,len(partition_list)):

                # skip the check if the object type is not related
                # to the partition part with index j at all
                if all(ot not in rel[a] for a in partition_list[j]):
                    continue

                #check for fully connectivity if the object type is shared between
                #two activities that are in different partition parts
                #this full connectivity does not care about divergence or not
                if i >= j: continue
                for a in partition_list[i]:
                    for b in partition_list[j]:
                        if ot in rel[a] and ot in rel[b]:
                            if (a, b) not in dfg:
                                precision_violation += 1
                                violation_list.append(("prec", ot, a, b))
                            else:
                                precision_correct += 1
                            if (b, a) not in dfg:
                                precision_violation += 1
                                violation_list.append(("prec", ot, b, a))
                            else:
                                precision_correct += 1


            #check if an object type is fully divergent in
            #the partition with the index i
            if not all(ot not in rel[a] or ot in div[a] for a in partition_list[i]):

                #if the object type is not fully divergent,
                #all start and ends of the partition must
                #also be start and ends of the log here
                for a in partition_list[i]:
                    if a in local_start and a not in start:
                        precision_violation += 1
                        violation_list.append(("prec", ot, "start", a))
                    else:
                        precision_correct += 1
                    if a in local_end and a not in end:
                        precision_violation += 1
                        violation_list.append(("prec", ot, a, "end"))
                    else:
                        precision_correct += 1

    return precision_violation / (precision_correct + precision_violation), 0.00, violation_list


def evaluate_xor(relations, partition_list, dfgs, clos, rel, div):

    fitness_violation = 0
    fitness_correct = 0
    precision_violation = 0
    precision_correct = 0
    violation_list = []

    for i in range(0,len(partition_list)):

        local_start = get_projected_start(relations, partition_list[i])
        local_end = get_projected_end(relations, partition_list[i])

        for ot in dfgs.keys():
            dfg, start, end = dfgs[ot]
            dfg = {key:value for key,value in dfg.items() if value}
            start = {key:value for key,value in start.items() if value}
            end = {key:value for key,value in end.items() if value}

            # skip the check if the object type is not related
            # to the partition part with index i at all
            if all(ot not in rel[a] for a in partition_list[i]):
                continue

            for j in range(0, len(partition_list)):

                # skip the check if the object type is not related
                # to the partition part with index j at all
                if all(ot not in rel[a] for a in partition_list[j]):
                    continue

                if i >= j: continue
                for a in partition_list[i]:
                    for b in partition_list[j]:
                        if ot in rel[a] and ot in rel[b]:

                            # check for fully connectivity if the object type is shared between
                            # two activities that are in different fully divergent partition parts
                            if all([ot not in rel[c] or ot in div[c] for c in partition_list[i] + partition_list[j]]):
                                if not (a, b) in dfg:
                                    precision_violation += 1
                                    violation_list.append(("prec",ot,a,b))
                                else:
                                    precision_correct += 1
                                if not (b, a) in dfg:
                                    precision_violation += 1
                                    violation_list.append(("prec",ot,b,a))
                                else:
                                    precision_correct += 1

                            # if the object type does not diverge on two partition parts,
                            # no connection should be visible between them
                            else:
                                if (a, b) in dfg:
                                    fitness_violation += 1
                                    violation_list.append(("fit",ot,a,b))
                                else:
                                    fitness_correct += 1
                                if (b, a) in dfg:
                                    fitness_violation+= 1
                                    violation_list.append(("fit",ot,b,a))
                                else:
                                    fitness_correct += 1

            #check if an object type is fully divergent in
            #the partition with the index i
            if not all(ot not in rel[a] or ot in div[a] for a in partition_list[i]):

                #if the object type is not fully divergent,
                #all start and ends of the partition must
                #also be start and ends of the log here
                for a in partition_list[i]:
                    if a in local_start and a not in start:
                        precision_violation += 1
                        violation_list.append(("prec", ot, "start", a))
                    else:
                        precision_correct += 1
                    if a in local_end and a not in end:
                        precision_violation += 1
                        violation_list.append(("prec", ot, a, "end"))
                    else:
                        precision_correct += 1

    return (precision_violation /(precision_correct + precision_violation),
            fitness_violation / (fitness_correct + fitness_violation), violation_list)


def evaluate_sequence(relations, partition_list, dfgs, clos, rel, div):

    fitness_violation = 0
    fitness_correct = 0
    precision_violation = 0
    precision_correct = 0

    violation_list = []

    for ot in dfgs.keys():
        dfg, _, __ = dfgs[ot]
        dfg = {key: value for key, value in dfg.items() if value}
        clo = clos[ot]
        clo = {key: value for key, value in clo.items() if value}

        for i in range(0, len(partition_list)):
            # skip the check if the object type is not related
            # to the partition part with index i at all
            if all(ot not in rel[a] for a in partition_list[i]):
                continue

            for j in range(0, len(partition_list)):

                # skip the check if the object type is not related
                # to the partition part with index j at all
                if all(ot not in rel[a] for a in partition_list[j]):
                    continue


                if i >= j: continue
                for a in partition_list[i]:
                    for b in partition_list[j]:
                        if ot in rel[a] and ot in rel[b]:

                            # check for fully connectivity if the object type is shared between
                            # two activities that are in different fully divergent partition parts
                            # inside the same region, i.e. without interruptions in between
                            if all([ot not in rel[c] or ot in div[c] for c in sum([partition_list[k] for k in range(i,j+1)],[])]):
                                if not (a, b) in dfg:
                                    precision_violation += 1
                                    violation_list.append(("prec",ot,a,b))
                                else:
                                    precision_correct += 1
                                if not (b, a) in dfg:
                                    precision_violation += 1
                                    violation_list.append(("prec",ot,b,a))
                                else:
                                    precision_correct += 1

                            #check for non-divergent object types if any order of events
                            #violates the opertor nodes restrictions
                            else:
                                if (a,b) not in clo:
                                    precision_violation += 1
                                    violation_list.append(("prec",ot,a,b))
                                else:
                                    precision_correct += 1
                                if (b,a) in clo:
                                    fitness_violation += 1
                                    violation_list.append(("fit",ot,b,a))
                                else:
                                    fitness_correct += 1

    return (precision_violation /(precision_correct + precision_violation),
            fitness_violation / (fitness_correct + fitness_violation), violation_list)

