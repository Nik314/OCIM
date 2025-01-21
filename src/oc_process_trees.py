from enum import Enum


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
        return indent + self.activity + "\n"



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
            result += str(tree)
        return result






