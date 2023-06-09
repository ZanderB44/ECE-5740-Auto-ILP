from typing import Dict, List
import copy
import networkx as nx
import matplotlib.pyplot as plt
import sys
import os

def main():
    minimizeLatency = False
    minimizeMemory = False
    schedulingMethod = ""

    # createGraph()
    nodeWeights = {}
    # findAllPaths()
    allPaths = []
    # ASAPNodes()
    nodesASAP = {}
    # ALAPNodes()
    nodesALAP = {}
    # createVariables()
    variables = {}
    # variablesWithSteps()
    variableStrings = {}
    # exeConstraints()
    eConstraint = []
    # depConstraints()
    dConstraint = []
    dConstraintNodes = {}
    # resConstraints()
    rConstraint = []
    #runGLPKPareto
    feasibleCoords = []
    #criticalPath()
    longestPath = 0

    if "-l" in sys.argv:
        latencyIndex = sys.argv.index("-l")
        latency =  int(sys.argv[latencyIndex + 1])
        minimizeMemory = True
        

    if "-a" in sys.argv:
        memoryIndex = sys.argv.index("-a")
        memory =  int(sys.argv[memoryIndex + 1])
        minimizeLatency = True

    if "-g" in sys.argv:
        fileIndex = sys.argv.index("-g")
        file = sys.argv[fileIndex + 1]

    if (minimizeLatency & minimizeMemory):
        print("PARETO-OPTIMAL ANALYSIS")
        schedulingMethod = "Pareto-Optimal"
    elif (minimizeLatency & ~minimizeMemory):
        print("LATENCY MINIMIZATION")
        schedulingMethod = "Latency"
    else:
        print("MEMORY MINIMIZATION")
        schedulingMethod = "Memory"
    
    match schedulingMethod:
        case "Pareto-Optimal":
            G = createGraph(file, nodeWeights)
            source = findSource(G)
            sink = findSink(G)
            findAllPaths(G, source, sink, allPaths)
            longestPath = criticalPath(allPaths)
            for testLatency in range(longestPath, latency):
                if (longestPath > testLatency):
                    print(f"==========================LATENCY: {testLatency} IS INFEASIBLE==========================")
                    continue
                    # end minimization
                ASAPNodes(G, nodesASAP)
                ALAPNodes(G, nodesALAP, testLatency)
                ALAP(allPaths, nodesALAP, testLatency)
                ASAP(allPaths, nodesASAP)
                createVariables(G, variables)
                stepLocations(variables, nodesASAP, nodesALAP)
                variablesWithSteps(variables, variableStrings)
                removeSource(variableStrings)
                exeConstraints(eConstraint, variableStrings)
                depConstraints(G, dConstraintNodes, variableStrings, dConstraint)
                testMemory = max(nodeWeights.values())
                for testMemory in range(int(max(nodeWeights.values())), memory): # Runs resConstraints for any value between 0 and # of nodes
                    if (max(nodeWeights.values()) > testMemory):
                        print(f"==========================MEMORY: {testMemory} IS INFEASIBLE==========================")
                        continue
                    if (testMemory == 0):
                        continue
                    else:
                        resConstraints(variableStrings, nodeWeights, testMemory, rConstraint)
                        # write text file
                        writeILP (variableStrings, rConstraint, dConstraint, eConstraint, testMemory)
                        if(runGLPKPareto(testMemory, testLatency, memory, feasibleCoords)):
                            rConstraint.clear()
                            break
                    rConstraint.clear()
                nodesALAP.clear()
                variables.clear()
                variableStrings.clear()
                eConstraint.clear()
                dConstraint.clear()
                dConstraintNodes.clear()
                longestPath = 0
            runParetoOpt(feasibleCoords, memory, latency)
        case "Latency":
            G = createGraph(file, nodeWeights)
            source = findSource(G)
            sink = findSink(G)
            findAllPaths(G, source, sink, allPaths)
            ASAPNodes(G, nodesASAP)
            ASAP(allPaths, nodesASAP)
            longestPath = criticalPath(allPaths)
            maxVal = max(nodeWeights.values())
            if ((maxVal) > memory):
                print(f"==========================MEMORY: {memory} IS INFEASIBLE==========================")
                sys.exit(f"ERROR: Memory Constraint Is Less Than Maximum Node Weight: {maxVal}")
            testLatency = longestPath
            while(True):
                ALAPNodes(G, nodesALAP, testLatency)
                ALAP(allPaths, nodesALAP, testLatency)
                createVariables(G, variables)
                stepLocations(variables, nodesASAP, nodesALAP)
                variablesWithSteps(variables, variableStrings)
                removeSource(variableStrings)
                exeConstraints(eConstraint, variableStrings)
                depConstraints(G, dConstraintNodes, variableStrings, dConstraint)
                resConstraints(variableStrings, nodeWeights, memory, rConstraint)
                # write text file 
                writeILP (variableStrings, rConstraint, dConstraint, eConstraint, memory)
                if(runGLPK(memory, testLatency)):
                    print(f"===================================================")
                    print(f"MIN LATENCY WITH MEMORY = {memory} IS {testLatency}")
                    print(f"===================================================")
                    break
                testLatency = testLatency + 1
                nodesALAP.clear()
                variables.clear()
                variableStrings.clear()
                eConstraint.clear()
                dConstraint.clear()
                dConstraintNodes.clear()
                rConstraint.clear()
        case "Memory":
            G = createGraph(file, nodeWeights)
            source = findSource(G)
            sink = findSink(G)
            findAllPaths(G, source, sink, allPaths)
            ASAPNodes(G, nodesASAP)
            ALAPNodes(G, nodesALAP, latency)
            ASAP(allPaths, nodesASAP)
            ALAP(allPaths, nodesALAP, latency)
            createVariables(G, variables)
            stepLocations(variables, nodesASAP, nodesALAP)
            variablesWithSteps(variables, variableStrings)
            longestPath = criticalPath(allPaths)
            if (longestPath > latency):
                print(f"==========================LATENCY: {latency} IS INFEASIBLE==========================")
                sys.exit(f"ERROR: Latency Constraint Less Than Critical Path Length: {longestPath}")
                # end minimization
            removeSource(variableStrings)
            exeConstraints(eConstraint, variableStrings)
            depConstraints(G, dConstraintNodes, variableStrings, dConstraint)
            testMemory = max(nodeWeights.values())
            while(True):
                if (testMemory == 0):
                    continue
                else:
                    resConstraints(variableStrings, nodeWeights, testMemory, rConstraint)
                    # write text file
                    writeILP (variableStrings, rConstraint, dConstraint, eConstraint, testMemory)
                    if(runGLPK(testMemory, latency)):
                        print(f"===================================================")
                        print(f"MIN MEMORY WITH LATENCY = {latency} IS {testMemory}")
                        print(f"===================================================")
                        break
                rConstraint.clear()
                print("rConstraint cleared")
                testMemory = testMemory + 1
        case _:
            print("error")

