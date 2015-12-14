# -*- coding: utf-8 -*-
"""
Created on Sun Dec 13 12:50:28 2015

@author: ilyass
"""

import logging
from scipy.optimize import fsolve
import timeit
from deck import PD_deck
import numpy as np
import scipy.optimize
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

class PD_problem():
    
    def __init__(self, PD_deck):
        #Import initial data
        self.get_pd_nodes(PD_deck)
        self.compute_b(PD_deck)
        self.compute_horizon(PD_deck)
        
        self.y = np.zeros( ( int(PD_deck.Num_Nodes), int(PD_deck.Num_TimeStep)) )
        self.forces= Ts = np.zeros( ( int(PD_deck.Num_Nodes), int(PD_deck.Num_TimeStep)) )

    def compute_b(self, PD_deck):       
        #Build  matrix b[row = node, column = time]
        b = np.zeros( ( int(PD_deck.Num_Nodes), int(PD_deck.Num_TimeStep)) )   
        PD_deck.get_parameters_loading_ramp()
        if PD_deck.Loading_Flag == "RAMP":
            PD_deck.get_parameters_loading_ramp()
            for x_i in range(0, PD_deck.Horizon_Factor):
                for t_n in range(1, int(PD_deck.Num_TimeStep)):
                    b[x_i, t_n] = - self.ramp_loading( PD_deck, t_n )
            for x_i in range(len(self.x) - PD_deck.Horizon_Factor, len(self.x) ):
                for t_n in range(1, int(PD_deck.Num_TimeStep)):
                    b[x_i, t_n] = self.ramp_loading( PD_deck, t_n )
        else:
            logger.error("There is a problem with the Boundary Conditions in your XML deck.")
        self.b = b
        
    def get_pd_nodes(self, PD_deck):
        # Define x
        x = np.zeros( PD_deck.Num_Nodes )    
        for i in range(0, PD_deck.Num_Nodes):
            x[i] = -PD_deck.Length_Tot/2 + i * PD_deck.Delta_x
        self.x = x
        
    def ramp_loading(self, PD_deck, t_n):     
        Time_t = PD_deck.Delta_t*t_n
        for x_i in range(0, int(PD_deck.Num_Nodes)):
            if Time_t <= PD_deck.Ramp_Time:
                result = (PD_deck.Force_Density*Time_t)/PD_deck.Ramp_Time   
                return result
            else:
                result = PD_deck.Force_Density
                return result
            
    def compute_horizon(self, PD_deck):
        #Be sure that points are IN the horizon
        safety_small_fraction = 1.01
        self.Horizon = PD_deck.Horizon_Factor*PD_deck.Delta_x*safety_small_fraction
        
    def get_index_x_family(self, x, x_i):
        x_family = []
        for x_p in range(0, len(x)):
            if x_p == x_i:
                #print "SAME", x_p, x_i
                pass
            elif np.absolute(x[x_p]-x[x_i]) <= self.Horizon:
                x_family.append( x_p )
            else:
                pass
        return x_family
        
    def compute_m(self, Num_Nodes, y_n):         
        M = np.zeros( (int(Num_Nodes), int(Num_Nodes)) )
        for x_i in range(0, len(self.x)):
            index_x_family = self.get_index_x_family(self.x, x_i)
            for x_p in index_x_family:
                M[x_i, x_p] = (y_n[x_p] - y_n[x_i]) / np.absolute(y_n[x_p] - y_n[x_i])
        return M
        
    def weighted_function(self, PD_deck, x, x_i):
        Horizon = self.compute_horizon(PD_deck)
        index_x_family = self.get_index_x_family( x, x_i )
        Delta_V = PD_deck.Volume
        Influence_Function = PD_deck.Influence_Function
        result = 0
        for x_p in index_x_family:
            #print x[x_i], x[x_p], Volume, Influence_Function
            result = result + Influence_Function*(x[x_p]-x[x_i])**2 * Delta_V
        return result
        
    def compute_residual(self, y, PD_deck, forces, t_n):
        residual = np.zeros( ( int(PD_deck.Num_Nodes) ) )
        from elastic import elastic_material
        y[len(y)/2] = 0
        forces = elastic_material( PD_deck, self, y )
        self.update_force_data(forces, t_n)
        for x_i in range(0, len(self.x)):
            residual[x_i] = forces.Ts[x_i] + self.b[x_i, t_n]
        return residual
        
    def update_force_data(self, forces, t_n):    
        self.forces[:, t_n] = forces.Ts
        
    def quasi_static_solver(self, y, PD_deck, forces):
        for t_n in range(1, PD_deck.Num_TimeStep):
            solver = scipy.optimize.root(self.compute_residual, y, args=(PD_deck, forces, t_n), method='krylov',jac=None,tol=1.0e-12,callback=None,options={'maxiter':1000})
            self.y[:, t_n] = solver.x
            y = solver.x
            if solver.success == "False":
                logger.warning("Convergence could not be reached.")
            else:
                logger.info( t_n, solver.success )
        return solver
        
    def write_data_to_csv(self, PD_deck, PD_problem):
        f = open('data_csv', 'wr+')
        for t_n in range(1, PD_deck.Num_TimeStep):
            f.write("Node")
            for node in self.x:
                f.write(","+str(node))
            f.write("\n")
            f.write("Time")
            for node in self.x:
                f.write(","+str(t_n*PD_deck.Delta_t))
            f.write("\n")
            f.write("Initial_position")
            for position in PD_problem.y[:,1]:
                f.write(","+str(position))
            f.write("\n")
            f.write("Position")
            for position in self.y[:,t_n]:
                f.write(","+str(position))
            f.write("\n")
            f.write("Force")
            for force in self.forces[:, t_n]:
                f.write(","+str(force))
            f.write("\n")
            f.write("\n")
            
    def plot_force(self, PD_deck):
        for t_n in range(1, PD_deck.Num_TimeStep):
            force_plot = plt
            force_plot.plot(self.y[:,1], self.forces[:, t_n], '-+')
        force_plot.legend(title = "forces")
        return force_plot
        
    def plot_positions(self, PD_deck):
        for t_n in range(1, PD_deck.Num_TimeStep):
            position_plot = plt
            position_plot.plot(self.y[:,1], self.y[:, t_n], '-+')
        position_plot.legend(title = "position")
        return position_plot
    