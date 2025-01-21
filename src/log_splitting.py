
from common_data import *



def split_log(local_data, partition, operator):
    return [LocalData([log[log["ocel:activity"].isin(part)] for log in local_data.oc_log_list]) for part in partition]


