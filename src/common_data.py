from auxillary_methods import *
from follows_relations import *
from interaction_patterns import *


class LocalData:

    def __init__(self, oc_log_list):
        self.oc_log_list = oc_log_list
        self.alphabet = list(set(sum([list(log["ocel:activity"].unique()) for log in oc_log_list],[])))
        self.object_types = list(set(sum([list(log["ocel:type"].unique()) for log in oc_log_list],[])))
        self.object_set = list(set(sum([list(log["ocel:oid"].unique()) for log in oc_log_list],[])))
        self.dfgs = get_cummulative_directly_follows_relation(oc_log_list)
        self.clos = get_transitive_closure_follows_relation(oc_log_list)


class GlobalData:

    def __init__(self, oc_log_list):
        self.oc_log_list = oc_log_list
        start = time.time()
        div, con, rel, defi = get_interaction_patterns(oc_log_list)
        print(rel)
        property_time = time.time()-start
        self.object_set = list(set(sum([list(log["ocel:oid"].unique()) for log in oc_log_list],[])))
        self.divergence = div
        self.convergence = con
        self.related = rel

        self.deficiency = defi
        self.runtime_info = {"properties":[property_time],"cuts":[],"fallthroughs":[],"taus":[],"splits":[]}