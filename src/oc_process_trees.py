from enum import Enum
from itertools import chain, combinations
from pm4py.objects.process_tree.obj import Operator

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

    def get_as_dict(self):
        return {"activity":self.activity,"related":self.related,
                "divergent":self.divergent,"convergent":self.convergent,
        "deficient":self.deficient}

    def get_type_information(self):
        return {(self.activity,"rel"):self.related, (self.activity,"div"):self.divergent,
                (self.activity,"con"):self.convergent, (self.activity,"def"):self.deficient}

    def get_object_types(self):
        return set(sum([list(value) for value in self.get_type_information().values()],[]))


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

    def get_as_dict(self):
        return {"operator":str(self.operator), "subtrees":[subtree.get_as_dict() for subtree in self.subtrees]}

    def get_type_information(self):
        return {key:value for subtree in self.subtrees for key,value in subtree.get_type_information().items()}

    def get_object_types(self):
        return set(sum([list(value) for value in self.get_type_information().values()],[]))

    def get_activities(self):
        return set(sum([[key[0]] for key in self.get_type_information().keys()],[]))





