import copy
import rustworkx
import hashlib
import multiprocessing
import numpy
from multiset import Multiset
from itertools import chain, combinations, product


class State:
    def __init__(self,sequence,marking):
        self.sequence = sequence
        self.marking = marking


    def get_state_hash(self,all_types):

        object_history = {ot: {oid: tuple() for transition, objects in
            self.sequence for oid in objects.get(ot, [])} for ot in all_types}

        for transition, all_objects in self.sequence:
            for ot, typed_objects in all_objects.items():
                for oid in typed_objects:
                    if not transition.silent:
                        object_history[ot][oid] = *object_history[ot][oid], transition.label

        marking_with_history = {place: Multiset(object_history[place.object_type].get(oid,tuple()) for oid in tokens)
                        for place,tokens in self.marking.items()}

        hash_string = str(list(sorted([(str(place),trace,counter) for place,value in marking_with_history.items()
                                       for trace,counter in value.items()])))
        return int(hashlib.md5(hash_string.encode("utf_8")).hexdigest(), 16)


    def get_state_context(self, all_types, buffer=1):

        object_history = {ot: {oid: tuple() for transition, objects in
                               self.sequence for oid in objects.get(ot, [])} for ot in all_types}

        for transition, all_objects in self.sequence[:-1]:
            for ot, typed_objects in all_objects.items():
                for oid in typed_objects:
                    if not transition.silent:
                        object_history[ot][oid] = *object_history[ot][oid], transition.label

        return  {ot:Multiset(trace for trace in object_history[ot].values()) for ot in all_types}


def hash_context(context):
    hash_string = str(list(sorted([(ot,trace,context[ot][trace]) for ot in context.keys() for trace in context[ot]])))
    return int(hashlib.md5(hash_string.encode("utf_8")).hexdigest(), 16)

def hash_cardinality(cardinality):
    hash_string = str(list(sorted([(key,value) for key,value in cardinality.items()])))
    return int(hashlib.md5(hash_string.encode("utf_8")).hexdigest(), 16)

def determine_log_context(relations):

    graph = rustworkx.PyDiGraph(multigraph=False)
    events = list(relations["ocel:eid"].unique())
    index = {events[i]:i for i in graph.add_nodes_from(events)}
    relations["ocel:eid"] = relations["ocel:eid"].apply(lambda eid:index[eid])
    activities = relations.drop_duplicates("ocel:eid").set_index("ocel:eid")["ocel:activity"].to_dict()
    types = relations.drop_duplicates("ocel:oid").set_index("ocel:oid")["ocel:type"].to_dict()

    relations.groupby("ocel:oid").apply(lambda frame:graph.add_edges_from_no_data(
        zip(frame["ocel:eid"].values[:-1],frame["ocel:eid"].values[1:]) if len(frame["ocel:eid"].values) > 1 else []))

    event_to_context_mapping = {}
    context_hash_to_activity_mapping = {}
    unique_context_list = []
    context_hash_to_event_mapping = {}

    for event in graph.nodes():

        ancestors = rustworkx.ancestors(graph,index[event])
        sub_relations = relations[relations["ocel:eid"].isin(ancestors)]
        context = {ot: Multiset() for ot in relations["ocel:type"].unique()}
        if sub_relations.shape[0]:
            traces = sub_relations.groupby("ocel:oid").apply(lambda frame:tuple(activities[e] for e in frame["ocel:eid"].values))
            for oid,trace in traces.items():
                context[types[oid]].add(trace)

        additional_objects = relations[relations["ocel:eid"] == index[event]]["ocel:oid"].unique()
        for oid in additional_objects:
            if oid not in sub_relations["ocel:oid"].unique():
                context[types[oid]].add(tuple())

        hash_value = hash_context(context)
        if hash_value in context_hash_to_activity_mapping:
            context_hash_to_activity_mapping[hash_value].append(activities[index[event]])
        else:
            context_hash_to_activity_mapping[hash_value] = [activities[index[event]]]
            unique_context_list.append(context)
        if hash_value in context_hash_to_event_mapping:
            context_hash_to_event_mapping[hash_value].append(index[event])
        else:
            context_hash_to_event_mapping[hash_value] = [index[event]]

        event_to_context_mapping[index[event]] = context
        print("Progress On Log Context: ",len(event_to_context_mapping) / len(graph.nodes()))

    context_hash_to_activity_mapping = {key:set(value) for key,value in context_hash_to_activity_mapping.items()}
    return context_hash_to_activity_mapping, event_to_context_mapping, unique_context_list, context_hash_to_event_mapping


