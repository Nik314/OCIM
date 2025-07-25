import logging
import os
from itertools import chain,combinations
import matplotlib.pyplot as plt
import seaborn
import pandas

import df2miner
from src.ocpn_conversion import *
import math


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


def export_ocpt(file_path, ocpt, additional=None):
	with open(file_path, "w") as text_file:
		text_file.write(str(additional) + "\n")
		text_file.write(str(ocpt.get_as_dict()) + "\n")
		text_file.write(str(ocpt))

def adjusted_log(relations, affected_activities):

	lookup = relations.groupby("ocel:eid").apply(lambda frame:list(frame["ocel:type"].unique())).to_dict()
	relations["ocel:activity"] = relations.apply(lambda row:(row["ocel:activity"] +"<|>" + str(sorted(
		lookup[row["ocel:eid"]])) if row["ocel:activity"] in affected_activities else row["ocel:activity"]),axis=1)
	return relations



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

	if not os.path.isdir(result_dir):
		os.mkdir(result_dir)

	try:
		conformance_results = pandas.read_csv(result_dir+"/experiment3.csv")
	except:
		conformance_results = pandas.DataFrame(columns=["Log", "Fitness", "Precision"])

	for file in os.listdir(dir_path):

		print(file)
		if file in conformance_results["Log"].unique():
			continue

		ocpt,runtime_stats, quality_stats = discovery(f"{dir_path}/{file}")
		print("OCPT Discovery Completed")

		from conformance.conformance import determine_conformance
		fitness, precision = determine_conformance(ocpt, f"{dir_path}/{file}",math.inf)
		conformance_results.loc[conformance_results.shape[0]] = (file,fitness,precision)
		conformance_results.to_csv(result_dir+"/experiment3.csv",index=False)


def run_experiment_4(dir_path, result_dir):

	if not os.path.isdir(result_dir):
		os.mkdir(result_dir)

	try:
		conformance_results = pandas.read_csv(result_dir+"/experiment4.csv")
	except:
		conformance_results = pandas.DataFrame(columns=["Log", "Fitness", "Precision"])

	for file in os.listdir(dir_path):

		print(file)
		if file in conformance_results["Log"].unique():
			continue

		ocpt = df2miner.df2_miner_apply(f"{dir_path}/{file}")
		print("OCPT Discovery Completed")

		from conformance.conformance import determine_conformance
		fitness, precision = determine_conformance(ocpt, f"{dir_path}/{file}",math.inf)
		conformance_results.loc[conformance_results.shape[0]] = (file,fitness,precision)
		conformance_results.to_csv(result_dir+"/experiment4.csv",index=False)




def run_experiment_5(dir_path, result_dir):

	if not os.path.isdir(result_dir):
		os.mkdir(result_dir)

	try:
		conformance_results = pandas.read_csv(result_dir + "/experiment5.csv")
	except:
		conformance_results = pandas.DataFrame(columns=["Log", "Fitness", "Precision"])

	for file in os.listdir(dir_path):

		print(file)
		if file in conformance_results["Log"].unique():
			continue

		try:
			input_log = pm4py.read_ocel2(f"{dir_path}/{file}").relations
		except:
			input_log = pm4py.read_ocel(f"{dir_path}/{file}").relations

		pts  = {ot:pm4py.discover_process_tree_inductive(input_log[input_log["ocel:type"]==ot],activity_key="ocel:activity",
				timestamp_key="ocel:timestamp",case_id_key="ocel:oid",noise_threshold=0.0)for ot in input_log["ocel:type"].unique()}
		print("OCPN Discovery Completed")

		from conformance.conformance import determine_conformance_pt_collection
		fitness, precision = determine_conformance_pt_collection(pts, f"{dir_path}/{file}")
		conformance_results.loc[conformance_results.shape[0]] = (file, fitness, precision)
		conformance_results.to_csv(result_dir + "/experiment5.csv", index=False)