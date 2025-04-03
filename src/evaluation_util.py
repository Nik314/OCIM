import os
from itertools import chain,combinations
import matplotlib.pyplot as plt
import time
import seaborn
import numpy
import pandas
from ocpa.objects.log.importer.ocel2.xml import factory as ocel_import_factory
from ocpa.algo.discovery.ocpn import algorithm as ocpn_discovery_factory
from ocpa.algo.conformance.precision_and_fitness import evaluator as quality_measure_factory
import ocpa.visualization.oc_petri_net.factory
from src.ocpn_conversion import *

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



def experiment_1_and_2(dir_path,discovery, result_dir):

	if not os.path.isdir(result_dir):
		os.mkdir(result_dir)

	try:
		runtime_result = pandas.read_csv(result_dir+"/experiment1.csv")
	except:
		runtime_result = pandas.DataFrame(columns=["Log", "Total Time", "Cut Detection",
			"Fallthrough Detection", "Tau Detection", "Log Splitting", "Interaction Properties"])

	try:
		quality_result = pandas.read_csv(result_dir+"/experiment2.csv")
	except:
		quality_result = pandas.DataFrame(columns=["Log", "Total Steps", "Detected Cuts", "Detected Fallthroughs"])


	for file in os.listdir(dir_path):

		print(file)

		if file in runtime_result["Log"].unique():
			continue

		ocpt,runtime_stats, quality_stats = discovery(f"{dir_path}/{file}")
		print("OCPT Discovery Completed")

		runtime_result.loc[runtime_result.shape[0]] = (file, runtime_stats["total"],sum(runtime_stats["cuts"]), sum(runtime_stats["fallthroughs"]),
				sum(runtime_stats["taus"]), sum(runtime_stats["splits"]), sum(runtime_stats["auxiliary"]))

		runtime_result.to_csv(result_dir+"/experiment1.csv",index=False)
		quality_result.loc[quality_result.shape[0]] = (file,len(quality_stats["cuts"]) + len(quality_stats["fallthroughs"]),
											quality_stats["cuts"], quality_stats["fallthroughs"])
		quality_result.to_csv(result_dir+"/experiment2.csv",index=False)



def print_experiment_1(result_dir):

	result = pandas.read_csv(result_dir+"/experiment1.csv")
	result["Remaining"] = result["Total Time"] - (result["Cut Detection"] + result["Fallthrough Detection"] +
		result["Tau Detection"] + result["Log Splitting"] +result["Interaction Properties"])
	for row in ["Cut Detection", "Fallthrough Detection", "Tau Detection", "Log Splitting", "Interaction Properties", "Remaining"]:
		result[row] = round((result[row] / result["Total Time"])*100,2)

	result.apply(lambda row:print(f"{row['Log'].split('_')[0]}& {round(row['Total Time'],2)} & {row['Cut Detection']} & {row['Fallthrough Detection']} "
							f"& {row['Tau Detection']} & {row['Log Splitting']} & {row['Interaction Properties']} & {row['Remaining']} \\\\"), axis=1)



def plot_experiment_2(result_dir):
	seaborn.set(font_scale=2)
	result = pandas.read_csv(result_dir+"/experiment2.csv")
	load_string = lambda input:eval(input.replace("->","Operator.SEQUENCE").replace("X","Operator.XOR").replace("+","Operator.PARALLEL").replace("*","Operator.LOOP"))
	result["Detected Cuts"] = result["Detected Cuts"].apply(load_string)
	result["Detected Fallthroughs"] = result["Detected Fallthroughs"].apply(load_string)
	result["Fallthrough Extent"] = result.apply(lambda row:[(row["Log"],value[2])
		for value in row["Detected Fallthroughs"]] + [(row["Log"],1.0) for value in row["Detected Cuts"]], axis=1)
	plot_data = sum(result["Fallthrough Extent"].values,[])
	plot_data = {"Object-Centric Input Log":[point[0].split("_")[0] for point in plot_data], "Fallthrough Precision Estimate":[point[1] for point in plot_data]}
	seaborn.stripplot(plot_data,y="Fallthrough Precision Estimate",x="Object-Centric Input Log",dodge=True)
	plt.show()





def run_experiment_3(dir_path, result_dir, discovery):

	for file in os.listdir(dir_path):

		try:
			log = pm4py.read_ocel2(dir_path+ "/" + file)
		except:
			log = pm4py.read_ocel(dir_path+ "/" + file)

		if not os.path.isdir(result_dir+"/"+file.split(".")[0]):
			os.mkdir(result_dir+"/"+file.split(".")[0])

		storage = result_dir+"/"+file.split(".")[0]

		if os.path.isfile(storage+"results.ocpt"):
			continue

		pm4py.write_ocel2(log,f"{storage}/{file.split('.')[0]}.jsonocel")
		pm4py.write_ocel2(log,f"{storage}/{file.split('.')[0]}.xml")
		ocpa_log = ocel_import_factory.apply(f"{storage}/{file.split('.')[0]}.xml")
		print("Number of process executions: " + str(len(ocpa_log.process_executions)))
		print("Number of total objects: " +str(log.relations["ocel:oid"].nunique()))

		ocpt, _, __ = discovery(f"{storage}/{file.split('.')[0]}.jsonocel")
		ocpn, special_activities = convert_ocpt_to_ocpn(ocpt)
		print("OCPT Discovery Completed")

		precision, fitness, skipped, timed, total = quality_measure_factory.apply(adjusted_log(ocpa_log,
			special_activities), ocpn, special_activities=special_activities)

		export_ocpt(f"{storage}/{file.split('.')[0]}.ocpt", ocpt,
					{ "fitness": fitness, "precision": precision,
					 "skipped": skipped, "timed": timed, "total": total})

		print("OCPT Conformance Completed")



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

		if os.path.isfile(f"{ocpn_path}/{file.split('.')[0]}.ocpn"):
			continue

		pm4py.write_ocel2(log,f"{log_paths}/{file.split('.')[0]}.jsonocel")
		pm4py.write_ocel2(log,f"{log_paths}/{file.split('.')[0]}.xml")

		ocpa_log = ocel_import_factory.apply(f"{log_paths}/{file.split('.')[0]}.xml")
		print("Number of process executions: " + str(len(ocpa_log.process_executions)))
		print("Number of total objects: " +str(log.relations["ocel:oid"].nunique()))

		start = time.time()
		ocpt,runtime_stats, quality_stats = discovery(f"{log_paths}/{file.split('.')[0]}.jsonocel")
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
		export_ocpn(f"{ocpn}/{file.split('.')[0]}.ocpn", ocpn.to_dict(),
		{"runtime": runtime,"fitness":fitness,"precision":precision,
				"skipped":skipped,"timed":timed,"total":total})
		print("OCPN Conformance Completed")

