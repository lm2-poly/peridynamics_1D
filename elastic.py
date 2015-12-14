# -*- coding: utf-8 -*-
"""
Created on Sun Dec 13 16:16:07 2015

@author: ilyass
"""
from deck import PD_deck
from problem import PD_problem
import numpy as np

class elastic_material():
    
    def __init__(self, PD_deck, PD_problem, y):
        self.len_x = len(PD_problem.x)
        self.Modulus = PD_deck.get_elastic_material_properties()
        self.compute_ext_state(PD_deck, PD_problem, y )
        self.compute_T(PD_deck, PD_problem, y)
        self.compute_Ts(PD_deck, PD_problem)
        
        
    def compute_ext_state(self, PD_deck, PD_problem, y):        
        # Initialization for e
        e = np.zeros( (int(PD_deck.Num_Nodes), int(PD_deck.Num_Nodes)) )    
    
        for x_i in range(0, len(PD_problem.x)):
            index_x_family = PD_problem.get_index_x_family(PD_problem.x, x_i)
            for x_p in index_x_family: 
                e[x_i, x_p] = np.absolute(y[x_p] - y[x_i]) - np.absolute(PD_problem.x[x_p] - PD_problem.x[x_i])
        self.e = e
        return e

    def compute_T(self, PD_deck, PD_problem, y):
        w = PD_deck.Influence_Function
        e = self.compute_ext_state(PD_deck, PD_problem, y)
        M = PD_problem.compute_m(PD_deck.Num_Nodes, y)
        tscal = np.zeros( (int(PD_deck.Num_Nodes), int(PD_deck.Num_Nodes) ) )
        for x_i in range(0, self.len_x):
            index_x_family = PD_problem.get_index_x_family( PD_problem.x, x_i)
            for x_p in index_x_family:
                tscal[x_i, x_p] = (w/PD_problem.weighted_function(PD_deck, PD_problem.x, x_i))*self.Modulus*e[x_i, x_p]
        self.tscal = tscal
        
        T = np.zeros( (int(PD_deck.Num_Nodes), int(PD_deck.Num_Nodes) ) )
        for x_i in range(0, self.len_x):
            index_x_family = PD_problem.get_index_x_family( PD_problem.x, x_i)
            for x_p in index_x_family:
                T[x_i, x_p] = tscal[x_i, x_p] * M[x_i, x_p]
        self.T = T
        
    def compute_Ts(self, PD_deck, PD_problem):
        Ts = np.zeros( (int(PD_deck.Num_Nodes) ) )
        for x_i in range(0, self.len_x):
            index_x_family = PD_problem.get_index_x_family( PD_problem.x, x_i)
            for x_p in index_x_family:
                Ts[x_i] = Ts[x_i] + self.T[x_i, x_p] - self.T[x_p, x_i]
            Ts[x_i] = Ts[x_i] * PD_deck.Volume
        self.Ts = Ts