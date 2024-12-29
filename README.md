# CDMO Project
As the combinatorial decision and optimization expert, students are asked
 to solve the Multiple Couriers Planning (MCP) problem which is defined as
 follows. <br>
 We have m couriers that must distribute n ≥ m items at different
 customer locations. <br>
 Each courier 'i' has a maximum load size 'l_i'. <br> 
 Each item 'j' has a distribution point 'j' and a size 'sj' (which can represent for instance a weight or a volume). <br>
 The goal of MCP is to decide for each courier the items to be distributed and plan a tour (i.e. a sequence of location points to visit) to perform the necessary distribution tasks.<br>
 Each courier tour must start and end at a given origin point 'o'. <br>
 Moreover, the maximum load 'l_i' of the courier 'i' should be respected when items are assigned to it. <br>
 To achieve a fair division among drivers, the objective is to minimize the maximum distance travelled by any courier.<br>
The project work involves approaching the problem using (i) Constraint Programming (CP), (ii) propositional SATisfiability (SAT) and/or its extension to Satisfiability Modulo Theories (SMT), and
 (iii) Mixed-Integer Linear Programming (MIP).<br>
 For the Constraint Programming part it was used MiniZinc, for the SMT part it was used the Z3 solver while the MIP was implemented using OR-Tools’ python library, PuLP and the CPLEX Python API Docplex. <br>
 For OR-Tools was used the solver SCIP while for PuLP were used both CBC and HIGHS.


## Docker instructions

Open the terminal on the project folder and run the following command to build the docker image.

```bash
docker build . -t cdmo
```
Then run the following command to start the container: 

```bash
docker run -it cdmo
```

## Models usage
### All at once

To run all the models at once, you can simply use: 

```python

python3 main.py
```
This command will run all the models available in the following order: CP -> SMT -> MIP.
##### Notes
<p>Due to the limited memory available in a Docker container, running large instances can cause memory issues, particularly with the MIP models, leading Docker to kill the process and halt execution. To prevent interruptions caused by insufficient memory, the OR-Tools model is executed for the first 10 instances and for instances 13 and 16, which are the ones the model was able to solve. The other instances are skipped to avoid failed attempts at finding a solution that could disrupt the function's execution.
Since in PuLP the solvers are slow, during the execution of the most complex instances the model not only fails to provide a solution, but it also fails to respect the timelimit. Thus, in the case of PuLP with CBC only the first 10 instances were solved, all the others were put to N/A and ignored during the execution of it. The Highs solver, however, is capable of producing a result also for instance 16.
So, in the "all_at_once" function, the PuLP model with the CBC solver is run only for the first 10 instances, whereas the model using the Highs solver is also executed for instance 16.
</p>

### CP
Two solvers were used for the CP part: gecode and chuffed.
The models available for ```gecode``` are: ```"dom_w_deg_rand_linear", "dom_w_deg_rand_luby", "fail_rand_lin_SB", "fail_rand_lin", "fail_rand_luby", "fail_rand_luby_SB"```.

For ```chuffed``` we have: ```"fail_min", "fail_min_SB", "fail_split", "fail_split_SB"```.
    
For example, to execute one specific model on a particular instance using ```gecode``` as a solver, you can run:

```python

python3 main.py gecode fail_rand_luby 07 
```
This command will run the model that uses ```first_fail``` and ```indomain_random``` search with ```luby``` restart on instance ```07``` using ``` gecode ``` solver.

The same thing can be done when using the solver ```chuffed```.

```python
python3 main.py chuffed fail_min 07 
```
This command will run the model that uses ```first_fail``` and ```indomain_min``` search without restart on instance ```07``` using ```chuffed```.
<u>Just remember to use the available models for the different solvers, and to put a 0 when the instance number is < 10 like we did in the example above.</u>

### SMT
To run the SMT model on a particular instance, use:
```python
python3 main.py smt <instance_number>
``` 


### MIP
To run the MIP model on a particular instance with ```ortools```, use:

```python
python3 main.py mip_ortools <instance_number>
``` 
To use ```pulp``` instead of ```ortools```, run the command:

```python
python3 main.py mip_pulp <instance_number>
``` 
Note that when specifying the ```instance_number``` both in the ```mip``` and ```smt``` you should <u>not</u> use the ```<>```.
When using ```pulp``` the command will launch the execution using both CBC and HIGHS solvers.
Since ```docplex``` is a commercial product, it would have not been possible to reproduce the results without a license, so we provided free alternatives like ```ortools``` and ```PuLP```. 
As for the "all_at_once" case, it is recommended to run both mip models only on the solved instances that can be found in the report. 

### Solution checker
The execution of the models will automatically save the results in json format in the ```res``` folder of the container, or in the ```res``` folder of the machine if it's run locally.
To run the solution checker provided, use the following command:

```python
python3 solution_check.py Instances res/
``` 