def get_unique_start_marking(unique_context_list):

    unique_cardinalities = {}
    cardinality_hash_context_mapping = {}

    for context in unique_context_list:
        cardinality = {ot:0 for ot in context.keys()}
        for ot, trace_multi_set in context.items():
            for trace, multiplicity in trace_multi_set.items():
                cardinality[ot] += multiplicity
        hash_value = hash_cardinality(cardinality)
        if not hash_value in unique_cardinalities:
            unique_cardinalities[hash_value] = cardinality

        if hash_value in cardinality_hash_context_mapping:
            cardinality_hash_context_mapping[hash_value].append(context)
        else:
            cardinality_hash_context_mapping[hash_value] = [context]

    return unique_cardinalities,cardinality_hash_context_mapping


def get_enabled_transitions(transitions, places, arcs, state):

    results = []
    for t in transitions:
        normal_input_places = [arc.source for arc in arcs if arc.target == t and arc.variable == False]
        variable_input_places = [arc.source for arc in arcs if arc.target == t and arc.variable == True]
        object_types = [p.object_type for p in normal_input_places+variable_input_places]
        sorted_places = {ot:[p for p in normal_input_places+variable_input_places if p.object_type == ot] for ot in object_types}
        place_sets = {ot:[state.marking[p] for p in sorted_places[ot]] for ot in sorted_places.keys()}
        available_tokens = {ot:place_sets[ot][0].intersection(*place_sets[ot][1:]) for ot in place_sets.keys()}
        variable_types = {p.object_type for p in variable_input_places}

        if all(available_tokens[ot] for ot in available_tokens.keys()):

            available_subsets = {ot:[[token] for token in available_tokens[ot]]
                if ot not in variable_types else list(chain.from_iterable(combinations(available_tokens[ot], r)
                for r in range(len(available_tokens[ot]) + 1))) for ot in available_tokens.keys()}
            ot_list = list(available_tokens.keys())
            index_combinations = product(*[range(len(available_subsets[ot]))for ot in ot_list])

            results += [(t,{ot_list[i]: [j for j in available_subsets[ot_list[i]][combi[i]]] for i in range(len(ot_list))})
                for combi in index_combinations]

    return results



def fire_enabled_transition(transitions, places, arcs, state, transition, objects):

    objects = {key:set(value) for key,value in objects.items()}
    input_places = [arc.source for arc in arcs if arc.target == transition]
    output_places = [arc.target for arc in arcs if arc.source == transition]

    new_marking = {p:copy.deepcopy(state.marking[p]) for p in state.marking.keys()}
    for p in input_places:
        for oid in objects[p.object_type]:
            new_marking[p].remove(oid)

    for p in output_places:
        for oid in objects[p.object_type]:
            new_marking[p].add(oid)

    return State(state.sequence +[(transition,objects)],new_marking)



def adapt_result_for_match(state, contained_contexts, result, all_types):
    for context in contained_contexts:
        if hash_context(state.get_state_context(all_types)) == hash_context(context):
            if not state.sequence[-1][0].silent:
                result[hash_context(context)].add(state.sequence[-1][0].label)




def check_context_reachable(context, state_context):

    for ot in state_context.keys():
        for partial_trace in state_context[ot].keys():
            check = False
            for full_trace in context[ot].keys():
                if len(full_trace) >= len(partial_trace) and all(full_trace[i] == partial_trace[i] for i in range(len(partial_trace))):
                    check = True
                    break
            if not check:
                return False

    return True


