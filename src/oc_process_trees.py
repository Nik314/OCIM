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


class OperatorNode:

    def __init__(self, operator, subtrees):
        self.operator = operator
        self.subtrees = subtrees



