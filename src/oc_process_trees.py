from enum import Enum
from itertools import chain, combinations

class Direction(Enum):

    ToTransition = 0
    ToPlace = 1

class Place:

    def __init__(self,object_type, start, end):
        self.object_type = object_type
        self.start = start
        self.end = end

class Transition:

    def __init__(self, label, object_types):
        self.label = label
        self.object_types = object_types

class Arc:
    def __init__(self, place, transition, variable, direction):
        self.place = place
        self.transition = transition
        self.variable = variable
        self.direction = direction


class Operator(Enum):

    Sequence = "->"
    Concurrent = "||"
    Exclusive = "X"
    Loop = "O^"


class LeafNode:


    def __init__(self, activity, related, divergent, convergent, deficient):
        self.activity = activity
        self.related = related
        self.divergent = divergent
        self.convergent = convergent
        self.deficient = deficient


    def __str__(self, depth = 0):
        indent = ""
        for i in range(0, depth):
            indent += "\t"

        result = indent + self.activity + "\n"
        result += indent + "\t Related Types: " + str(self.related) +"\n"
        result += indent + "\t Divergent Types: " + str(self.divergent) +"\n"
        result += indent + "\t Convergent Types: " + str(self.convergent) +"\n"
        result += indent + "\t Deficient Types: " + str(self.deficient) +"\n"
        return result

    def get_type_information(self):
        return {(self.activity,"rel"):self.related, (self.activity,"div"):self.divergent,
                (self.activity,"con"):self.convergent, (self.activity,"def"):self.deficient}

    def get_object_types(self):
        return set(sum([list(value) for value in self.get_type_information().values()],[]))


    def project(self,object_type):
        typesets = chain.from_iterable(combinations(self.deficient, r) for r in range(len(self.deficient) + 1))
        baseline = set([ot for ot in self.related if ot not in self.deficient])
        typesets = [set(combi) | baseline for combi in typesets]
        typesets = [combi for combi in typesets if object_type in combi]

        if self.activity == "tau" or not typesets:
            return [Place(object_type, True, True)], [],[]

        else:

            transitions = [Transition(self.activity, types) for types in typesets]
            if object_type in self.divergent:
                input_output_place = Place(object_type, True, True)
                arcs = [Arc(place=input_output_place,transition = t,variable=object_type
                    in self.convergent, direction=Direction.ToPlace) for t in transitions ]
                arcs += [Arc(place=input_output_place,transition = t,variable=object_type
                    in self.convergent, direction=Direction.ToTransition) for t in transitions]
                return [input_output_place], transitions, arcs
            else:
                input_place = Place(object_type,True,False)
                output_place = Place(object_type,False, True)
                arcs = [Arc(place=input_place,transition = t,variable=object_type
                    in self.convergent, direction=Direction.ToTransition) for t in transitions]
                arcs += [Arc(place=output_place,transition = t,variable=object_type
                    in self.convergent, direction=Direction.ToPlace) for t in transitions ]
                return [input_place,output_place], transitions, arcs


