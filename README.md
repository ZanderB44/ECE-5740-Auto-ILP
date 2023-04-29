# ECE-5740-Auto-ILP

Downoad code from file autoILP.py
Create or download edgelist for minimization
run file with command format: "python autoILP.py -l= (latency upper-bound) -a= (memory upper-bound) -g= (filename)" for Pareto Optimization 
                              "python autoILP.py -a= (memory constriant) -g= (filename)" for Latency Minimization"
                              "python autoILP.py -l= (latency constraint) -g= (filename)" for Memory Minimization"
                              
Must have GLPK installed on computer to run
Must have python 3.10 or newer (match-case statements)
Graph must be in weighted edge-list format: (parent node) (child node) (edge weight)
Graph must not contain any cycles

Error will be displayed if: Latency constraint is smaller than the critical path of the graph
                            Memory constraint is smaller than the largest node of the graph
                            GLPK not accessible
