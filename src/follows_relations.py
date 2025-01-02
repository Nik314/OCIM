import pm4py
import networkx


def get_transitive_closure_follows_relation(relation_frames):

    result = {}
    object_types = set(sum([list(frame["ocel:type"].unique()) for frame in relation_frames],[]))
    activities = list(set(sum([list(frame["ocel:activity"].unique()) for frame in relation_frames],[])))

    for ot in object_types:
        sub_frames = [frame[frame["ocel:type"] == ot] for frame in relation_frames]
        dfgs = [pm4py.discover_directly_follows_graph(sub_frame, "ocel:activity", "ocel:timestamp", "ocel:oid") for sub_frame in sub_frames]
        dfg = {(a,b):sum([graph[0].get((a,b),0) for graph in dfgs]) for a in activities for b in activities}

        edges =[(activities.index(key[0]), activities.index(key[1])) for key, value in dfg.items() if value]
        closure_edges = networkx.transitive_closure( networkx.DiGraph(edges), reflexive=False).edges()
        result[ot] = {(activities[edge[0]],activities[edge[1]]): 1 for edge in closure_edges}

    return result


def get_cummulative_directly_follows_relation(relation_frames):

    result = {}
    object_types = set(sum([list(frame["ocel:type"].unique()) for frame in relation_frames],[]))
    activities = set(sum([list(frame["ocel:activity"].unique()) for frame in relation_frames],[]))

    for ot in object_types:
        sub_frames = [frame[frame["ocel:type"] == ot] for frame in relation_frames]
        dfgs = [pm4py.discover_directly_follows_graph(sub_frame, "ocel:activity", "ocel:timestamp", "ocel:oid") for sub_frame in sub_frames]
        dfg = {(a,b):sum([graph[0].get((a,b),0) for graph in dfgs]) for a in activities for b in activities}
        start = {a:sum([graph[1].get(a,0) for graph in dfgs]) for a in activities}
        end = {a:sum([graph[2].get(a,0) for graph in dfgs]) for a in activities}
        result[ot] = dfg, start, end

    return result

def get_graph_structures(relations, div):

    object_type = relations["ocel:type"].unique()
    directly_follows_graph, divergence_free_graph, eventually_follows_graph = {}, {}, {}
    for ot in object_type:
        sub_log = relations[relations["ocel:type"] == ot]
        dfg = pm4py.discover_directly_follows_graph(sub_log,"ocel:activity","ocel:timestamp","ocel:oid")
        efg = pm4py.discover_eventually_follows_graph(sub_log,"ocel:activity","ocel:timestamp","ocel:oid")
        directly_follows_graph[ot] = dfg
        eventually_follows_graph[ot] = efg
        graph, start, end = dfg
        graph = {key:value for key,value in graph.items() if ot not in div[key[0]] or ot not in div[key[1]]}
        start = {key:value for key,value in start.items() if ot not in div[key]}
        end = {key:value for key,value in end.items() if ot not in div[key]}
        divergence_free_graph[ot] = (graph, start, end)

    alphabet = relations["ocel:activity"].unique()

    total_graph = {(a,b):sum([divergence_free_graph[ot][0].get((a,b),0) for ot in object_type]) for a in alphabet for b in alphabet}
    total_graph = {key:value for key,value in total_graph.items() if value}
    return directly_follows_graph, divergence_free_graph, eventually_follows_graph, total_graph
