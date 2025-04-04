import copy

import rustworkx
import hashlib
from multiset import Multiset
from itertools import chain, combinations, product
import numpy


class State:
    def __init__(self,sequence,marking):
        self.sequence = sequence
        self.marking = marking

    def get_state_context_hash(self):
        pass


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

        event_to_context_mapping[index[event]] = context

    context_hash_to_activity_mapping = {key:set(value) for key,value in context_hash_to_activity_mapping.items()}
    return context_hash_to_activity_mapping, event_to_context_mapping, unique_context_list


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



def check_context_possible(state, contained_contexts):
    #todo check if at least of of the contained contexts can still be reached
    return True

def adapt_result_for_match(state, contained_contexts, result):
    pass



def replay_single_cardinality(transitions, places, arcs, contained_contexts, cardinality):

    start_model_marking = {p:set() if not p.initial else set(list(range(0,cardinality[p.object_type]))) for p in places}
    start_model_state = State([], start_model_marking)
    state_queue = [start_model_state]
    context_hash_to_enabled_activities = {hash_context(c):set() for c in contained_contexts}
    total_states_visited = 0

    while state_queue:

        current_state = state_queue[0]
        print(current_state.marking)
        adapt_result_for_match(current_state,contained_contexts,context_hash_to_enabled_activities)

        possible_next_states = [fire_enabled_transition(transitions,places,arcs,current_state,transition,objects)
            for transition,objects in get_enabled_transitions(transitions,places,arcs,current_state)]

        allowed_next_states = [state for state in possible_next_states if check_context_possible(state,contained_contexts)]
        state_queue += allowed_next_states
        state_queue.remove(current_state)

        print(total_states_visited)
        total_states_visited += 1

    print("Full Run On A Single Cardinality Set :) ")