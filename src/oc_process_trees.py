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

        result = indent + self.activity + "\n"
        result += indent + "\t Related Types: " + str(self.related) +"\n"
        result += indent + "\t Divergent Types: " + str(self.divergent) +"\n"
        result += indent + "\t Convergent Types: " + str(self.convergent) +"\n"
        result += indent + "\t Deficient Types: " + str(self.deficient) +"\n"
        return result


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






