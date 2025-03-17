import os

import pm4py


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




