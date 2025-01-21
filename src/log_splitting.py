



def split_log(relation, partition):
    return [relation[relation["ocel:activity"].isin(part)] for part in partition]


