from src import apply, evaluation_util



if __name__ == "__main__":

	#Provide the directory in which the input logs are placed
	#OCEL1.0 and 2.0 are both possible with pm4py compatibility
	data_directory = "data"

	#Provide the directory in which the results are placed
	#If it does not exist, it will be created automatically
	result_directory = "results"

	#Next, decide which experiments you want to run
	#By default, all four from the paper are executed
	#Note, this will take some time and use lots of cores

	evaluation_util.experiment_1_and_2(data_directory,apply,result_directory)
	evaluation_util.print_experiment_1(result_directory)
	evaluation_util.plot_experiment_2(result_directory)
	evaluation_util.run_experiment_3("data","results", apply,"")