def replay_single_cardinality(ocpn, contained_contexts, cardinality, log_enabled_activities, event_size):

    transitions, arcs, places = ocpn.transitions, ocpn.arcs, ocpn.places
    visited_information = []
    start_model_marking = {p:set() if not p.initial else set(list(range(0,cardinality[p.object_type]))) for p in places}
    start_model_state = State([], start_model_marking)

    state_queue = [start_model_state]
    context_hash_to_enabled_activities = {hash_context(c):set() for c in contained_contexts}
    all_types = {p.object_type for p in places}

    while state_queue:

        current_state = state_queue[0]
        adapt_result_for_match(current_state,contained_contexts,context_hash_to_enabled_activities,all_types)

        if (current_state.get_state_hash(all_types) in visited_information or not
                any(check_context_reachable(context,current_state.get_state_context(all_types)) for context in contained_contexts)):
            state_queue.remove(current_state)
            del current_state
            continue

        if len(visited_information) >= (event_size*1000000):
            break

        state_queue += [fire_enabled_transition(transitions,places,arcs,current_state,transition,objects)
            for transition,objects in get_enabled_transitions(transitions,places,arcs,current_state)]
        state_queue.remove(current_state)
        visited_information.append(current_state.get_state_hash(all_types))
        del current_state

    timed_contexts = set()
    if state_queue:
        for context in contained_contexts:
            for state in state_queue:
                if check_context_reachable(context,state.get_state_context(all_types)):
                    timed_contexts.add(hash_context(context))
                    break

    hash_to_conformance = {}
    for context in contained_contexts:
        key = hash_context(context)

        if key in timed_contexts:
            hash_to_conformance[key] = "Timed","Timed"
        else:
            model_enabled = context_hash_to_enabled_activities[key]
            log_enabled = log_enabled_activities[key]
            local_fitness = len(set(model_enabled) & set(log_enabled)) / len(log_enabled) if model_enabled else 0
            local_precision = len(set(model_enabled) & set(log_enabled)) / len(model_enabled) if model_enabled else 1
            hash_to_conformance[key] = local_fitness,local_precision
            if local_fitness != 1:
                print("Lacking Model Fitness")

    print("Cardinality Done")
    return hash_to_conformance


def determine_conformance(ocpn, relations):

    (hash_to_activity_map, event_to_context_map,
        unique_context_list, context_hash_to_event_mapping) = determine_log_context(relations)
    unique_cardinalities, cardinality_hash_context_map = get_unique_start_marking(unique_context_list)
    hash_to_conformance = {}
    print("Log Context Done")
    print("Model Context Distribution Running On: ",len(unique_cardinalities))

    inputs = [(copy.deepcopy(ocpn),cardinality_hash_context_map[hash_value],
            cardinality, copy.deepcopy({hash_context(context): hash_to_activity_map[hash_context(context)]
            for context in cardinality_hash_context_map[hash_value]}), sum(len(context_hash_to_event_mapping[hash_context(context)])
            for context in cardinality_hash_context_map[hash_value]) / len(event_to_context_map.keys()))
            for hash_value, cardinality in unique_cardinalities.items()]

    result = multiprocessing.Pool(3).starmap(replay_single_cardinality, inputs)
    for entry in result:
        hash_to_conformance.update(entry)

    total_fitness = [hash_to_conformance[hash_context(context)][0] for context in event_to_context_map.values() if
                     hash_to_conformance[hash_context(context)][0] != "Timed"]
    total_precision = [hash_to_conformance[hash_context(context)][1] for context in event_to_context_map.values() if
                       hash_to_conformance[hash_context(context)][1] != "Timed"]
    total_timed = [1 for context in event_to_context_map.values()
                   if hash_to_conformance[hash_context(context)][1] == "Timed"]

    print(numpy.mean(total_fitness),numpy.mean(total_precision),len(total_timed)/len(event_to_context_map.keys()))
    return numpy.mean(total_fitness),numpy.mean(total_precision),len(total_timed)/len(event_to_context_map.keys())


