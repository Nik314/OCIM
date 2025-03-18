import os
from itertools import chain,combinations
import pm4py
import pandas
import time


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
		text_file.write(str(ocpt))



def determine_runtime_demands(dir_path,log_paths,ocpn_path,ocpt_path,discovery):
	for file in os.listdir(dir_path):
		print(file)
		try:
			log = pm4py.read_ocel2(dir_path+ "/" + file)
		except:
			log = pm4py.read_ocel(dir_path+ "/" + file)

		try:
			os.mkdir(f"{ocpn_path}/{file.split('_')[0]}")
		except:
			pass

		try:
			os.mkdir(f"{ocpt_path}/{file.split('_')[0]}")
		except:
			pass

		try:
			os.mkdir(f"{log_paths}/{file.split('_')[0]}")
		except:
			pass

		relations = log.relations

		for object_types in powerset(list(relations["ocel:type"].unique())):
			if len(object_types) > 1:
				print(object_types)
				sublog = pm4py.filter_ocel_object_types(log,object_types,positive=True)
				name = "_".join(object_types).replace(":","")
				pm4py.write_ocel2(sublog,f"{log_paths}/{file.split('_')[0]}/{name}.jsonocel")

				start = time.time()
				model = discovery(f"{log_paths}/{file.split('_')[0]}/{name}.jsonocel")
				runtime = time.time() - start
				export_ocpt(f"{ocpt_path}/{file.split('_')[0]}/{name}.ocpt", model, {"runtime": runtime})

				start = time.time()
				model = pm4py.discover_oc_petri_net(sublog)
				runtime = time.time()-start
				export_ocpn(f"{ocpn_path}/{file.split('_')[0]}/{name}.ocpn", model , {"runtime":runtime})
