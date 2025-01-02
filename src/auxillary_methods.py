import time
import pm4py



def get_non_divergent_types(a, b, context_activities, div, rel):
    return [ot for ot in rel[a] & rel[b] if
        not all(ot not in rel[c] or ot in div[c] for c in context_activities)]


def get_divergent_types(a, b, context_activities, div, rel):
    return [ot for ot in rel[a] & rel[b] if
        all(ot not in rel[c] or ot in div[c] for c in context_activities)]


def get_projected_start(relation_frames, partition_part):
    object_types = set(sum([list(frame["ocel:type"].unique()) for frame in relation_frames],[]))
    filtered_frames = [frame[frame["ocel:activity"].isin(partition_part)] for frame in relation_frames]
    return {ot:sum([list(pm4py.get_start_activities(frame[frame["ocel:type"]==ot],activity_key="ocel:activity",case_id_key="ocel:oid",
        timestamp_key="ocel:timestamp").keys()) for frame in filtered_frames
        if frame[frame["ocel:type"]==ot].shape[0]],[]) for ot in object_types}



def get_projected_end(relation_frames, partition_part):
    start = time.time()
    object_types = set(sum([list(frame["ocel:type"].unique()) for frame in relation_frames],[]))
    filtered_frames = [frame[frame["ocel:activity"].isin(partition_part)] for frame in relation_frames]
    return {ot:sum([list(pm4py.get_end_activities(frame[frame["ocel:type"]==ot],activity_key="ocel:activity",case_id_key="ocel:oid",
        timestamp_key="ocel:timestamp").keys()) for frame in filtered_frames
        if frame[frame["ocel:type"]==ot].shape[0]],[]) for ot in object_types}

