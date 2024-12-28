import os
from timeit import default_timer as timer
import time
import math
import json
from utils import computeBounds, import_data
import docplex.mp.model as cpx


def main_mip_cplex(instance):
    
    print("Running instance: ", instance)
    file_name = f"Instances/inst{instance}.dat"
    
    timelimit = 300
    num_couriers, num_items, courier_size, item_size, distances = import_data(file_name)

    opt_model = cpx.Model(name="MIP Model")
    

    # --------Create variables--------

    # Binary variable visit
    visit  = {(k,i,j): opt_model.binary_var(name="visit_{0}_{1}_{2}".format(k,i,j)) 
    for k in range(num_couriers) for i in range(num_items + 1) for j in range(num_items + 1)}

    # Binary variable load
    load  = {(i,j): opt_model.binary_var(name="load_{0}_{1}".format(i,j)) 
    for i in range(num_couriers) for j in range(num_items)}
    
    # Integer
    num_visit  = {(i,j): opt_model.integer_var(name="num_visit_{0}_{1}".format(i,j)) 
    for i in range(num_couriers) for j in range(num_items + 1)}

    max_distance  = opt_model.integer_var() 


    start_time = timer()

    # --------Constraints--------

    # Each customer should be visited only once
    constraints = {j : 
        opt_model.add_constraint(
            ct=opt_model.sum(load[i,j] for i in range(num_couriers)) == 1,
            ctname="customer_once{0}".format(j))
        for j in range(num_items)}
    
    
    constraints = {
        (i): opt_model.add_constraint(
            ct=opt_model.sum(visit[k,i,j] for k in range(num_couriers) for j in range(num_items+1)) == 1,
            ctname="1{0}".format(i)
        )
        for i in range(num_items)
    }
    
    constraints = {
        (i): opt_model.add_constraint(
            ct=opt_model.sum(visit[k,j,i] for k in range(num_couriers) for j in range(num_items+1) ) == 1,
            ctname="1{0}".format(i)
        )
        for i in range(num_items)
    }
    
    
    constraints = {
        (i,k): opt_model.add_constraint(
            ct=opt_model.sum(visit[k,i,j] for j in range(num_items+1) ) == opt_model.sum(visit[k,j,i] for j in range(num_items+1)),
            ctname="flow_{0}_{1}".format(i, k)
        )
        for i in range(num_items)
        for k in range(num_couriers)
    }
    
    constraints = {i : 
        opt_model.add_constraint(
            ct=opt_model.sum(visit[k,i,j] for j in range(num_items + 1)) == load[k,i])
        for i in range(num_items) for k in range(num_couriers)}


    constraints = {i : 
        opt_model.add_constraint(
            ct=opt_model.sum(visit[k,j,i] for j in range(num_items + 1)) == load[k,i])
        for i in range(num_items) for k in range(num_couriers)}
    
    
    
    # Ensure no self-loop
    constraints = {i : 
        opt_model.add_constraint(
            ct=opt_model.sum(visit[i,j,j] for j in range(num_items)) == 0)
        for i in range(num_couriers)}


    constraints = {i : 
        opt_model.add_constraint(
            ct=opt_model.sum(load[i,j] * item_size[j] for j in range(num_items)) <= courier_size[i])
        for i in range(num_couriers)}


    constraints = {k : 
        opt_model.add_constraint(
            ct=opt_model.sum(visit[k,num_items,i] for i in range(num_items)) == 1)
        for k in range(num_couriers)}

    constraints = {k : 
        opt_model.add_constraint(
            ct=opt_model.sum(visit[k,i,num_items] for i in range(num_items)) == 1)
        for k in range(num_couriers)}

    constraints = {i : 
        opt_model.add_constraint(
            ct=opt_model.sum(visit[i,j,k] * distances[j][k] for j in range(num_items + 1) for k in range(num_items + 1)) <= max_distance)
        for i in range(num_couriers)}


    constraints = {
        (i, j, k): opt_model.add_constraint(
            num_visit[i, j] - num_visit[i, k] + (num_items) * visit[i, j, k] <= (num_items - 1),
            ctname="mtz_{0}_{1}_{2}".format(i, j, k)
        )
        for i in range(num_couriers)
        for j in range(num_items + 1)
        for k in range(num_items + 1)
        if j != k and j != num_items 
    }
    
    
    end_const = timer()
    print(f"Constraints added in time {math.floor(end_const-start_time)}")
    
    opt_model.set_time_limit(timelimit)
    
    opt_model.minimize(max_distance)
    
    start = timer()
    
    status = opt_model.solve()

    end = timer()
    time = math.floor(end - start)

    

    best_paths_dict = {}
    if opt_model.solve_status.name == "OPTIMAL_SOLUTION":
        is_optimal = True
        for i in range(num_couriers):
            for j in range(num_items+1):
                for k in range(num_items+1):
                    if visit[i,j,k].solution_value > 0:
                        best_paths_dict[(i, j)] = k
                        
        best_paths = [[] for i in range(num_couriers)]
        for i in range(num_couriers):
            k = num_items
            while k != num_items or len(best_paths[i]) == 0:
                if (i, k) in best_paths_dict.keys():
                    if best_paths_dict[(i, k)] != num_items:
                        best_paths[i].append(best_paths_dict[(i, k)] + 1)
                    k = best_paths_dict[(i, k)]
                else:
                    break
    
        best_max_dist = int(max_distance.solution_value)
        print("Optimal solution found, max distance: ", best_max_dist)
        results = {
                "cplex": {
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
    
    elif opt_model.solve_status.name == "FEASIBLE_SOLUTION":
        is_optimal = False
        time = 300
        print('The problem does not have an optimal solution.')
        if int(max_distance.solution_value) > 10000:
            results = {
                    "cplex": {
                        "time": time,
                        "optimal": is_optimal,
                        "obj": 0,
                        "sol": "N/A"
                    }
            }
        
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
            for i in range(num_couriers):
                for j in range(num_items+1):
                    for k in range(num_items+1):
                        if visit[i,j,k].solution_value > 0:
                            best_paths_dict[(i, j)] = k
                        
            best_paths = [[] for i in range(num_couriers)]
            for i in range(num_couriers):
                k = num_items
                while k != num_items or len(best_paths[i]) == 0:
                    if (i, k) in best_paths_dict.keys():
                        if best_paths_dict[(i, k)] != num_items:
                            best_paths[i].append(best_paths_dict[(i, k)] + 1)
                        k = best_paths_dict[(i, k)]
                    else:
                        break
            
            best_max_dist = int(max_distance.solution_value)
            print("Max distance: ", best_max_dist)
            results = {
                    "cplex": {
                       "time": time,
                       "optimal": is_optimal,
                       "obj": best_max_dist,
                       "sol": best_paths
                    }
            }
            
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
        print("No value for the objective function was found.")
        time = 300
        is_optimal = False
        results = {
                "cplex": {
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
      
   