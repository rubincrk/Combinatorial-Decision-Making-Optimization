import os
import sys
import time
from math import floor
import sys
from utils import create_dzn, output_to_routes, routes_to_json, import_data, computeBounds, insert_bounds_to_file
from mip import main_mip
from smt import main_smt
from mip_pulp import main_mip_pulp
from mip_pulp_highs import main_mip_pulp_highs
#from mip_cplex import main_mip_cplex
import minizinc
import datetime

def run_cp_instance(data_path, chosen_model, chosen_solver):
    
    chosen_model = os.path.join("cp", "models", chosen_model)
    
    #chosen_model = os.path.join("/home", "cp", "models", chosen_model)
    
    # Check if the model file exists
    if not os.path.exists(chosen_model):
        raise FileNotFoundError(f"Model file {chosen_model} does not exist.")

    # Check if the data file exists
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file {data_path} does not exist.")

    # Load the MiniZinc model
    model = minizinc.Model(chosen_model)
    
    # Add the data file to the model
    model.add_file(data_path)

    # Select the solver
    solver = minizinc.Solver.lookup(chosen_solver)
    
    if solver is None:
        raise ValueError(f"Solver {chosen_solver} not found.")
    
    # Create an instance of the MiniZinc problem
    instance = minizinc.Instance(solver, model)

    # Set a timeout of 300 seconds
    timeout = datetime.timedelta(seconds=300)
    
    #Start the timer
    time_start = time.time()

    # Run the model with the specified timeout
    output = instance.solve(timeout=timeout)
        
    # Stop timer
    time_end = floor(time.time() - time_start)
    
    # Check if the solution is optimal
    if output.status.has_solution():
        if output.status == minizinc.result.Status.OPTIMAL_SOLUTION:
            output_dict = {
              'succ': output.solution.succ,
               'u' :output.solution.u,
              'max_dist': output.solution.objective,
              'optimal': "true"
            }
        else:
            output_dict = {
              'succ': output.solution.succ,
               'u' :output.solution.u,
              'max_dist': output.solution.objective,
              'optimal': "false"
            }
    else:
        output_dict = None
        
    
    if output_dict is not None:
        routes = output_to_routes(output_dict)
    else:
        routes = []

    return output_dict, time_end, routes


def run_all_cp(solver):
    
    methods_gecode = ["dom_w_deg_rand_linear", "dom_w_deg_rand_luby", "fail_rand_lin_SB", "fail_rand_lin", "fail_rand_luby", "fail_rand_luby_SB"]
    
    methods_chuffed = ["fail_min", "fail_min_SB", "fail_split", "fail_split_SB"]
    
    if solver == "gecode":
        print("Solver used: ", solver)
    
        for model in methods_gecode:
            print("----------------------------------------------------------------")
            
            if model == "dom_w_deg_rand_linear":
                model_type = "model_dom_rand_linear.mzn"
            elif model == "dom_w_deg_rand_luby":
                model_type = "model_dom_rand_luby.mzn"
            elif model == "fail_rand_lin_SB":
                model_type = "model_fail_rand_lin_SB.mzn"
            elif model == "fail_rand_lin":
                model_type = "model_fail_rand_lin.mzn"
            elif model == "fail_rand_luby":
                model_type = "model_fail_rand_luby.mzn"
            elif model == "fail_rand_luby_SB":
                model_type = "model_fail_rand_luby_SB.mzn"
                
            
            print("Using model " + model)    
            for i in range(1,22):
                if i<10:
                    instance=f"0{i}"
                else:
                    instance=f"{i}"
        
                print("Running instance", instance)
            
                file_name = f"./cp/Instances/inst{instance}.dzn"
                file_name_dat = f"Instances/inst{instance}.dat"
                num_couriers, num_items, courier_size, item_size, distances = import_data(file_name_dat)
                lb, ub = computeBounds(distances, num_couriers, num_items)
            
                insert_bounds_to_file(file_name, lb, ub)
        
                output_dict, time, routes = run_cp_instance(file_name, model_type, solver)

                routes_to_json(routes, time, instance, output_dict, model, solver)
        
                if output_dict != None:
                    print("Max distance: ", output_dict['max_dist'], "Optimal: ", output_dict["optimal"],"\n")
    
                else:
                    print("\n")
    else:
        
        print("Solver used: ", solver)
    
        for model in methods_chuffed:
            print("----------------------------------------------------------------")
            nameModel = model
            model = f"{model}_{solver}"
            
            if model == "fail_min_SB_chuffed":
                model_type = "model_fail_min_SB_chuffed.mzn"
            elif model == "fail_split_chuffed":
                model_type = "model_fail_split_chuffed.mzn"
            elif model == "fail_min_chuffed":
                model_type = "model_fail_min_chuffed.mzn"
            elif model == "fail_split_SB_chuffed":
                model_type = "model_fail_split_SB_chuffed.mzn"
                
        
            print("Using model " + model)    
            for i in range(1,22):
                if i<10:
                    instance=f"0{i}"
                else:
                    instance=f"{i}"
        
                print("Running instance", instance)
            
                file_name = f"./cp/Instances/inst{instance}.dzn"
                file_name_dat = f"Instances/inst{instance}.dat"
                num_couriers, num_items, courier_size, item_size, distances = import_data(file_name_dat)
                lb, ub = computeBounds(distances, num_couriers, num_items)
            
                insert_bounds_to_file(file_name, lb, ub)
        
                output_dict, time, routes = run_cp_instance(file_name, model_type, solver)

                routes_to_json(routes, time, instance, output_dict, nameModel, solver)
        
                if output_dict != None:
                    print("Max distance: ", output_dict['max_dist'], "Optimal: ", output_dict["optimal"],"\n")
    
                else:
                    print("\n")
        
        
           
