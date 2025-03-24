import pandas
from cut_definition import *
from oc_process_trees import *


def detect_tau_cases(local_data, global_data):
    if len(local_data.expected_objects) > len(local_data.object_set):

        combined_input = pandas.concat(local_data.oc_log_list)
        combined_original = pandas.concat(global_data.oc_log_list)
        missing_objects = [o for o in local_data.expected_objects
                if o not in combined_input["ocel:oid"].unique()]
        missing_types = combined_original[combined_original["ocel:oid"].isin(missing_objects)]["ocel:type"].unique()
        local_data.expected_objects = local_data.object_set

        if any(ot in combined_input["ocel:type"].unique() for ot in missing_types):
            return [local_data.alphabet, []], Operator.XOR


    for a in local_data.alphabet:
        for b in local_data.alphabet:
            for ot in get_non_divergent_types(a,b,local_data.alphabet,global_data):
                if not local_data.clos[ot].get((a,b),0) or not local_data.clos[ot].get((b,a),0):
                    return None, None

    for ot in local_data.object_types:
        for a in local_data.alphabet:
            for b in local_data.alphabet:
                if local_data.dfgs[ot][2].get(a,0) and local_data.dfgs[ot][1].get(b,0) and not local_data.dfgs[ot][0].get((a,b),0):
                    return None, None

    if not any(ot in global_data.related[a] and ot not in global_data.divergence[a]
           for a in local_data.alphabet for ot in local_data.object_types):
        return None,None

    return [local_data.alphabet, []], Operator.LOOP