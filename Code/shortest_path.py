#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed May 16 21:01:24 2018

@author: ericgero
"""

from gurobipy import *
import matplotlib.pyplot as plt
import networkx as nx

# read the setup file
f = open("graph_setup.txt", "r")
line = f.readline()
line = line.strip('\n')

data = line.split(':')
num_nodes = int(data[1])

line = f.readline()
line = line.strip('\n')
data = line.split(':')
num_arcs = int(data[1])

line = f.readline()
line = line.strip('\n')
data = line.split(':')
origin = int(data[1])

line = f.readline()
line = line.strip('\n')
data = line.split(':')
destination = int(data[1])

f.close()

links = tuplelist()
miles  = {}
temps = {}
cost = {}
construction = {}
drive_times = {}

# read the data
f = open("full_data.txt", "r")
line = f.readline()
line = f.readline()
# read remaining lines from file and assign to variable
while(len(line)):
    line = line.strip('\n')
    data = line.split()
    from_node = int(data[0])
    to_node = int(data[1])
    miles_arc = float(data[2])
    temps_arc = float(data[3])
    cost_arc = float(data[4])
    construction_arc = float(data[5])
    drive_time_arc = float(data[6])

    links.append((from_node, to_node))
    miles[from_node, to_node] = miles_arc
    temps[from_node, to_node] = temps_arc
    cost[from_node, to_node] = cost_arc
    construction[from_node, to_node] = construction_arc
    drive_times[from_node, to_node] = drive_time_arc

    line = f.readline()
f.close() 

miles_target = 2228
cost_target = 1209.87
drive_times_target = 2056

# get model type to run
print('1. Optimize by miles.')
print('2. Optimize by cost.')
print('3. Optimize by driving time.')
print('4. Optimize by miles, cost and driving time (MOLP)')
user_input = raw_input('Enter model to optimize: ')

try:
    user_input = int(user_input)
except ValueError:
    print('Input not valid, running miles optimization.\n\n')
    user_input = 1

if user_input == 1:
    optimize_me = miles
    v_name = 'miles'
if user_input == 2:
    optimize_me = cost
    v_name = 'cost'
if user_input == 3:
    optimize_me = drive_times
    v_name = 'drive_times'
if user_input == 4:
    optimize_me = drive_times
    v_name = 'drive_times'

# create model and add variables
m = Model('SP')

if user_input != 4:
    m.ModelSense = GRB.MINIMIZE
    x = m.addVars(links, obj = optimize_me, name = v_name, vtype = GRB.BINARY)

if user_input == 4:
    x = m.addVars(links, name = 'flow', vtype = GRB.BINARY)
    # set the objectives
    miles_objective = LinExpr()
    cost_objective = LinExpr()
    driving_objective = LinExpr()
    for vars in x:
        miles_objective += miles[vars] * x[vars]
        cost_objective += cost[vars] * x[vars]
        driving_objective += drive_times[vars] * x[vars]
    
    m.setObjectiveN(miles_objective, index = 0, priority = 1, weight = 1, name = 'Miles')
    m.setObjectiveN(cost_objective, index = 1, priority = 2, weight = 1, name = 'Cost')
    m.setObjectiveN(driving_objective, index = 2, priority = 3, weight = 1, name = 'Drive Time')

# add constraints and solve
for i in range(1, num_nodes + 1):
    m.addConstr( sum(x[i,j] for i,j in links.select(i, '*')) - sum(x[j,i] for j,i in links.select('*',i)) == 
                     (1 if i == origin else - 1 if i == destination else 0 ),'node%s_' % i )

# add conditional constraint if temperature < 32
for i,j in links:
       if(temps[i,j] < 32):
           m.addConstr(x[i,j] == 0)
    
m.optimize() 

# print the optimal solution
if m.status == GRB.Status.OPTIMAL:
   print('The final solution is:')
   for i,j in links:
       if(x[i,j].x > 0):
           #print(i, j, x[i,j].x)
           print('Leg', i, j)
 
# plot the graph
fig = plt.figure(figsize=(20, 10))          
G=nx.DiGraph()
list_nodes = list(range(1, num_nodes + 1))
G.add_nodes_from(list_nodes)
for i,j in links:
    G.add_edge(i,j)

# Adding the position attribute to each node
node_pos = {1:(0, 0), 2:(10, 2), 3:(10, -2), 4:(20, 0), 5:(30, 2), 6:(30, -2), \
            7:(40, 0), 8:(50, 2), 9:(50, -2), 10:(60, 0), 11:(70, 2), 12:(70, -2), \
            13: (80, 0), 14:(90, 2), 15:(90, -2), 16:(100, 0), 17:(110, 2), 18:(110, -2), \
            19:(120, 0), 20:(130, 2), 21:(130,-2), 22:(140, 0), 23:(150, 2), 24:(150, -2), \
            25:(160,0)}

# Create a list of edges in shortest path
red_edges = [(i,j) for i,j in links if x[i,j].x > 0]

#Create a list of nodes in shortest path
sp = [ i for i,j in links if x[i,j].x > 0 ]
sp.append(destination)

# If the node is in the shortest path, set it to red, else set it to white color
node_col = ['gray' if not node in sp else 'green' for node in G.nodes()]

# If the edge is in the shortest path set it to red, else set it to white color
edge_col = ['white' if not edge in red_edges else 'green' for edge in G.edges()]

# Draw the nodes
nx.draw_networkx(G,node_pos, node_color = node_col, node_size = 450)

# Draw the node labels
# nx.draw_networkx_labels(G, node_pos,node_color= node_col)

# Draw the edges
nx.draw_networkx_edges(G, node_pos, edge_color = edge_col)

# Draw the edge labels
nx.draw_networkx_edge_labels(G, node_pos, edge_color = edge_col, edge_labels = optimize_me)

# Remove the axis
plt.axis('off')

# Show the plot
plt.savefig("Graph.png", format="PNG")
plt.show()

# Sensitivity analysis
#edges = [(i,j) for i,j in links if x[i,j].x > 0]
#for x in edges:
#    print(optimize_me)

# rerun model and save sensitivity analysis info
#if m.status != GRB.Status.OPTIMAL:
#    print('Optimization ended with status %d' % m.status)
#    exit(0)

# Store the optimal solution
origObjVal = m.ObjVal
for v in m.getVars():
    v._origX = v.X

# Disable solver output for subsequent solves
m.Params.outputFlag = 0

# Iterate through unfixed, binary variables in model
for v in m.getVars():
    if (v.LB == 0 and v.UB == 1 \
        and (v.VType == GRB.BINARY or v.VType == GRB.INTEGER)):

        # Set variable to 1-X, where X is its value in optimal solution
        if v._origX < 0.5:
            v.LB = v.Start = 1
        else:
            v.UB = v.Start = 0

        # Update MIP start for the other variables
        for vv in m.getVars():
            if not vv.sameAs(v):
                vv.Start = vv._origX

        # Solve for new value and capture sensitivity information
        m.optimize()

        if m.status == GRB.Status.OPTIMAL:
            print('Objective sensitivity for variable %s is %g' % \
                  (v.VarName, m.ObjVal - origObjVal))
        else:
            print('Objective sensitivity for variable %s is infinite' % \
                  v.VarName)

        # Restore the original variable bounds
        v.LB = 0
        v.UB = 1