def run_all_at_once():
    orT_available_inst = [1,2,3,4,5,6,7,8,9,10,13,16]
    
    #file_path = f"Instances/"
    #create_dzn(file_path)
    
    print("Running all")
    #folder_path = f"cp/models/"
    run_all_cp(solver="gecode")
    run_all_cp(solver="chuffed")   
    
    #----------------------------------------------------------------    
    
    print("----------------------------------------------------------------") 
    print("\nStarting SMT")
    for inst in range(1,22):
        if inst<10:
            instance=f"0{inst}"
        else:
            instance=f"{inst}"
            
        main_smt(instance)  
        
    #----------------------------------------------------------------  
          
    
    print("----------------------------------------------------------------") 
    print("\nStarting MIP with ortools")
    for inst in range(1,22):
        if inst not in orT_available_inst:
            continue
        else:
            if inst<10:
                instance=f"0{inst}"
            else:
                instance=f"{inst}"
            
            main_mip(instance)   
    
    print("----------------------------------------------------------------") 
    print("\nStarting MIP with PuLP using CBC solver")
    for inst in range(1,11):
        if inst<10:
            instance=f"0{inst}"
        else:
            instance=f"{inst}"
            
        main_mip_pulp(instance)    
        
    print("----------------------------------------------------------------") 
    print("\nStarting MIP with PuLP using HIGHS solver")
    for inst in range(1,11):
        if inst<10:
            instance=f"0{inst}"
        else:
            instance=f"{inst}"
            
        main_mip_pulp_highs(instance) 
    instance = 16
    main_mip_pulp_highs(instance)
    
    
    print("----------------------------------------------------------------") 
    #print("\nStarting MIP with Docplex solver")
    #for inst in range(1,22):
     #   if inst<10:
      #      instance=f"0{inst}"
       # else:
        #    instance=f"{inst}"
            
        #main_mip_cplex(instance) 
        

    
    return None



