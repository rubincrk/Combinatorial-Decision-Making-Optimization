from ortools.linear_solver import pywraplp
import os
from timeit import default_timer as timer
import time
import math
import json
from utils import computeBounds, import_data
import gc


def main_mip(instance):
            
    print("Running instance", instance)
    file_name = f"Instances/inst{instance}.dat"
    
    num_couriers, num_items, courier_size, item_size, distances = import_data(file_name)
    solver = pywraplp.Solver.CreateSolver('SCIP')


    # Create variables
    visit = [[[solver.IntVar(0, 1, f'visit_{k}_{i}_{j}') for j in range(num_items + 1)] for i in range(num_items + 1)] for k in range(num_couriers)]
    load = [[solver.IntVar(0,1, f'load_{i}_{j}') for j in range(num_items)] for i in range(num_couriers)]
    u = [[solver.IntVar(0, solver.infinity(), f'u_{i}_{j}') for j in range(num_items +1)] for i in range(num_couriers)] 

    #max_distance = solver.IntVar(0, solver.infinity(), 'max_distance')
    lb, ub = computeBounds(distances, num_couriers, num_items)
    max_distance = solver.IntVar(lb, ub, 'max_distance')

    

    # ----------Constraints----------

    #Each customer should be visited only once
    for j in range(num_items):
        solver.Add(sum(load[i][j] for i in range(num_couriers)) == 1)
    
    for i in range(num_items):
        solver.Add(sum(visit[k][i][j] for k in range(num_couriers) for j in range(num_items + 1) ) == 1)
        
    for i in range(num_items):
        solver.Add(sum(visit[k][j][i] for k in range(num_couriers) for j in range(num_items + 1) ) == 1)
    

    for i in range(num_items):
        for k in range(num_couriers):
            solver.Add(sum(visit[k][i][j] for j in range(num_items+1)) == sum(visit[k][j][i] for j in range(num_items + 1)))

    # Ensure no self-loop
    for i in range(num_couriers):
        solver.Add(sum(visit[i][j][j] for j in range(num_items)) == 0)

    # Ensure consistent visits for each courier
    for i in range(num_items):
        for k in range(num_couriers):
            solver.Add(sum(visit[k][i][j] for j in range(num_items + 1)) == load[k][i])\
            
    for i in range(num_items):
        for k in range(num_couriers):
            solver.Add(sum(visit[k][j][i] for j in range(num_items + 1)) == load[k][i])

    # Capacity constraint
    for i in range(num_couriers):
        solver.Add(sum(load[i][j] * item_size[j] for j in range(num_items)) <= courier_size[i])


    # Ensure each courier starts and ends at the depot exactly once
    for k in range(num_couriers):
        solver.Add(sum(visit[k][num_items][i] for i in range(num_items)) == 1)
        solver.Add(sum(visit[k][i][num_items] for i in range(num_items)) == 1)

    for i in range(num_couriers):
        solver.Add(sum(visit[i][j][k] * distances[j][k] for j in range(num_items + 1) for k in range(num_items + 1)) <= max_distance)


    # MTZ constraint
    for i in range(num_couriers):
        for j in range(num_items + 1):
            for k in range(num_items + 1):
                if j != num_items and j != k:
                    solver.Add(u[i][j] - u[i][k] + num_items * visit[i][j][k] <= num_items - 1)


    solver.Minimize(max_distance)
    solver.set_time_limit(300000)   
        
            
    print("Constraint defined, starting the solving process...")
    start = timer()
    status = solver.Solve()
    end_time = timer()
    
    time = math.floor(end_time - start)
        
    solver_name = "ortools"

    best_paths_dict = {}
    if status == pywraplp.Solver.OPTIMAL:
        is_optimal = True
        for i in range(num_couriers):
            for j in range(num_items+1):
                for k in range(num_items+1):
                    if visit[i][j][k].solution_value() > 0:
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
        
        best_max_dist = int(max_distance.solution_value())
        print("Optimal solution found, best_max_dist: ", best_max_dist)
        results = {
            solver_name: {
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
        
    elif  status == pywraplp.Solver.FEASIBLE:
        is_optimal = False
        time = 300
        for i in range(num_couriers):
            for j in range(num_items+1):
                    for k in range(num_items+1):
                        if visit[i][j][k].solution_value() > 0:
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
        
        best_max_dist = int(max_distance.solution_value())
        print("Feasible solution found, best_max_dist: ", best_max_dist)
        results = {
            solver_name: {
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
        is_optimal = False
        time = 300
        print('The problem does not have a solution.')
        results = {
            solver_name: {
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
    
    # Free memory by deleting variables
    del visit, load, u, max_distance
    del solver
    del num_couriers, num_items, courier_size, item_size, distances
    gc.collect()
    
    return None