# Creates and returns the graph G
def createGraph (file, nodeWeights):
    # Read the DFG from an external file in edge-list format
    filename = file # Pull this from filename
    G = nx.read_weighted_edgelist(filename, create_using = nx.DiGraph, nodetype = int)

    # Add source and sink nodes
    firstNode = -1
    G.add_node(firstNode)
    lastNode = max(G.nodes())

    # Assign a weight to each node. Node weight is the sum of all fan-out edge weights
    for node in G.nodes():
        nodeWeights.update({node : 0})
    for node in G.nodes():
        if (len(list(G.successors(node))) != 0):
            for successor in G.successors(node):
                nodeWeights[node] = nodeWeights[node] + G[node][successor]["weight"]

    edgesToAdd = []
    for node in G.nodes():
        if ((len(list(G.predecessors(node))) == 0) & (node != firstNode)):
            edgesToAdd.append([-1, node])
    G.add_edges_from(edgesToAdd)

    nodesToRemove = []
    for node in G.nodes():
        if (len(list(G.successors(node))) == 0):
            nodesToRemove.append(node)
    G.remove_nodes_from(nodesToRemove)

    G.add_node(lastNode + 1)
    lastNode = max(G.nodes())

    edgesToAdd2 = []
    for node in G.nodes():
        if ((len(list(G.successors(node))) == 0) & (node != lastNode)):
            edgesToAdd2.append([node, lastNode])
    G.add_edges_from(edgesToAdd2)

    for node in nodesToRemove:
        if node in nodeWeights:
            del nodeWeights[node]

    return G

# Finds and returns the source node of the graph
def findSource (G):
    source = min(G.nodes())
    return source

# Finds and returns the sink node of the graph
def findSink (G):
    source = max(G.nodes())
    return source

