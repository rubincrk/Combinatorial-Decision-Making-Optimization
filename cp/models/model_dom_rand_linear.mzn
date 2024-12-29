%include "globals.mzn";
include "alldifferent.mzn";
include "bin_packing_capa.mzn";
include "count_eq.mzn";


int: num_items; % Item number
int: num_couriers; % Vehicle number
array [1..num_couriers] of int: courier_size; % Vehicle capacities
array [1..num_items] of int: item_size; % Item sizes 

set of int: NODES = 1..num_items+1;
set of int: ITEMS = 1..num_items;
set of int: VEHICLES = 1..num_couriers;

array [NODES,NODES] of int: distances;
int: max_load = max(courier_size) + 1;
array[VEHICLES,NODES] of var 1..num_items+1: succ;
array[ITEMS] of var VEHICLES: courier_assignment; 

array[ITEMS] of var ITEMS: u; 
int: lb;
int: ub;

     
               
% Each item should be distributed only once
constraint forall(i in ITEMS) (
    count_eq(succ[..,i], i, num_couriers-1)
);

% Subtour constraint
constraint forall(i in VEHICLES)(
    forall(j in ITEMS)(
        if j != succ[i, j] /\ succ[i, j] != num_items+1 then 
            u[j] < u[succ[i, j]] 
        endif
    )
);

% Same vehicle cannot visit the same node again
constraint forall(i in VEHICLES)(
    alldifferent(succ[i, ..])
);

% Link courier_assignment to succ to represent courier assignment
constraint forall(i in ITEMS, j in VEHICLES)(
    (succ[j, i] != i) -> (courier_assignment[i] = j)
);

% Capacity constraint using bin packing capa
constraint bin_packing_capa(courier_size, courier_assignment, item_size);

% Ensure that each vehicle visits the depot exactly once after deliveries
constraint forall(j in VEHICLES)(
    count_eq([succ[j, i] | i in ITEMS], num_items+1, 1)
);

var lb..ub: max_dist = max(j in VEHICLES)(
    sum(i in NODES)(distances[i, succ[j, i]])
);

% Ensure each vehicle performs at least one delivery
constraint forall(j in VEHICLES)(
       succ[j, num_items+1] != num_items+1
);


ann:search_ann;

search_ann = int_search(succ, dom_w_deg, indomain_random);

       
%for LNS
%include "gecode.mzn";

solve 
   :: search_ann
   %:: restart_luby(250)
   :: restart_linear(250)
   %:: relax_and_reconstruct(succ_flattened, 55)
   minimize max_dist;  

               
output [
    "succ = ", show(succ), "\n",
    "u = ", show(u), "\n",
    "max_dist = ", show(max_dist), "\n"
];