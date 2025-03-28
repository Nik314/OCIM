import os
from itertools import chain,combinations
import time

import pandas

from ocpa.objects.log.importer.ocel2.xml import factory as ocel_import_factory
from ocpa.algo.discovery.ocpn import algorithm as ocpn_discovery_factory
from ocpa.algo.conformance.precision_and_fitness import evaluator as quality_measure_factory

import ocpa.visualization.oc_petri_net.factory
from ocpn_conversion import *

def check_stats_print(dir_path):
	for file in os.listdir(dir_path):
		print(file)
		try:
			log = pm4py.read_ocel2(dir_path+ "/" + file)
			print(f"# Activities = {log.relations['ocel:activity'].nunique()}")
			print(f"# Events = {log.relations['ocel:eid'].nunique()}")
			print(f"# Objects = {log.relations['ocel:oid'].nunique()}")
			print(f"# Types = {log.relations['ocel:type'].nunique()}")
		except:
			log = pm4py.read_ocel(dir_path+ "/" + file)
			print(f"# Activities = {log.relations['ocel:activity'].nunique()}")
			print(f"# Events = {log.relations['ocel:eid'].nunique()}")
			print(f"# Objects = {log.relations['ocel:oid'].nunique()}")
			print(f"# Types = {log.relations['ocel:type'].nunique()}")


def check_stats_latex(dir_path):
	for file in os.listdir(dir_path):
		try:
			log = pm4py.read_ocel2(dir_path+ "/" + file)
			print(f"{file.split('_')[0]}&{' '.join(file.split('.')[0].split('_')[2:])}&{log.relations['ocel:activity'].nunique()}& {log.relations['ocel:eid'].nunique()}&"
				  f" {log.relations['ocel:oid'].nunique()} & {log.relations['ocel:type'].nunique()}&No& \\cite" +"{}\\\\")

		except:
			log = pm4py.read_ocel(dir_path+ "/" + file)
			print(f"{file.split('_')[0]}&{' '.join(file.split('.')[0].split('_')[2:])}&{log.relations['ocel:activity'].nunique()}& {log.relations['ocel:eid'].nunique()}&"
				  f" {log.relations['ocel:oid'].nunique()} & {log.relations['ocel:type'].nunique()}&No& \\cite" +"{}\\\\")




def powerset(iterable):
	s = list(iterable)
	return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))


def export_ocpn(file_path, ocpn, additional=None):
	with open(file_path, "w") as text_file:
		text_file.write(str(additional) + "\n")
		text_file.write(str(ocpn))

	ocpa.visualization.oc_petri_net.factory.save(
		ocpa.visualization.oc_petri_net.factory.apply(ocpn), file_path.replace(".ocpn",".png"))



def export_ocpt(file_path, ocpt, additional=None):
	with open(file_path, "w") as text_file:
		text_file.write(str(additional) + "\n")
		text_file.write(str(ocpt.get_as_dict()) + "\n")
		text_file.write(str(ocpt))

	translated_ocpt, special = convert_ocpt_to_ocpn(ocpt)
	ocpa.visualization.oc_petri_net.factory.save(
		ocpa.visualization.oc_petri_net.factory.apply(translated_ocpt), file_path.replace(".ocpt",".png"))


def adjusted_log(ocpa_log, affected_activities):
	ocpa_log.log.log["event_activity"] = ocpa_log.log.log.apply(lambda row:(row["event_activity"] +"<|>"+ str(sorted([ot
		for ot in ocpa_log.object_types if row[ot]])) if row["event_activity"] in affected_activities
															else row["event_activity"]),axis=1)

	return ocpa_log



def measure_runtime_ocpt(dir_path,discovery):

	result = pandas.DataFrame(columns=["Log", "Total Time", "Cut Detection",
			"Fallthrough Detection", "Tau Detection", "Log Splitting", "Interaction Properties"])
	for file in os.listdir(dir_path):

		ocpt,runtime_stats, _ = discovery(f"{dir_path}/{file}")
		print("OCPT Discovery Completed")

		result.loc[result.shape[0]] = (file, runtime_stats["total"],sum(runtime_stats["cuts"]), sum(runtime_stats["fallthroughs"]),
				sum(runtime_stats["taus"]), sum(runtime_stats["splits"]), sum(runtime_stats["properties"]))
		result.to_csv("time_measure.csv")







def determine_runtime_demands(dir_path,log_paths,ocpn_path,ocpt_path,discovery):
	for file in os.listdir(dir_path):

		try:
			log = pm4py.read_ocel2(dir_path+ "/" + file)
		except:
			log = pm4py.read_ocel(dir_path+ "/" + file)

		for dir in [log_paths,ocpn_path,ocpt_path]:
			try:
				os.mkdir(f"{dir}")
			except:
				pass

		if os.path.isfile(f"{ocpn_path}/{file.split(".")[0]}.ocpn"):
			continue

		pm4py.write_ocel2(log,f"{log_paths}/{file.split(".")[0]}.jsonocel")
		pm4py.write_ocel2(log,f"{log_paths}/{file.split(".")[0]}.xml")

		ocpa_log = ocel_import_factory.apply(f"{log_paths}/{file.split(".")[0]}.xml")
		print("Number of process executions: " + str(len(ocpa_log.process_executions)))
		print("Number of total objects: " +str(log.relations["ocel:oid"].nunique()))

		start = time.time()
		ocpt,runtime_stats, quality_stats = discovery(f"{log_paths}/{file.split(".")[0]}.jsonocel")
		runtime_stats["total"] = time.time() -start
		ocpn, special_activities = convert_ocpt_to_ocpn(ocpt)
		print("OCPT Discovery Completed")

		precision, fitness, skipped, timed, total = quality_measure_factory.apply(adjusted_log(ocpa_log,
			special_activities), ocpn, special_activities=special_activities)
		print("OCPT Conformance Completed")
		export_ocpt(f"{ocpt_path}/{file.split('.')[0]}.ocpt", ocpt,
					{"runtime": runtime_stats, "quality":quality_stats,
					 "fitness": fitness, "precision": precision,
					 "skipped": skipped, "timed": timed, "total": total})

		start = time.time()
		ocpn = ocpn_discovery_factory.apply(ocpa_log, parameters={"debug": True})
		runtime = time.time()-start
		print("OCPN Discovery Completed")

		precision, fitness, skipped, timed, total = quality_measure_factory.apply(ocpa_log, ocpn)
		export_ocpn(f"{ocpn}/{file.split(".")[0]}.ocpn", ocpn.to_dict(),
		{"runtime": runtime,"fitness":fitness,"precision":precision,
				"skipped":skipped,"timed":timed,"total":total})
		print("OCPN Conformance Completed")

