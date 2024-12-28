import os
from timeit import default_timer as timer
import math
import json
from math import floor
from utils import import_data
from z3 import *


def main_smt(instance):
    
    print("Running instance", instance)

    file_name = f"Instances/inst{instance}.dat"
    
    timelimit = 300
    const_limit = 180

    num_couriers, num_items, courier_size, item_size, distances = import_data(file_name)

    print("Defining vars and adding constraints...")

    # Define variables
    visit = [[[Bool(f"visit_{i}_{j}_{k}") for k in range(num_items + 1)] for j in range(num_items + 1)] for i in range(num_couriers)]
    load = [[Bool(f"load_{i}_{j}") for j in range(num_items)] for i in range(num_couriers)]
    u = [[Int(f"u{i}_{j}") for j in range(num_items+1)] for i in range(num_couriers)]

    # Create solver instance
    s = Optimize()

    #----------constraints definition-------------
    start_time = timer()
    try:

        # Each item should be assigned to only one vehicle
        for j in range(num_items):
            s.add(Sum([If(load[i][j], 1, 0) for i in range(num_couriers)]) == 1)
            if timer() - start_time > const_limit:
                raise TimeoutError("Timeout reached while adding constraints")
        
        for i in range(num_items):
            s.add(Sum([If(visit[k][i][j], 1, 0) for k in range(num_couriers) for j in range(num_items + 1)]) == 1)
            if timer() - start_time > const_limit:
                raise TimeoutError("Timeout reached while adding constraints")
        
        for i in range(num_items):
            s.add(Sum([If(visit[k][j][i], 1, 0) for k in range(num_couriers) for j in range(num_items + 1)]) == 1)
            if timer() - start_time > const_limit:
                raise TimeoutError("Timeout reached while adding constraints")
      
        for i in range(num_items):
            for k in range(num_couriers):
                s.add(Sum([If(visit[k][i][j], 1,0) for j in range(num_items+1)]) == Sum([If(visit[k][j][i],1,0) for j in range(num_items + 1)]))
                if timer() - start_time > const_limit:
                   raise TimeoutError("Timeout reached while adding constraints")

        # Ensure consistent visits for each courier
        for i in range(num_items):
            for k in range(num_couriers):
                s.add(Sum([If(visit[k][i][j],1,0) for j in range(num_items + 1)]) == load[k][i])
                if timer() - start_time > const_limit:
                   raise TimeoutError("Timeout reached while adding constraints")
               
        for i in range(num_items):
            for k in range(num_couriers):
                s.add(Sum([If(visit[k][j][i], 1,0) for j in range(num_items + 1)]) == load[k][i])    
                if timer() - start_time > const_limit:
                   raise TimeoutError("Timeout reached while adding constraints")

        # MTZ constraint
        for i in range(num_couriers):
            for j in range(num_items + 1):
                for k in range(num_items + 1):
                    if j != num_items and j != k:
                        s.add(u[i][j] - u[i][k] + num_items * If(visit[i][j][k],1,0) <= num_items - 1)
                        if timer() - start_time > const_limit:
                            raise TimeoutError("Timeout reached while adding constraints")

        # Capacity constraint
        for i in range(num_couriers):
            s.add(Sum([If(load[i][j], item_size[j], 0) for j in range(num_items)]) <= courier_size[i])
            if timer() - start_time > const_limit:
                raise TimeoutError("Timeout reached while adding constraints")
            
        # Ensure no self-loop
        for i in range(num_couriers):
            s.add(Sum([If(visit[i][j][j], 1, 0) for j in range(num_items)]) == 0)
            if timer() - start_time > const_limit:
                raise TimeoutError("Timeout reached while adding constraints")

        # Ensure each courier starts and ends at the depot exactly once
        for k in range(num_couriers):
            s.add(Sum([If(visit[k][num_items][i], 1, 0) for i in range(num_items)]) == 1)
            s.add(Sum([If(visit[k][i][num_items], 1, 0) for i in range(num_items)]) == 1)
            if timer() - start_time > const_limit:
                raise TimeoutError("Timeout reached while adding constraints")

        # Calculate the maximum distance traveled
        max_dist = Int('max_dist')
        for i in range(num_couriers):
            s.add(Sum([If(visit[i][j][k], distances[j][k], 0) for j in range(num_items + 1) for k in range(num_items + 1)]) <= max_dist)
            if timer() - start_time > const_limit:
                raise TimeoutError("Timeout reached while adding constraints")
      
        end_const = timer()
        print(f"Constraints added in time {floor(end_const-start_time)}")
        
    except TimeoutError:
        print("Terminating constraint addition due to timeout.")
        optimal = "false"
        time = 300
        
        if not os.path.exists("res"):
            os.mkdir("res")
        if not os.path.exists(os.path.join("res", "SMT")):
            os.mkdir(os.path.join("res", "SMT"))
        
        results = {
                "Z3": {
                    "time": time,
                    "optimal": optimal,
                    "obj": 0,
                    "sol": "N/A"
                }
        }
        
        results_paths = f"res/SMT/inst{instance}.json"
        
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
        
    # Define the objective function and solve
    s.minimize(max_dist)

    # Set the timeout
    s.set("timeout", timelimit*1000)

    start = timer()
    res = s.check()
    end = timer()
   
    if res == sat:
        optimal = "true"
        print("The problem is satisfiable.")
    elif res == unsat:
        optimal = "false"
        print("The problem is unsatisfiable.")
    else:
        optimal = "false"
        print("Timeout!")

    time = math.floor(end - start)
    # Prepare directories 
    if not os.path.exists("res"):
        os.mkdir("res")
    if not os.path.exists(os.path.join("res", "SMT")):
        os.mkdir(os.path.join("res", "SMT"))
        

    model = s.model()
    best_paths_dict = {}
    for i in range(num_couriers):
         for j in range(num_items + 1):
            for k in range(num_items + 1):
                if is_true(model.eval(visit[i][j][k])):
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

    if res != unsat:
        if  optimal == "false":
            time = 300
        try:
            best_max_dist = model.eval(max_dist).as_long()
            print(best_max_dist)
            results = {
                "Z3": {
                    "time": time,
                    "optimal": optimal,
                    "obj": best_max_dist,
                    "sol": best_paths
                }
            }
        except AttributeError:
            results = {
                "Z3": {
                    "time": time,
                    "optimal": optimal,
                    "obj": 0,
                    "sol": "N/A"
                }
            }
                     
        results_paths = f"res/SMT/inst{instance}.json"
        
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
        time = 300
        print("No solution found")
        results = {
                "Z3": {
                    "time": time,
                    "optimal": optimal,
                    "obj": 0,
                    "sol": "N/A"
                }
        }
        
        results_paths = f"res/SMT/inst{instance}.json"
        
        # Read existing data from the json
        if os.path.exists(results_paths):
            with open(results_paths, "r") as f:
                loaded_data = json.load(f)
        else:
            loaded_data = dict()
        
        for key in results.keys():
            loaded_data[key] = results[key]

        # Creates JSON file with the data
        with open(results_paths, "w") as json_file:
            json.dump(loaded_data, json_file, indent=4)

        