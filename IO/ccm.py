# -*- coding: utf-8 -*-
#@author: ilyass.tabiai@polymtl.ca
#@author: rolland.delorme@polymtl.ca
#@author: patrick.diehl@polymtl.ca
import numpy as np
from scipy import linalg
import sys
np.set_printoptions(threshold='nan')

## Class to compute, as a vector state, the global internal volumic force of an elastic material using its material properties
class CCM_calcul():

    ## Constructor
    # @param deck The input deck
    # @param problem The related peridynamic problem
    # @param y The actual postions
    def __init__(self, deck, problem):
        ## Scalar influence function
        self.x = deck.geometry.nodes
        self.y = problem.y
        self.force_int = problem.force_int
        self.ext = problem.ext
        
        self.dim = deck.dim
        self.num_nodes = deck.num_nodes
        self.time_steps = deck.time_steps
        self.node_volumes = deck.geometry.volumes        
        self.influence_function = deck.influence_function
        
        #self.compute_u_displacement()

    # Compute the displacement for each node
    def compute_u_displacement(self):
        self.u = np.zeros((self.num_nodes, self.dim, self.time_steps),dtype=np.float64)
        for t_n in range(1, self.time_steps):
            for i in range(0, self.num_nodes):
                self.u[i,:,t_n] = self.y[i,:,t_n] - self.y[i,:,t_n-1]
            
    # Return the image of (xi - xp) under the reference position vector state X 
    def X_vector_state(self, problem, i, p):
        image = self.x[p,:] - self.x[i,:]
        image = np.reshape(image,(self.dim,1))
        return image

    # Return the image of (xi - xp) under the deformation vector state Y 
    def Y_vector_state(self, problem, i, p, t_n):
        image = self.y[p,:,t_n] - self.y[i,:,t_n]
        image = np.reshape(image,(self.dim,1))
        return image
        
    # Return the shape tensor K related to node i
    def K_shape_tensor(self, problem, i):
        K = np.zeros((self.dim, self.dim),dtype=np.float64)
        index_x_family = problem.neighbors.get_index_x_family(i)
        for p in index_x_family:
            X = self.X_vector_state(problem, i, p)
            K += self.influence_function * np.dot(X,X.T) * self.node_volumes[p]
        return K

    # Return the deformation gradient tensor epsilon related to node i
    def epsilon_tensor(self, problem, i, t_n):
        tmp = np.zeros((self.dim, self.dim),dtype=np.float64)       
        index_x_family = problem.neighbors.get_index_x_family(i)
        for p in index_x_family:
            Y = self.Y_vector_state(problem, i, p, t_n)            
            X = self.X_vector_state(problem, i, p)
            tmp += self.influence_function * np.dot(Y,X.T) * self.node_volumes[p]
        epsilon = np.dot(tmp, linalg.inv(self.K_shape_tensor(problem, i))) - np.identity(self.dim, dtype=np.float64)
        return epsilon[0,0]
            
            
        