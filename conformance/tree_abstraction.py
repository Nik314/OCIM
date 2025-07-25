import time
import pm4py

from src.ocpn_conversion import project_ocpt
from src.oc_process_trees import *
import math

def get_tree_abstraction(tree):

    rel,div,con,defi,opt = get_tree_interaction_patterns(tree)
    dfgs = get_tree_dfgs(tree)
    return dfgs,rel,div,con,defi,opt


def search_leaf_path(tree,a):
    if isinstance(tree,OperatorNode):
        for sub in tree.subtrees:
            sub_path, check = search_leaf_path(sub,a)
            if check:
                return sub_path +[tree.operator],check
        return [], False

    return [], tree.activity == a


def check_convergence(tree,a,ot,leaf_spefication,opt,div):
    if ot not in leaf_spefication[(a,"con")]:
        return False
    if ot in leaf_spefication[(a,"def")] or ot in div[a]:
        return True
    problems = [ot2 for ot2 in leaf_spefication[(a,"rel")] if ot2 != ot and ot2 not in opt[a]
        and ot2 not in leaf_spefication[(a,"con")]]

    result = True
    for ot2 in problems:
        result = result and check_convergence_recursion(tree,a,ot,ot2,leaf_spefication,opt,div)

    return result


def check_convergence_recursion(tree,a,ot,ot2, leaf_specification,opt,div):

    if isinstance(tree,OperatorNode):
        if tree.operator in [Operator.SEQUENCE,Operator.PARALLEL]:
            return all([check_convergence_recursion(sub,a,ot,ot2,leaf_specification,opt,div) for sub in tree.subtrees])
        if tree.operator in [Operator.XOR]:
            return any([check_convergence_recursion(sub,a,ot,ot2,leaf_specification,opt,div) for sub in tree.subtrees])
        if tree.operator in [Operator.LOOP]:
            return check_convergence_recursion(tree.subtrees[0],a,ot,ot2,leaf_specification,opt,div)

    assert isinstance(tree,LeafNode)
    if tree.activity == "" or tree.activity =="tau":
        return True
    if ot in leaf_specification[(tree.activity,"con")] or ot in opt[tree.activity]:
        return True
    if ot2 in leaf_specification[(tree.activity,"def")] or ot in div[tree.activity]:
        return True
    return False



def check_deficient(tree,a,ot,leaf_spefication,opt,div):
    if ot not in leaf_spefication[(a,"def")]:
        return False
    if ot in leaf_spefication[(a,"con")] or ot in opt[a]:
        return True
    problems = [ot2 for ot2 in leaf_spefication[(a,"rel")] if ot2 != ot and ot2 not in div[a]
        and ot2 not in leaf_spefication[(a,"def")]]

    result = True
    for ot2 in problems:
        result = result and check_deficient_recursion(tree,a,ot,ot2,leaf_spefication,opt,div)

    return result


def check_deficient_recursion(tree,a,ot,ot2, leaf_specification,opt,div):
    if isinstance(tree,OperatorNode):
        if tree.operator in [Operator.SEQUENCE,Operator.PARALLEL]:
            return all([check_deficient_recursion(sub,a,ot,ot2,leaf_specification,opt,div) for sub in tree.subtrees])
        if tree.operator in [Operator.XOR]:
            return any([check_deficient_recursion(sub,a,ot,ot2,leaf_specification,opt,div) for sub in tree.subtrees])
        if tree.operator in [Operator.LOOP]:
            return check_deficient_recursion(tree.subtrees[0],a,ot,ot2,leaf_specification,opt,div)

    assert isinstance(tree,LeafNode)
    if tree.activity == "" or tree.activity =="tau":
        return True
    if ot in leaf_specification[(tree.activity,"def")] or ot in opt[tree.activity]:
        return True
    if ot2 in leaf_specification[(tree.activity,"con")] or ot in div[tree.activity]:
        return True
    return False




def get_tree_interaction_patterns(tree):

    assert isinstance(tree,OperatorNode) or isinstance(tree,LeafNode)
    leaf_specification = tree.get_type_information()
    activities = [a for a in tree.get_activities() if a != "" and a != "tau"]
    object_types = tree.get_object_types()

    rel = {a:[ot for ot in object_types if ot in leaf_specification[(a,"rel")]] for a in activities}
    div = {a:[ot for ot in object_types if ot in leaf_specification[(a,"div")] or (ot in leaf_specification[(a,"rel")] and
        Operator.LOOP in search_leaf_path(tree,a)[0])] for a in activities}
    opt = {a:[ot for ot in object_types if ot in leaf_specification[(a,"div")] or (ot in leaf_specification[(a,"rel")] and
        Operator.XOR in search_leaf_path(tree,a)[0])] for a in activities}
    con = {a:[ot for ot in object_types if check_convergence(tree,a,ot,leaf_specification,opt,div)] for a in activities}
    defi = {a:[ot for ot in object_types if check_deficient(tree,a,ot,leaf_specification,opt,div)] for a in activities}

    return rel,div,con,defi,opt