def run_chosen_approach_cp(instance_num, solver, approach):
    
    methods_gecode = ["dom_w_deg_rand_linear", "dom_w_deg_rand_luby", "fail_rand_lin_SB", "fail_rand_lin", "fail_rand_luby", "fail_rand_luby_SB"]
    
    methods_chuffed = ["fail_min", "fail_min_SB", "fail_split", "fail_split_SB"]
    
    if solver == "gecode":
        
        if approach not in methods_gecode:
            print("Method not available for gecode, insert another method.")
            return
        
        else:
            
            if approach == "dom_w_deg_rand_linear":
                 model_type = "model_dom_rand_linear.mzn"
            elif approach == "dom_w_deg_rand_luby":
                model_type = "model_dom_rand_luby.mzn"
            elif approach == "fail_rand_lin_SB":
                model_type = "model_fail_rand_lin_SB.mzn"
            elif approach == "fail_rand_lin":
                model_type = "model_fail_rand_lin.mzn"
            elif approach == "fail_rand_luby":
                model_type = "model_fail_rand_luby.mzn"
            elif approach == "fail_rand_luby_SB":
                model_type = "model_fail_rand_luby_SB.mzn"
    
        
        
            print(f"Running instance {instance_num}")
            print("Solver used: Gecode")
        
            file_name = f"./cp/Instances/inst{instance_num}.dzn"
            file_name_dat = f"Instances/inst{instance_num}.dat"
            num_couriers, num_items, courier_size, item_size, distances = import_data(file_name_dat)
        
            lb, ub = computeBounds(distances, num_couriers, num_items)
       
            insert_bounds_to_file(file_name, lb, ub)
        
            output_dict, time, routes = run_cp_instance(file_name, model_type, solver)

            routes_to_json(routes, time, instance_num, output_dict, approach, solver)
        
            if output_dict != None:
                print("Max distance: ", output_dict['max_dist'], "Optimal: ", output_dict["optimal"],"\n")
            else:
                print("\n")
                
    elif solver == "chuffed":
        if approach not in methods_chuffed:
            print("Method not available for chuffed, insert another method.")
            return
        
        else:   
            nameModel = approach 
            approach = f"{approach}_{solver}"
            
            if approach == "fail_min_SB_chuffed":
                 model_type = "model_fail_min_SB_chuffed.mzn"
            elif approach == "fail_split_chuffed":
                model_type = "model_fail_split_chuffed.mzn"
            elif approach == "fail_min_chuffed":
                model_type = "model_fail_min_chuffed.mzn"
            elif approach == "fail_split_SB_chuffed":
                model_type = "model_fail_split_SB_chuffed.mzn"
            
    
            print("Solver used: chuffed")
        
            print(f"Running instance {instance_num} with {approach} model")
            
        
            file_name = f"./cp/Instances/inst{instance_num}.dzn"
            file_name_dat = f"Instances/inst{instance_num}.dat"
            num_couriers, num_items, courier_size, item_size, distances = import_data(file_name_dat)
        
            lb, ub = computeBounds(distances, num_couriers, num_items)
       
            insert_bounds_to_file(file_name, lb, ub)
        
            output_dict, time, routes = run_cp_instance(file_name, model_type, solver)

            routes_to_json(routes, time, instance_num, output_dict, nameModel, solver)
        
            if output_dict != None:
                print("Max distance: ", output_dict['max_dist'], "Optimal: ", output_dict["optimal"],"\n")
            else:
                print("\n")
    
    else:
        print("No solver available with that name. You have tu use either 'gecode' or 'chuffed'.")
        return
    
    return None


def run_chosen_approach(instance_num, method):
    
    if method == "smt":
        print("----------------------------------------------------------------")
        print("Executing smt method...")
        main_smt(instance_num)
        
    elif method == "mip_ortools":
        print("----------------------------------------------------------------")
        print("Executing mip with ortools...")
        main_mip(instance_num)
        
    elif method == "mip_pulp":
        print("----------------------------------------------------------------")
        
        print("Executing mip with pulp using CBC...")
        if int(instance_num) > 10:
            print("PuLP with CBC solver cannot solve instances larger than 10!")
        else:
            main_mip_pulp(instance_num)
        
        
        print("----------------------------------------------------------------")
        
        print("Executing mip with PuLP using HIGHS...")
        if int(instance_num) > 10 and int(instance_num) != 16:
            print("PuLP with HIGHS solver cannot solve instances larger than 10 except 16!")
        else:
            main_mip_pulp_highs(instance_num)
        
    
    
    return None
    


def main():
    
    if len(sys.argv) == 4:
    
        instance_num = sys.argv[3]
        solver = sys.argv[1]
        approach = sys.argv[2]
        run_chosen_approach_cp(instance_num, solver, approach)
        
    elif len(sys.argv) == 3:
        instance_num = sys.argv[2]
        method = sys.argv[1]
        run_chosen_approach(instance_num, method)
        
    elif len(sys.argv) == 1:
        run_all_at_once()
    
    else:
        print("You must provide 4 args for cp, 3 args for smt/mip or no arguments if you want to run all at once.")
        return


    return None



if __name__ == "__main__":
    main()