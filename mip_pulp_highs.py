import os
from timeit import default_timer as timer
import time
import math
import json
from utils import computeBounds, import_data
import pulp as plp
import highspy

def main_mip_pulp_highs(instance):
    
    print("Running instance: ", instance)
    file_name = f"Instances/inst{instance}.dat"
    
    timelimit = 300
    num_couriers, num_items, courier_size, item_size, distances = import_data(file_name)
    lb, ub = computeBounds(distances, num_couriers, num_items)
    
    opt_model = plp.LpProblem(name="MIP_Model")
    

    # Binary variable visit
    visit  = {(k,i,j):
    plp.LpVariable(cat=plp.LpBinary, name="visit_{0}_{1}_{2}".format(k,i,j)) 
    for k in range(num_couriers) for i in range(num_items+1) for j in range(num_items+1)}
    
    # Binary variable load
    load  = {(i,j): 
    plp.LpVariable(cat=plp.LpBinary, name="load_{0}_{1}".format(i,j)) 
    for i in range(num_couriers) for j in range(num_items)}
    
    # if x is Integer
    num_visit  = {(i,j):
    plp.LpVariable(cat=plp.LpInteger, name="num_visit_{0}_{1}".format(i,j)) 
    for i in range(num_couriers) for j in range(num_items + 1)}
    
    # Integer variable max_distance
    max_distance = plp.LpVariable(cat=plp.LpInteger, lowBound=lb, upBound=ub, name="max_distance")

    start_time = timer()
    
    # --------Constraints--------

    # Each customer should be visited only once
    for j in range(num_items):
        opt_model += (plp.lpSum(load[i, j] for i in range(num_couriers)) == 1, f"customer_once_{j}")
    
    for i in range(num_items):
        opt_model += (plp.lpSum(visit[k, i, j] for k in range(num_couriers) for j in range(num_items+1)) == 1, f"visit_1_{i}")
        opt_model += (plp.lpSum(visit[k, j, i] for k in range(num_couriers) for j in range(num_items+1)) == 1, f"visit_2_{i}")

    for i in range(num_items):
        for k in range(num_couriers):
            opt_model += (
                plp.lpSum(visit[k, i, j] for j in range(num_items+1)) == 
                plp.lpSum(visit[k, j, i] for j in range(num_items+1)), f"flow_{i}_{k}"
            )
            opt_model += (plp.lpSum(visit[k, i, j] for j in range(num_items+1)) == load[k, i], f"const_{i}_{k}")
            opt_model += (plp.lpSum(visit[k, j, i] for j in range(num_items+1)) == load[k, i], f"const2_{i}_{k}")
    
    for k in range(num_couriers):
        opt_model += (plp.lpSum(visit[k, j, j] for j in range(num_items)) == 0, f"self_loop_{k}")
        opt_model += (plp.lpSum(load[k, j] * item_size[j] for j in range(num_items)) <= courier_size[k], f"capacity_{k}")
        opt_model += (plp.lpSum(visit[k, num_items, i] for i in range(num_items)) == 1, f"start_{k}")
        opt_model += (plp.lpSum(visit[k, i, num_items] for i in range(num_items)) == 1, f"end_{k}")
        opt_model += (plp.lpSum(visit[k, i, j] * distances[i][j] for i in range(num_items+1) for j in range(num_items+1)) <= max_distance, f"distance_{k}")
    
    for k in range(num_couriers):
        for i in range(num_items+1):
            for j in range(num_items+1):
                if i != j and i != num_items:
                    opt_model += (num_visit[k, i] - num_visit[k, j] + num_items * visit[k, i, j] <= num_items - 1, f"mtz_{k}_{i}_{j}")
    
    
    end_const = timer()
    print(f"Constraints added in time {math.floor(end_const-start_time)} seconds.")
    
    # Set the objective function
    opt_model += max_distance

    # Convert PuLP model to MPS format
    opt_model.writeMPS('model.mps')

    # Create a HiGHS solver instance
    highs = highspy.Highs()
    highs.setOptionValue("time_limit", timelimit)
    highs.setOptionValue("output_flag", False)

    # Read the MPS file into HiGHS
    highs.readModel('model.mps')


    #return solution.model_status
    start = timer()
    # Run the solver
    highs.run()
    end = timer()
    time = math.floor(end - start)
    
    # Get the solution
    solution = highs.getSolution()
    
    # Create a dictionary for fast lookup of variable indices
    variable_index_map = {var.name: idx for idx, var in enumerate(opt_model.variables())}

    for var in opt_model.variables():
        var_index = variable_index_map[var.name]  
        var.varValue = solution.col_value[var_index]  
        
    # Set the model status based on HiGHS output
    status_code = highs.getModelStatus()
    #print(status_code)
    
    # Convert HiGHS status code to a human-readable format
    if status_code == highspy.HighsModelStatus.kOptimal:
        opt_model.status = plp.LpStatusOptimal
        print("Optimal solution found.")
    elif status_code == highspy.HighsModelStatus.kTimeLimit:
        opt_model.status = plp.LpStatusNotSolved  
        print("Timeout.")
    else:
        opt_model.status = plp.LpStatusNotSolved
        print("No solution found.")
    
    # Verify variable values to ensure they are not None
    if all(var.varValue is not None for var in opt_model.variables()):
        if math.isfinite(highs.getObjectiveValue()):
            feasible = True
        else:
            feasible = False
    else:
        feasible = False
   
    best_paths_dict = {}
    if plp.LpStatus[opt_model.status] == 'Optimal':
        is_optimal = True
        if time >= 300:
            time = 300
            is_optimal = False
        for i in range(num_couriers):
            for j in range(num_items+1):
                for k in range(num_items+1):
                        visit_val = visit[i, j, k].varValue
                        if visit_val == None: 
                            continue
                        elif visit_val > 0:
                            best_paths_dict[(i, j)] = k
                        
        best_paths = [[] for _ in range(num_couriers)]
        for i in range(num_couriers):
            k = num_items
            while k != num_items or len(best_paths[i]) == 0:
                if (i, k) in best_paths_dict.keys():
                    if best_paths_dict[(i, k)] != num_items:
                        best_paths[i].append(best_paths_dict[(i, k)] + 1)
                    k = best_paths_dict[(i, k)]
                else:
                    break
    
        best_max_dist = int(highs.getObjectiveValue())
        #print(best_max_dist)
        
        print("Optimal solution found, max distance: ", best_max_dist)
        results = {
            "pulp_HIGHS": {
                "time": time,
                "optimal": is_optimal,
                "obj": best_max_dist,
                "sol": best_paths
            }
        }
        
        # Prepare directories if they don't exist yet
        if not os.path.exists("res"):
            os.mkdir("res")
        if not os.path.exists(os.path.join("res", "MIP")):
            os.mkdir(os.path.join("res", "MIP"))

        results_paths = f"res/MIP/inst{instance}.json"
    
        # Read existing data from the json
        if os.path.exists(results_paths):
            with open(results_paths, "r") as f:
                loaded_data = json.load(f)
        else:
            loaded_data = dict()
        
        for key in results.keys():
            loaded_data[key] = results[key]

        # Creates JSON file with associated data
        with open(results_paths, "w") as json_file:
            json.dump(loaded_data, json_file, indent=4)
    
    elif plp.LpStatus[opt_model.status] != 'Optimal' and feasible == True:
        is_optimal = False
        time = 300  

        best_paths_dict = {}
        for i in range(num_couriers):
            for j in range(num_items + 1):
                for k in range(num_items + 1):
                    visit_val = visit[i, j, k].varValue
                    if visit_val == None: 
                        continue
                    elif visit_val > 0:
                        best_paths_dict[(i, j)] = k
    
        # Construct paths from extracted solutions
        best_paths = [[] for _ in range(num_couriers)]
        for i in range(num_couriers):
            k = num_items
            print(f"Constructing path for Courier {i}")
            loop_counter = 0  # To avoid infinite loops
            while k != num_items or len(best_paths[i]) == 0:
                if (i, k) in best_paths_dict.keys():
                    if best_paths_dict[(i, k)] != num_items:
                        best_paths[i].append(best_paths_dict[(i, k)] + 1)
                    k = best_paths_dict[(i, k)]
                    #print(f"Next node for Courier {i}: {k}")
                else:
                    #print(f"No further path from node {k} for Courier {i}")
                    break
                loop_counter += 1
                if loop_counter > 1000:  # Safety check to prevent infinite loop
                    print(f"Exiting.")
                    results = {
                      "pulp_HIGHS": {
                        "time": time,
                        "optimal": is_optimal,
                        "obj": 0,
                        "sol": "N/A"
                      }
                    }

                    # Prepare directories if they don't exist yet
                    if not os.path.exists("res"):
                        os.mkdir("res")
                    if not os.path.exists(os.path.join("res", "MIP")):
                        os.mkdir(os.path.join("res", "MIP"))
        
                    results_paths = f"res/MIP/inst{instance}.json"
    
                    # Read existing data from the json
                    if os.path.exists(results_paths):
                        with open(results_paths, "r") as f:
                            loaded_data = json.load(f)
                    else:
                        loaded_data = dict()
        
                    for key in results.keys():
                         loaded_data[key] = results[key]

                    # Creates JSON file with associated data
                    with open(results_paths, "w") as json_file:
                        json.dump(loaded_data, json_file, indent=4)
                    return
        
        best_max_dist = int(highs.getObjectiveValue())
        print("Feasible solution found, best_max_dist: ", best_max_dist)

        results = {
            "pulp_HIGHS": {
               "time": time,
               "optimal": is_optimal,
               "obj": best_max_dist,
               "sol": best_paths
            }
        }

        # Prepare directories if they don't exist yet
        if not os.path.exists("res"):
            os.mkdir("res")
        if not os.path.exists(os.path.join("res", "MIP")):
            os.mkdir(os.path.join("res", "MIP"))
        
        results_paths = f"res/MIP/inst{instance}.json"
    
        # Read existing data from the json
        if os.path.exists(results_paths):
            with open(results_paths, "r") as f:
                loaded_data = json.load(f)
        else:
            loaded_data = dict()
        
        for key in results.keys():
            loaded_data[key] = results[key]

        # Creates JSON file with associated data
        with open(results_paths, "w") as json_file:
            json.dump(loaded_data, json_file, indent=4)
            
    else:
        #print(plp.LpStatus[opt_model.status])
        is_optimal = False
        time = 300
        print('No solution found.')
        results = {
            "pulp_HIGHS": {
                "time": time,
                "optimal": is_optimal,
                "obj": 0,
                "sol": "N/A"
            }
        }
        # Prepare directories if they don't exist yet
        if not os.path.exists("res"):
            os.mkdir("res")
        if not os.path.exists(os.path.join("res", "MIP")):
            os.mkdir(os.path.join("res", "MIP"))
        
        results_paths = f"res/MIP/inst{instance}.json"
    
        # Read existing data from the json
        if os.path.exists(results_paths):
            with open(results_paths, "r") as f:
                loaded_data = json.load(f)
        else:
            loaded_data = dict()
        
        for key in results.keys():
            loaded_data[key] = results[key]

        # Creates JSON file with associated data
        with open(results_paths, "w") as json_file:
            json.dump(loaded_data, json_file, indent=4)

    return None