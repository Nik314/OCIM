import pm4py

from conformance.interaction_properties import get_interaction_patterns

def get_log_abstraction(relations):

    div,con,rel,defi = get_interaction_patterns(relations)
    opt = {a:[ot for ot in rel[a] if relations[relations["ocel:type"]==ot]["ocel:oid"].nunique()
        > relations[(relations["ocel:type"]==ot) & (relations["ocel:activity"]==a)]["ocel:oid"].nunique()] for a in relations["ocel:activity"].unique()}
    print("Log Interaction Properties Done")
    dfgs = {ot:pm4py.discover_dfg(relations[relations["ocel:type"] == ot],
        activity_key="ocel:activity",timestamp_key="ocel:timestamp",case_id_key="ocel:oid")   for ot in relations["ocel:type"].unique()}
    print("Log Follows Relations Done")
    return dfgs,rel,div,con,defi,opt