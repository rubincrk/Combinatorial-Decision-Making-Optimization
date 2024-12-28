# CDMO Project

Models using MiniZinc, SMT and MIP in order to solve the multiple couriers planning problem.

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