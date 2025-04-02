import pprint
import time

from matplotlib.rcsetup import validate_int
from pm4py.objects.process_tree.utils import generic as pt_util
from oc_process_trees import OperatorNode,LeafNode
import pm4py
from pm4py.objects.petri_net.obj import PetriNet
from ocpa.objects.oc_petri_net.obj import ObjectCentricPetriNet
import uuid
from pm4py.objects.process_tree.obj import ProcessTree,Operator



def project_ocpt(ocpt,object_type):



    if isinstance(ocpt,LeafNode):
        if ocpt.activity == "" or object_type not in ocpt.related:
            return ProcessTree()
        return ProcessTree(label=ocpt.activity)

    assert isinstance(ocpt,OperatorNode)
    related_activities = set([a for a in ocpt.get_activities()
        if object_type in ocpt.get_type_information()[(a,"rel")] and a != ""])

    if not related_activities:
        return ProcessTree()

    if all(object_type in ocpt.get_type_information()[(a,"div")] for a in related_activities):
        return ProcessTree(operator=pm4py.objects.process_tree.obj.Operator.LOOP,
            children=[ProcessTree(),ProcessTree(operator=pm4py.objects.process_tree.obj.Operator.XOR,children=
            [ProcessTree(label=a) for a in related_activities])])

    else:
        if ocpt.operator == Operator.PARALLEL or ocpt.operator == Operator.LOOP:
            return ProcessTree(operator=ocpt.operator,children=[project_ocpt(sub,object_type) for sub in ocpt.subtrees])

        diverging = [i for i in range(len(ocpt.subtrees)) if ocpt.subtrees[i].get_activities() & related_activities
            and all(object_type in ocpt.get_type_information()[(a,"div")]
                    for a in ocpt.subtrees[i].get_activities() & related_activities)]
        non_diverging = [i for i in range(len(ocpt.subtrees)) if ocpt.subtrees[i].get_activities()
            & related_activities and i not in diverging]
        skipped = [i for i in range(0,len(ocpt.subtrees)) if i not in diverging and i not in non_diverging]

        if ocpt.operator == Operator.SEQUENCE:

            children, index = [],0

            while index < len(ocpt.subtrees):

                if index in diverging:

                    div_activities = ocpt.subtrees[index].get_activities() & related_activities
                    while index+1 in diverging and index+1 < len(ocpt.subtrees):
                        index += 1
                        if index not in skipped:
                            div_activities |= ocpt.subtrees[index].get_activities() & related_activities

                    div_activities = {a for a in div_activities if a != ""}
                    div_subtree = ProcessTree(operator=pm4py.objects.process_tree.obj.Operator.LOOP,
                          children=[ProcessTree(),
                                    ProcessTree(
                                        operator=pm4py.objects.process_tree.obj.Operator.XOR,
                                        children=[ProcessTree(label=a) for a in div_activities])])
                    children.append(div_subtree)

                else:
                    children.append(project_ocpt(ocpt.subtrees[index],object_type))
                index += 1
            return ProcessTree(operator=Operator.SEQUENCE,children=children)

        if ocpt.operator == Operator.XOR:

            div_activities = set(sum([list(ocpt.subtrees[i].get_activities() & related_activities) for i in diverging],[]))
            div_activities = {a for a in div_activities if a != ""}
            optional = any([isinstance(sub,LeafNode) and sub.activity == "" and object_type in sub.related for sub in ocpt.subtrees])

            if div_activities:
                div_subtree = ProcessTree(operator=pm4py.objects.process_tree.obj.Operator.LOOP,
                            children=[ProcessTree(),
                                      ProcessTree(operator=pm4py.objects.process_tree.obj.Operator.XOR, children=
                                      [ProcessTree(label=a) for a in div_activities])])

                return ProcessTree(operator=Operator.XOR,children=[div_subtree] +
                    [project_ocpt(ocpt.subtrees[i],object_type) for i in non_diverging] + ([ProcessTree()] if optional else []))
            else:
                return ProcessTree(operator=Operator.XOR,children=
                    [project_ocpt(ocpt.subtrees[i],object_type) for i in non_diverging] + ([ProcessTree()] if optional else []))



def handle_deficiency(ocpt):

    if isinstance(ocpt,OperatorNode):
        subresults = [handle_deficiency(sub) for sub in ocpt.subtrees]
        return OperatorNode(ocpt.operator,[sub[0] for sub in subresults]),sum([sub[1] for sub in subresults],[])
    elif ocpt.activity == "":
        return ocpt,[]
    else:
        from itertools import combinations, chain
        stable_types = ocpt.related - ocpt.deficient
        variable_types = ocpt.related & ocpt.deficient
        if variable_types:
            ot_sets =  [stable_types | {c for c in comb} for comb in chain.from_iterable(combinations(variable_types,n)
                                    for n in range(len(variable_types)+1))]

            children = [LeafNode(activity=ocpt.activity + "<|>"+str(sorted(list(ots))), related=ots, convergent=ocpt.convergent & ots,
                        deficient= set(), divergent= ocpt.divergent & ots) for ots in ot_sets]
            return OperatorNode(operator=Operator.XOR,subtrees=children), [ocpt.activity]
        else:
            return ocpt,[]



def convert_ocpt_to_ocpn(ocpt):

    assert isinstance(ocpt,OperatorNode) or isinstance(ocpt,LeafNode)

    nets = {}
    convergent_activities = {}
    ocpt, special_activities = handle_deficiency(ocpt)

    for ot in ocpt.get_object_types():
        pt = project_ocpt(ocpt,ot)
        pt = pt_util.reduce_tau_leafs(pt)
        pt = pt_util.fold(pt)
        nets[ot] = pm4py.convert_to_petri_net(pt)
        convergent_activities[ot] = [a for a in ocpt.get_activities() if ot in ocpt.get_type_information()[(a,"con")]]

    places = []
    transitions = []
    arcs = []
    place_mapping = {}
    transition_mapping = {}
    arc_mapping = {}
    for index, persp in enumerate(nets):
        net, im, fm = nets[persp]
        pl_count = 1
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
                if arc.source.label in convergent_activities[persp]:
                    a = ObjectCentricPetriNet.Arc(t, p, variable=True)
                else:
                    a = ObjectCentricPetriNet.Arc(t, p)
                p.in_arcs.add(a)
                t.out_arcs.add(a)
                arcs.append(a)
            else:
                t = transition_mapping[arc.target]
                p = place_mapping[arc.source]
                if arc.target.label in convergent_activities[persp]:
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
    return ocpn, special_activities