class OperatorNode:

    def __init__(self, operator, subtrees):
        self.operator = operator
        self.subtrees = subtrees


    def __str__(self, depth = 0):
        indent = ""
        for i in range(0,depth):
            indent += "\t"
        result = indent + str(self.operator) + "\n"
        for tree in self.subtrees:
            result += tree.__str__(depth+1)
        return result

    def get_type_information(self):
        return {key:value for subtree in self.subtrees for key,value in subtree.get_type_information().items()}

    def get_object_types(self):
        return set(sum([list(value) for value in self.get_type_information().values()],[]))

    def get_activities(self):
        return set(sum([[key[0]] for key in self.get_type_information().keys()],[]))

    def combine_diverging_subnets(self, subnets, object_type):
        places = [Place(object_type, True, True)]
        transitions = sum([subnet[1] for subnet in subnets], [])
        arcs = [Arc(places[0], t, False, Direction.ToPlace) for t in transitions]
        arcs += [Arc(places[0], t, False, Direction.ToTransition) for t in transitions]
        return places, transitions, arcs

    def combine_related_subnets_xor(self, subnets, object_type):

        if len(subnets) == 1:
            return subnets[0]

        input_place = Place(object_type, True, False)
        output_place = Place(object_type, False, True)
        places, arcs, transitions = [input_place, output_place], [], []

        for sub_net in subnets:
            for place in sub_net[0]:
                places.append(place)
                if place.start:
                    place.start = False
                    tau_transition = Transition("tau", [object_type])
                    arcs.append(Arc(input_place, tau_transition, False, Direction.ToTransition))
                    arcs.append(Arc(place, tau_transition, False, Direction.ToPlace))
                if place.end:
                    place.end = False
                    tau_transition = Transition("tau", [object_type])
                    arcs.append(Arc(output_place, tau_transition, False, Direction.ToPlace))
                    arcs.append(Arc(place, tau_transition, False, Direction.ToTransition))
            arcs += sub_net[2]
            transitions += sub_net[1]

        return places, transitions, arcs

    def combine_related_subnets_concurrent(self, subnets, object_type):

        if len(subnets) == 1:
            return subnets[0]

        input_place = Place(object_type, True, False)
        output_place = Place(object_type, False, True)
        input_transition = Transition("tau",[object_type])
        output_transition = Transition("tau",[object_type])

        places, arcs, transitions = ([input_place, output_place], [input_transition,output_transition],
            [Arc(input_place,input_transition,False,Direction.ToTransition),
             Arc(output_place,output_transition,False,Direction.ToPlace)])

        for sub_net in subnets:
            for place in sub_net[0]:
                places.append(place)
                if place.start:
                    place.start = False
                    arcs.append(Arc(place, input_transition, False, Direction.ToPlace))
                if place.end:
                    place.end = False
                    arcs.append(Arc(place, output_transition, False, Direction.ToTransition))
            arcs += sub_net[2]
            transitions += sub_net[1]

        return places, transitions, arcs


    def combine_related_subnets_sequence(self, subnets, object_type):

        if len(subnets) == 1:
            return subnets[0]

        input_place = Place(object_type, True, False)
        output_place = Place(object_type, False, True)
        places, arcs, transitions = [input_place, output_place], [], []

        start_places = [input_place] + [[p for p in subnet[0] if p.start][0] for subnet in subnets]
        end_places = [[p for p in subnet[0] if p.end][0] for subnet in subnets] + [output_place]
        transitions += [Transition("tau",[object_type]) for _ in range(0,len(start_places))]

        for i in range(len(transitions)):
            arcs.append(Arc(start_places[i],transitions[i],False,Direction.ToTransition))
            arcs.append(Arc(end_places[i],transitions[i],False,Direction.ToPlace))

        for sub_net in subnets:
            for place in sub_net[0]:
                places.append(place)
                if place.start:
                    place.start = False
                if place.end:
                    place.end = False
            arcs += sub_net[2]
            transitions += sub_net[1]

        return places, transitions, arcs

    def project(self, object_type):

        sub_nets = [subtree.project(object_type) for subtree in self.subtrees]
        trivial_subnets = [subnet for subnet in sub_nets if len(subnet[0]) == 1 and len(subnet[1]) == 0]
        divergent_subnets = [subnet for subnet in sub_nets if len(subnet[0]) == 1 and len(subnet[1]) != 0]
        related_subnets = [subnet for subnet in sub_nets if len(subnet[0]) != 1 and len(subnet[1]) != 0]

        if self.operator.value == "||":

            if divergent_subnets:
                places, transitions, arcs = self.combine_diverging_subnets(divergent_subnets, object_type)
                related_subnets.append((places, transitions, arcs))

            if related_subnets:
                return self.combine_related_subnets_concurrent(related_subnets, object_type)
            else:
                return [Place(object_type, True, True)], [], []

        if self.operator.value == "X":

            if divergent_subnets:
                places, transitions, arcs = self.combine_diverging_subnets(divergent_subnets,object_type)
                related_subnets.append((places, transitions, arcs))

            if related_subnets:
                places, transitions, arcs = self.combine_related_subnets_xor(related_subnets,object_type)
                if trivial_subnets and not divergent_subnets:
                    places.append(Place(object_type,False,False))
                    transitions.append(Transition("tau",[object_type]))
                    arcs.append(Arc([p for p in places if p.start][0],transitions[-1],False,Direction.ToTransition))
                    arcs.append(Arc([p for p in places if p.end][0],transitions[-1],False,Direction.ToPlace))
                return places,transitions,arcs
            else:
                return [Place(object_type, True, True)], [], []

        if self.operator.value == "->":

            if divergent_subnets:
                new_subnets, current_nets = [],[]
                for i in range(0,len(sub_nets)):
                    if sub_nets[i] in divergent_subnets:
                        current_nets.append(sub_nets[i])
                    if sub_nets[i] not in divergent_subnets:
                        if current_nets:
                            new_subnets.append(self.combine_diverging_subnets(current_nets,object_type))
                        new_subnets.append(sub_nets[i])

                related_subnets = new_subnets

            if related_subnets:
                return self.combine_related_subnets_sequence(related_subnets, object_type)
            else:
                return [Place(object_type, True, True)], [], []

        if self.operator.value == "O^":

            body_net = sub_nets[0]
            redo_net = sub_nets[1]

            input_place = Place(object_type,True,False)
            output_place = Place(object_type,False,True)
            input_transition = Transition("tau",[object_type])
            output_transition = Transition("tau",[object_type])
            redo_transition = Transition("tau",[object_type])
            reenter_transition = Transition("tau",[object_type])

            places = [input_place,output_place] + body_net[0] + redo_net[0]
            transitions = [input_transition,output_transition,redo_transition,reenter_transition] + body_net[1] + redo_net[1]
            arcs = body_net[2] + redo_net[2] + [
                Arc(input_place,input_transition,False,Direction.ToTransition),
                Arc([p for p in body_net[0] if p.start][0], input_transition, False, Direction.ToPlace),
                Arc([p for p in body_net[0] if p.end][0], output_transition, False, Direction.ToTransition),
                Arc(output_place, output_transition, False, Direction.ToPlace),
                Arc([p for p in body_net[0] if p.end][0], redo_transition, False, Direction.ToTransition),
                Arc([p for p in redo_net[0] if p.start][0], redo_transition, False, Direction.ToPlace),
                Arc([p for p in redo_net[0] if p.end][0], reenter_transition, False, Direction.ToTransition),
                Arc([p for p in body_net[0] if p.start][0], reenter_transition, False, Direction.ToPlace),
            ]

            for p in body_net[0] + redo_net[0]:
                p.start, p.end = False, False

            return places,transitions,arcs


    def convert_ocpn(self):
        perspectives = {ot:self.project(ot) for ot in self.get_object_types()}
        for key,value in perspectives.items():
            print(value)







