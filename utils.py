import os
import json
import glob


def create_dzn(path):
    for filename in glob.glob(os.path.join(path, '*.dat')):
        with open(os.path.join(os.getcwd(), filename), 'r') as f: 
            data = f.read().strip().splitlines()

         # Parse the data
        num_couriers = int(data[0])
        num_items = int(data[1])
        courier_size = [int(x) for x in data[2].split()]
        item_size = [int(x) for x in data[3].split()]
        distances = [[int(x) for x in line.split()] for line in data[4:]]
        
        fname = os.path.basename(filename)
        instance = os.path.splitext(fname)[0]
        
        if not os.path.exists("cp/Instances"):
            os.mkdir("cp/Instances")
    
        new_file = f"cp/Instances/{instance}.dzn"
        if os.path.exists(new_file):
            break

        # Write to the file
        with open(new_file, 'x') as f:
            f.write(f"num_couriers = {num_couriers};\n")
            f.write(f"num_items = {num_items};\n")
            f.write(f"courier_size = {courier_size};\n")
            f.write(f"item_size = {item_size};\n")
        
            distance_lines = [
                "| " + ", ".join(map(str, row)) for row in distances
            ]
            distances_str = "\n     ".join(distance_lines)

            f.write(f"distances = [{distances_str}|];\n")

    return None

def insert_bounds_to_file(filename, lb, ub):
    
    with open(filename, 'a+') as dzn_file:
        dzn_file.seek(0)
        
        # Read the content of the file
        content = dzn_file.read()
        
        if "lb" not in content: 
            dzn_file.write(f"lb = {lb};\n")
            
        if "ub" not in content:        
            dzn_file.write(f"ub = {ub};\n")


def output_to_routes(output):
    
    succ = output['succ']
    u = output['u']

    num_items = len(u)
    num_couriers = len(succ) 

    routes = []

    # Iterate over each courier
    for i in range(num_couriers):
        route = []
        # Start from the depot
        current_node = num_items 
        while True:
            # Find the successor of the current node for this courier
            next_node = succ[i][current_node]
            if next_node == num_items + 1:
                # If the next node is the depot, end the route
                break
            route.append(next_node)
            current_node = next_node - 1  

        routes.append(route)

    return routes


def routes_to_json(routes, time, instance, output_dict, model_type, solver):
    
    if output_dict != None:  
        is_optimal = output_dict['optimal']
        if is_optimal == "false":
            time = 300
            
        results = {
                f"{solver}_{model_type}": {
                   "time": time,
                   "optimal": is_optimal,
                   "obj": output_dict['max_dist'],
                   "sol": routes
                }
        }
    else:
        print("No value for the objective function was found.")
        is_optimal = "false"
        time = 300
            
        results = {
            f"{solver}_{model_type}": {
                    "time": time,
                    "optimal": is_optimal,
                    "obj": 0,
                    "sol": "N/A"
            }
        }
    
    if not os.path.exists("res"):
        os.mkdir("res")
    if not os.path.exists(os.path.join("res", "CP")):
        os.mkdir(os.path.join("res", "CP"))
        
    results_paths = f"res/CP/inst{instance}.json"
    
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


def import_data(filename):
    
    with open(filename, 'r') as file:
        data = file.read().strip().splitlines()

        # Assign the first line to the Couriers
        num_couriers = int(data[0])
        
        # Assign the second line to the items
        num_items = int(data[1])

        # Assign the third line to the Couriers' maximum load
        courier_size = [int(x) for x in data[2].split()]

        # Assign the fourth line to the item size
        item_size = [int(x) for x in data[3].split()]

        # Assign the remaining lines to the Distances between locations
        distances = []
        for line in data[4:]:
            distances.append([int(x) for x in line.split()])

    return num_couriers, num_items, courier_size, item_size, distances


def lower_bound(distances, num_items):
    for i in range(num_items):
        simple_path = [distances[num_items][i] + distances[i][num_items]]
    lb = max(simple_path)

    return lb


def upper_bound(distances, num_couriers, num_items):
    max_item_per_courier = num_items-num_couriers+1
    from_depot = max([distances[num_items][i] for i in range(num_items)]) 
    to_depot = max([distances[i][num_items] for i in range(num_items)]) 

    between_items = [max(distances[j][i] for j in range(num_items) if i!=j) for i in range(num_items)]
    between_items.sort(reverse=True)

    return sum(between_items[:max_item_per_courier-1]) + from_depot + to_depot


def computeBounds(distances, num_couriers, num_items):
    return lower_bound(distances, num_items), upper_bound(distances, num_couriers, num_items)

