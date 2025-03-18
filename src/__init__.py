import pandas.errors

from auxillary_methods import *
from interaction_patterns import *
from cut_definition import *
from follows_relations import *
from cut_detection import *
from fallthrough_detection import *
from tau_cases import *
from oc_process_trees import *
from log_splitting import *
from common_data import *

import warnings
warnings.filterwarnings("ignore", category=pandas.errors.SettingWithCopyWarning)


def object_centric_inductive_miner(local_data, global_data, brute_force = False, noise = False):

    partition, operator = detect_tau_cases(local_data,global_data)

    if operator:
        print(partition, operator)
        print("##############################################################################")

        sublogs = split_log(local_data, partition,operator,global_data)
        subtrees = [object_centric_inductive_miner(sublogs[0], global_data, brute_force, noise),
            LeafNode("tau",local_data.object_types,local_data.object_types,local_data.object_types,local_data.object_types)]
        return OperatorNode(operator, subtrees)

    if len(local_data.alphabet) == 1:
        return LeafNode(local_data.alphabet[0],global_data.related[local_data.alphabet[0]],
            global_data.divergence[local_data.alphabet[0]],global_data.convergence[local_data.alphabet[0]],
                        global_data.deficiency[local_data.alphabet[0]])

    partition, operator = find_strict_cut(local_data, global_data)
    if operator is None:
        if not brute_force:
            partition, operator = detect_fallthrough_fitness_polynomial(local_data,global_data)
        else:
            partition, operator = detect_fallthrough_fitness_brute_force(local_data,global_data)

    print(partition,operator)
    print("##############################################################################")

    sublogs = split_log(local_data,partition,operator,global_data)
    subtrees = [object_centric_inductive_miner(split_local_data, global_data,brute_force,noise) for split_local_data in sublogs]
    return OperatorNode(operator, subtrees)



def apply(file_path):
    input_log = pm4py.read_ocel2(file_path).relations
    global_data = GlobalData([input_log])
    local_data = LocalData([input_log])
    return object_centric_inductive_miner(local_data, global_data)



if __name__ == "__main__":

    print(apply("../data/24_ocel_legacy_running-example.jsonocel"))
    exit()

    from ocpa.objects.log.importer.ocel import factory as ocel_import_factory
    from ocpa.algo.conformance.precision_and_fitness import evaluator as quality_measure_factory
    from ocpa.algo.discovery.ocpn import algorithm as ocpn_discovery_factory

    filename = "../data/23_ocel_legacy_recruiting.jsonocel"
    ocel = ocel_import_factory.apply(filename)
    ocpn = ocpn_discovery_factory.apply(ocel, parameters={"debug": True})
    precision, fitness = quality_measure_factory.apply(ocel, ocpn)
    print("Precision of IM-discovered net: " + str(precision))
    print("Fitness of IM-discovered net: " + str(fitness))




