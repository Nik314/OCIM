from jedi.inference.gradual.annotation import infer_return_for_callable

from oc_process_trees import OperatorNode,LeafNode,Operator
import pm4py
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.objects.petri_net.utils.networkx_graph import create_networkx_directed_graph_ret_dict_both_ways
from pm4py.objects.petri_net.utils.petri_utils import add_arc_from_to
from pm4py.objects.petri_net.utils.petri_utils import remove_place, remove_transition
from pm4py.objects.petri_net.obj import PetriNet
from ocpa.algo.util.util import project_log, project_log_with_object_count
from ocpa.objects.oc_petri_net.obj import ObjectCentricPetriNet
from ocpa.objects.log.importer.csv.util import succint_mdl_to_exploded_mdl, clean_frequency, clean_arc_frequency, \
    clean_normalized_frequency
import pandas as pd
import time
import networkx as nx
import uuid

from pm4py.objects.process_tree.obj import ProcessTree



def project_ocpt(ocpt,object_type):

    if isinstance(ocpt,LeafNode):
        return ProcessTree(label=ocpt.activity)

    assert isinstance(ocpt,OperatorNode)
    activities = ocpt.get_activities()
    type_dict = ocpt.get_type_information()

    related_activities = set([a for a in activities if object_type in type_dict[(a,"rel")]])
    if all(object_type in type_dict[(a,"div")] for a in related_activities):
        return ProcessTree(operator=pm4py.objects.process_tree.obj.Operator.LOOP,
            children=[ProcessTree(),ProcessTree(operator=pm4py.objects.process_tree.obj.Operator.XOR,children=
            [ProcessTree(label=a) for a in related_activities])])

    else:
        if ocpt.operator == Operator.PARALLEL or ocpt.operator == Operator.LOOP:
            return ProcessTree(operator=ocpt.operator,children=[project_ocpt(sub,object_type) for sub in ocpt.subtrees])

        diverging = [i for i in range(len(ocpt.subtrees)) if ocpt.subtrees[i].get_activities() & related_activities and all(
                    object_type in type_dict[(a,"div")] for a in ocpt.subtrees[i].get_activities() & related_activities) ]
        non_diverging = [i for i in range(len(ocpt.subtrees)) if ocpt.subtrees[i].get_activities() & related_activities and
                         i not in diverging]

        if ocpt.operator == Operator.SEQUENCE:

            children, index = [],0

            while index < len(ocpt.subtrees):

                if index in diverging:

                    div_activities = ocpt.subtrees[index].get_activities()
                    while index+1 in diverging and index+1 < len(ocpt.subtrees):
                        index += 1
                        div_activities |= ocpt.subtrees[index].get_activities()

                    div_subtree = ProcessTree(operator=pm4py.objects.process_tree.obj.Operator.LOOP,
                          children=[ProcessTree(),
                                    ProcessTree(
                                        operator=pm4py.objects.process_tree.obj.Operator.XOR,
                                        children=
                                        [ProcessTree(label=a) for a in div_activities])])
                    children.append(div_subtree)

                else:
                    children.append(project_ocpt(ocpt.subtrees[index],object_type))
                index += 1
                return ProcessTree(operator=Operator.SEQUENCE,children=children)

        if ocpt.operator == Operator.XOR:

            div_activities = [ocpt.subtrees[i].get_activities() & related_activities for i in diverging]
            div_subtree = ProcessTree(operator=pm4py.objects.process_tree.obj.Operator.LOOP,
                        children=[ProcessTree(),
                                  ProcessTree(operator=pm4py.objects.process_tree.obj.Operator.XOR, children=
                                  [ProcessTree(label=a) for a in div_activities])])
            return ProcessTree(operator=Operator.XOR,children=[div_subtree] +
                [project_ocpt(ocpt.subtrees[i],object_type) for i in non_diverging])


def convert_ocpt_to_ocpn(ocpt,log):

    assert isinstance(ocpt,Operator) or isinstance(ocpt,LeafNode)

    nets = {}
    object_count_persp = {}

    for ot in ocpt.get_object_types():
        nets[ot] = pm4py.convert_to_petri_net(project_ocpt(ocpt,ot))
        object_count_persp[ot] = project_log_with_object_count(log, ot)

    places = []
    transitions = []
    arcs = []
    place_mapping = {}
    transition_mapping = {}
    arc_mapping = {}
    for index, persp in enumerate(nets):
        net, im, fm = nets[persp]
        pl_count = 1
        object_count = object_count_persp[persp]
        for pl in net.places:
            p_name = "%s%d" % (persp, pl_count)
            pl_count += 1
            if pl in im:
                p = ObjectCentricPetriNet.Place(name=p_name,
                                                object_type=persp, initial=True)
            elif pl in fm:
                p = ObjectCentricPetriNet.Place(
                    name=p_name, object_type=persp, final=True)
            else:
                p = ObjectCentricPetriNet.Place(
                    name=p_name, object_type=persp)
            place_mapping[pl] = p
            places.append(p)

        for tr in net.transitions:
            t = None
            for _, new_t in transition_mapping.items():
                if tr.label == new_t.label:
                    t = new_t
            if t is None:
                this_uuid = str(uuid.uuid4())
                if tr.label != "" and tr.label != None:
                    t = ObjectCentricPetriNet.Transition(
                        name=this_uuid, label=tr.label)
                else:
                    t = ObjectCentricPetriNet.Transition(
                        name=this_uuid, label=this_uuid, silent=True)
                transitions.append(t)
            transition_mapping[tr] = t

        for arc in net.arcs:
            if type(arc.source) == PetriNet.Transition:
                t = transition_mapping[arc.source]
                p = place_mapping[arc.target]
                if arc.source.label in object_count and sum(object_count[arc.source.label]) != len(
                        object_count[arc.source.label]):
                    a = ObjectCentricPetriNet.Arc(t, p, variable=True)
                else:
                    a = ObjectCentricPetriNet.Arc(t, p)
                p.in_arcs.add(a)
                t.out_arcs.add(a)
                arcs.append(a)
            else:
                t = transition_mapping[arc.target]
                p = place_mapping[arc.source]
                if arc.target.label in object_count and sum(object_count[arc.target.label]) != len(
                        object_count[arc.target.label]):
                    a = ObjectCentricPetriNet.Arc(p, t, variable=True)
                else:
                    a = ObjectCentricPetriNet.Arc(p, t)

                p.out_arcs.add(a)
                t.in_arcs.add(a)
                arcs.append(a)
            arc_mapping[arc] = a
    ocpn = ObjectCentricPetriNet(
        places=set(places), transitions=set(transitions), arcs=set(arcs), nets=nets, place_mapping=place_mapping,
        transition_mapping=transition_mapping, arc_mapping=arc_mapping)
    return ocpn