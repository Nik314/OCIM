from pytz import common_timezones

from ocpa.algo.conformance.precision_and_fitness.variants import replay_context
import ocpa.algo.conformance.precision_and_fitness.utils as utils
import copy



def apply(ocel,ocpn,contexts=None,bindings=None, special_activities=None):
    '''
    Calculation precision and fitness for an object-centric Petri net with respect to an object-centric event log. The
    measures are calculated according to replaying the event log and checking enabled and executed behavior. Contexts and
    bindings can be pre-computed and passed to the method to save computation time upon multiple calling. If not given,
    contexts and binding wil be calculated.

    :param ocel: Object-centric event log
    :type ocel: :class:`OCEL <ocpa.objects.log.ocel.OCEL>`

    :param ocpn: Object-centric Petri net
    :type ocpn: :class:`OCPN <ocpa.objects.oc_petri_net.obj.ObjectCentricPetriNet>`

    :param contexts: multiset of previously executed traces of activities for each event (can be computed by calling :func:`the corresponding function <ocpa.algo.evaluation.precision_and_fitness.utils.calculate_contexts_and_bindings>`)
    :type contexts: Dict

    :param bindings: bindings for each event (can be computed by calling :func:`the corresponding function <ocpa.algo.evaluation.precision_and_fitness.utils.calculate_contexts_and_bindings>`)
    :type bindings: Dict

    :return: precision, fitness
    :rtype: float, float

    '''

    object_types = ocel.object_types
    if contexts == None or bindings == None:
        contexts, bindings = utils.calculate_contexts_and_bindings(ocel)
    print("Context Done")
    en_l =  replay_context.enabled_log_activities(ocel.log, copy.deepcopy(contexts))
    en_m, total_timed =  replay_context.enabled_model_activities_multiprocessing(copy.deepcopy(contexts), bindings, ocpn, object_types)
    if special_activities:
        en_l = {key:{a.split("<|>")[0] if a.split("<|>")[0] in special_activities else a for a in value } for key,value in en_l.items()}
        en_m = {key:{a.split("<|>")[0] if a.split("<|>")[0] in special_activities else a for a in value } for key,value in en_m.items()}
    precision, skipped_events, fitness, timed, total =  replay_context.calculate_precision_and_fitness(ocel.log, copy.deepcopy(contexts), en_l, en_m, total_timed)
    return precision, fitness, skipped_events, timed, total
    