# Find all paths from source to sink
def findAllPaths (G, src : int, dst : int, allPaths : List[List[int]]):
    path = []
    path.append(src)

    DFS(G, src, dst, path, allPaths)

# Depth-First Search, called in findAllPaths()
def DFS (G, src : int, dst : int, path : List[int], allPaths : List[List[int]]):
    if (src == dst):
        allPaths.append(copy.deepcopy(path))
    else:
        for adjNode in G.successors(src):
            path.append(adjNode)
            DFS(G, adjNode, dst, path, allPaths)
            path.pop()

def criticalPath (allPaths):
    longestPath = 0
    for path in allPaths:
        if (len(path) > longestPath):
            longestPath = len(path)
    longestPath = longestPath - 1
    return longestPath

def ASAPNodes (G, nodesASAP : dict({})):
    for i in G.nodes():
        nodesASAP.update({i : 0})

def ALAPNodes (G, nodesALAP : dict({}), latency):
    for i in G.nodes():
        nodesALAP.update({i : latency})

# Find the earliest step location of each node
def ASAP (allPaths : List[List[int]], nodesASAP : Dict[int, int]):
    for paths in allPaths:
        for node in paths:
            #minimize
            if (paths.index(node) > nodesASAP[node]):
                nodesASAP[node] = paths.index(node)

# Find the latest step location of each node
def ALAP (allPaths : List[List[int]], nodesALAP : Dict[int, int], latency):
    for paths in allPaths:
        pathLength = len(paths)
        shift = latency - pathLength
        for node in paths:
            if ((paths.index(node) + shift) < nodesALAP[node]):
                nodesALAP[node] = paths.index(node) + shift

# Creates a dictionary for the variables. Key = node, Value = List of all possible step locations
def createVariables (G, variables):
    for node in G.nodes():
        variables[node] = []

# Adds all possible step locations to each list of step locations
def stepLocations (variables, nodesASAP, nodesALAP):
    for node in variables:
        for i in range(nodesASAP[node], nodesALAP[node] + 2): # THIS IS PROBABLY NOT THE RIGHT WAY TO DO THIS
            variables[node].append(i)

# Creates a dictionary of all variables. Key = node, Value = all variables in "x1_1" form
def variablesWithSteps (variables, variableStrings):
    for node in variables:
        variableStrings[node] = []
    for node in variables:
        for step in variables[node]:
            variableString = f"x{node}_{step}"
            variableStrings[node].append(variableString)

# Remove the source node
def removeSource (variableStrings):
    del variableStrings[-1]

# Execution constraint: Each node is only executed once
def exeConstraints (eConstraint, variableStrings):
    for node in variableStrings:
        str = ""
        for i in variableStrings[node]:
            str += i
            if (variableStrings[node].index(i) + 1 < len(variableStrings[node])):
                str += " + "
            else:
                str += " = 1"
        eConstraint.append(str)

def depConstraints (G, dConstraintNodes, variableStrings, dConstraint):
    # This will make a dictionary where the key is the original node and the values for that key are all successors of that original node
    for node in G.nodes():
        successorList = []
        if (len(list(G.successors(node))) > 0):
            for successor in G.successors(node):
                successorList.append(successor)
            dConstraintNodes.update({node : successorList})
    del dConstraintNodes[-1]

    # Loop through all nodes and all successors in dConstraintNodes.
    index = 0
    for node in dConstraintNodes:
        for successor in dConstraintNodes[node]:
            eqString = ""
            for var in variableStrings[successor]:
                string = f"x{successor}_"
                if (string in var):
                        vars = var.split("_")
                        weight = vars[1]
                        eqString += str(weight) + "" + var + " + " # Need to figure out how to not add a "+" on the last value
            eqString = eqString.rstrip(eqString[-1])
            eqString = eqString.rstrip(eqString[-1])
            eqString = eqString.rstrip(eqString[-1])
            eqString += " - "
            for var in variableStrings[node]:
                string = f"x{node}_"
                if (string in var):
                    vars = var.split("_")
                    weight = vars[1]
                    eqString += str(weight) + "" + var + " - "
            eqString = eqString.rstrip(eqString[-1])
            eqString = eqString.rstrip(eqString[-1])
            eqString = eqString.rstrip(eqString[-1])
            eqString += " >= 1"
            dConstraint.append(eqString)
            index = index + 1