def add_parents(tree,parent):
    if parent:
        tree.parent = parent
    if tree.operator:
        for sub in tree.children:
            add_parents(sub,tree)
    return tree


def get_tree_dfgs(tree):
    return {ot:dfg_recursion(project_ocpt(tree,ot))[:3] for ot in tree.get_object_types()}


def dfg_recursion(pt,output = False):

    if pt.operator == Operator.SEQUENCE:
        sub_dfgs = [dfg_recursion(sub,output) for sub in pt.children]
        dfg,start,end,optional,sigma= {},{},{},True,[]

        for i in range(0,len(sub_dfgs)):
            sub_dfg,sub_start,sub_end, sub_optional,sub_sigma = sub_dfgs[i]
            optional = optional and sub_optional
            sigma = sigma+sub_sigma
            dfg.update(sub_dfgs[i][0])

            if all(sub_dfgs[j][3] for j in range(0,i)):
                start.update(sub_start)
            if all(sub_dfgs[j][3] for j in range(i+1,len(sub_dfgs))):
                end.update(sub_end)

            for j in range(0, i):
                if all(sub_dfgs[k][3] for k in range(j+1,i)):
                    dfg.update({(a,b):1 for a in sub_dfgs[j][2] for b in sub_start})

            for j in range(i+1, len(sub_dfgs)):
                if all(sub_dfgs[k][3] for k in range(i+1,j)):
                    dfg.update({(a,b):1 for b in sub_dfgs[j][1] for a in sub_end})

        return dfg,start,end,optional,sigma

    elif pt.operator == Operator.XOR:
        sub_dfgs = [dfg_recursion(sub,output) for sub in pt.children]
        dfg, start, end, optional, sigma = {}, {}, {}, False, []

        for i in range(0,len(sub_dfgs)):
            sub_dfg, sub_start, sub_end, sub_optional, sub_sigma = sub_dfgs[i]
            dfg.update(sub_dfg)
            sigma += sub_sigma
            start.update(sub_start)
            end.update(sub_end)
            optional = optional or sub_optional

        return dfg,start,end,optional,sigma

    elif pt.operator == Operator.PARALLEL:
        sub_dfgs = [dfg_recursion(sub,output) for sub in pt.children]
        dfg, start, end, optional, sigma = {}, {}, {}, True, []

        for i in range(0, len(sub_dfgs)):
            sub_dfg, sub_start, sub_end, sub_optional, sub_sigma = sub_dfgs[i]
            dfg.update(sub_dfg)
            sigma += sub_sigma
            start.update(sub_start)
            end.update(sub_end)
            optional = optional and sub_optional

            for j in range(i+1,len(sub_dfgs)):
                other_sigma = sub_dfgs[j][4]
                new_rules = {(a,b):1 for a in sub_sigma for b in other_sigma}
                dfg.update(new_rules)
                new_rules = {(b,a):1 for a in sub_sigma for b in other_sigma}
                dfg.update(new_rules)

        return dfg, start, end, optional, sigma

    elif pt.operator == Operator.LOOP:

        sub_dfgs = [dfg_recursion(sub,output) for sub in pt.children]
        dfg, start, end, optional, sigma = {}, {}, {}, sub_dfgs[0][3], []

        for i in range(0, len(sub_dfgs)):
            sub_dfg, sub_start, sub_end, sub_optional, sub_sigma = sub_dfgs[i]
            dfg.update(sub_dfg)
            sigma += sub_sigma

        start.update(sub_dfgs[0][1])
        end.update(sub_dfgs[0][2])

        for i in range(1, len(sub_dfgs)):
            if optional:
                start.update(sub_dfgs[i][1])
                end.update(sub_dfgs[i][2])

            newrules = {(a,b):1 for a in sub_dfgs[0][2] for b in sub_dfgs[i][1] }
            dfg.update(newrules)
            newrules = {(a,b):1 for a in sub_dfgs[i][2] for b in sub_dfgs[0][1] }
            dfg.update(newrules)

        newrules = {(a, b): 1 for a in end.keys() for b in start.keys()}
        dfg.update(newrules)

        return dfg, start, end, optional, sigma

    else:
        dfg,start,end,optional,sigma = {},{},{},True,[]
        if pt.label and pt.label != "":
            start[pt.label] = 1
            end[pt.label] = 1
            optional = False
            sigma = [pt.label]
        return dfg,start,end,optional,sigma