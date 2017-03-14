#-*- coding: utf-8 -*-
#@author: ilyass.tabiai@polymtl.ca
#@author: rolland.delorme@polymtl.ca
#@author: patrick.diehl@polymtl.ca
import numpy as np
import csv
import os
import sys

## Class handeling the discrete nodes
class Geometry():
    ## Constructor
    def __init__(self):
        ## Volume per node
        self.volumes = np.array(0)
        ## Density per node
        self.density = np.array(0)
       
    ## Read the positions, volume, and density of the nodes from the inFile.
    # @param dim Dimension of the nodes
    # @param inFile CSV file with the geometry
    def readNodes(self,dim,inFile):
        if not os.path.exists(inFile):
                print "Error: Could not find " + inFile
                sys.exit(1)
        #Dimension of the problem
        self.dim = dim
        with open(inFile, 'r') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=' ')
            #Skip the first line, because is the header
            next(spamreader)
            length = len(list(spamreader))
            csvfile.seek(0)
            next(spamreader)
           
            ## Amount of nodes
            self.amount = length
            self.volumes = np.empty(length)
            
            if dim >= 1:
                pos_x = np.empty(length)
            if dim >= 2:
                pos_y = np.empty(length)
            if dim >= 3:
                pos_z = np.empty(length)
            
            i = 0
            
            for row in spamreader:
                if dim >= 1:
                    pos_x[i] = np.array(float(row[1]))
                if dim >= 2:
                    pos_y[i] = np.array(float(row[2]))
                if dim >= 3:
                    pos_z[i] = np.array(float(row[3]))
                
                self.volumes[i] = float(row[dim +1])
                i +=1
                
            if dim == 1:
                ## Nodes of the discretization
                self.nodes = np.array(zip(pos_x))
                del pos_x
            if dim == 2:
                self.nodes = np.array(zip(pos_x,pos_y))
                del pos_x
                del pos_y
            if dim >= 3:
                self.nodes = np.array(zip(pos_x,pos_y,pos_z))
                del pos_x
                del pos_y
                del pos_z
                
    ## Computes the min distance between all nodes
    # @param dim The dimension of nodes
    # @return Minimal dim    
    def getMinDist(self,dim):
        tmp = float('inf')
        if dim == 1:
            for i in range(0,self.amount):
                for j in range(0,self.amount):
                    if i != j:
                        val = abs(self.nodes[j]-self.nodes[i])
                        if val < tmp:
                            tmp = val
        if dim == 2:
            for i in range(0,self.amount):
                for j in range(0,self.amount):
                    if i != j:
                        val = np.sqrt(np.power(self.nodes[j][0]-self.nodes[i][0],2) + np.power(self.nodes[j][1]-self.nodes[i][1],2))
                        if val < tmp:
                            tmp = val
        if dim == 3:
            for i in range(0,self.amount):
                for j in range(0,self.amount):
                    if i != j:
                        val = np.sqrt(np.power(self.nodes[j][0]-self.nodes[i][0],2) + np.power(self.nodes[j][1]-self.nodes[i][1],2) + np.power(self.nodes[j][2]-self.nodes[i][2],2))
                        if val < tmp:
                            tmp = val
        return tmp
            
            