def resConstraints (variableStrings, nodeWeights, memory, rConstraint):
    # Makes a dictionary of all the variables and their corresponding weights
    numberOfSteps = 0
    for var in variableStrings:
        for step in variableStrings[var]:
            string = step.split("_")
            step = string[1]
            if (int(step) > numberOfSteps):
                numberOfSteps = numberOfSteps + 1
    
    while (numberOfSteps > 0):
        rConstraint.append("")
        numberOfSteps = numberOfSteps - 1

    # Resource constraint: The nodes executed in each step don't overuse the memory constraint
    for var in variableStrings:
        for step in variableStrings[var]:
            if (var == max(variableStrings)):
                continue
            weight = int(nodeWeights[var])
            string = step.split("_")
            string = string[1]
            rConstraint[int(string) - 1] = rConstraint[int(string) - 1] + str(weight) + "" + step + " + "
    rConstraint.pop()
    index = 0
    for step in rConstraint:
        string = step
        string = string.rstrip(string[-1])
        string = string.rstrip(string[-1])
        string = string.rstrip(string[-1])
        step = string
        step += " - mem <= 0"
        rConstraint[index] = step
        index = index + 1

def writeILP (variableStrings, rConstraint, dConstraint, eConstraint, memory):
    constraintList = eConstraint + rConstraint + dConstraint
    objStatement = "mem"
    # Creates a new file called 'formulations.lp' that will be submitted to GLPK
    with open("formulations.lp", "w") as f:
        # Write objective statement (Cunxi said to just write a constant, might be wrong)
        f.write(f"Minimize \nobj: {objStatement}")

        # Write dependency and memory constraints 
        f.write(f"\n\nSubject To\nc0: mem <= {memory}\n")
        for i, const in enumerate(constraintList):
             f.write(f"c{i+1}: {const}\n")

        # Write pos-int constraints 
        count = 1
        for i, variableList in variableStrings.items():
            for variable in variableList:
                f.write(f"i{count}: {variable} >= 0\n")
                count = count + 1

        # Define variables as ints 
        f.write("\nInteger\n")
        for variable in variableStrings.values():
            string_list = " ".join(variable) + " " 
            f.write(f"{string_list}")
        f.write(" mem")     
        
        f.write("\n\nEnd")

def runGLPK(memory, latency):
    # Run glpsol command
    os.system("glpsol formulations.lp --lp -o solution.lp")

    try:
        f = open("solution.lp", "r")
    except OSError:
        print("Could not open/read file")
        sys.exit()

    # Open solution.lp file and check if it contains "INFEASIBLE"
    with f:
        fileContent = f.read()
        if "ERROR" in fileContent:
            print("ILP FORMULATION ERROR")
        elif "INFEASIBLE" in fileContent:
            print(f"==========================MEMORY: {memory}, LATENCY: {latency} IS INFEASIBLE==========================")
            return False
        else:
            #print(f"==========================MEMORY: {memory}, LATENCY: {latency} IS FEASIBLE==========================")
            return True
          
def runGLPKPareto(testMemory, testLatency, memory, feasibleCoords):
    # Run glpsol command
    os.system("glpsol formulations.lp --lp -o solution.lp")

    try:
        f = open("solution.lp", "r")
    except OSError:
        print("Could not open/read file")
        sys.exit()

    # Open solution.lp file and check if it contains "INFEASIBLE"
    with f:
        fileContent = f.read()
        if "ERROR" in fileContent:
            print("ILP FORMULATION ERROR")
            return False
        elif "INFEASIBLE" in fileContent:
            print(f"==========================MEMORY: {testMemory}, LATENCY: {testLatency} IS INFEASIBLE==========================")
            return False
        else:
            #X coord = memory Y = latency
            for memIt in range(testMemory, 2*memory):
                feasibleCoords.append([memIt, testLatency])
            print(f"==========================MEMORY: {testMemory}, LATENCY: {testLatency} IS FEASIBLE==========================")
            return True
          
def runParetoOpt(feasibleCoords, memory, latency):
    # Split coordinates into x and y lists
    x_coords = [coord[0] for coord in feasibleCoords]
    y_coords = [coord[1] for coord in feasibleCoords]

    # Create scatter plot
    plt.scatter(x_coords, y_coords)
    plt.xlabel("MEMORY")
    plt.ylabel("LATENCY")
    plt.title("PARETO OPTIMAL ANALYSIS")

    plt.xlim([0, memory])
    plt.ylim([0, latency])

    # Show plot
    plt.show()

if __name__== "__main__":
    main()
