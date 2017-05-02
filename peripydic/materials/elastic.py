# -*- coding: utf-8 -*-
#@author: ilyass.tabiai@polymtl.ca
#@author: rolland.delorme@polymtl.ca
#@author: patrick.diehl@polymtl.ca
import numpy as np
from scipy import linalg
from multiprocessing import Process, Lock
import sharedmem
from ..util import linalgebra
import sys

## Class to compute the global internal volumic force at each node of an elastic material using its material properties
class Elastic_material():

    ## Constructor
    # @param deck The input deck
    # @param data_solver Data from the peridynamic problem/solving class
    # @param y Actual nodes' position
    def __init__(self, deck, data_solver, y):

        ## Influence function
        self.w = deck.influence_function

        ## Weighted volume
        self.Weighted_Volume = data_solver.weighted_volume

        if deck.dim == 1:
            ## Young modulus of the material
            self.Young_Modulus = deck.young_modulus

        if deck.dim == 2:
            ## Bulk modulus of the material
            self.K = deck.bulk_modulus
            ## Shear modulus of the material
            self.Mu = deck.shear_modulus
            ## Poisson ratio of the material
            self.Nu = (3. * self.K - 2. * self.Mu) / (2. * (3. * self.K + self.Mu))
            ## Factor applied for 2D plane stress to compute dilatation and force state
            self.factor2d = (2. * self.Nu - 1.) / (self.Nu - 1.)
#            ## Plane strain
#            self.factor2d = 1

        if deck.dim == 3:
            ## Bulk modulus of the material
            self.K = deck.bulk_modulus
            ## Shear modulus of the material
            self.Mu = deck.shear_modulus

        ## Compute the dilatation for each node
        self.compute_dilatation(deck, data_solver, y)

        ## Compute the global internal force density at each node
        self.compute_f_int(deck, data_solver, y)

    ## Compute the dilatation for each node
    # @param deck The input deck
    # @param data_solver Data from the peridynamic problem/solving class
    # @param y The actual nodes' position
    # @param start Starting Id of the loop
    # @param end Ending Id of the loop
    def compute_dilatation_slice(self, deck, data_solver, y, start, end):

        for i in range(start, end):
            index_x_family = data_solver.neighbors.get_index_x_family(i)
            for p in index_x_family:
                    Y = (y[p,:]) - y[i,:]
                    X = deck.geometry.nodes[p,:] - deck.geometry.nodes[i,:]
                    self.e[i,p] = linalgebra.norm(Y) - linalgebra.norm(X)

                    if deck.dim == 1:
                        self.dilatation[i] += (1. / self.Weighted_Volume[i]) * self.w * linalgebra.norm(X) * self.e[i,p] * deck.geometry.volumes[p]

                    if deck.dim == 2:
                        self.dilatation[i] += (2. / self.Weighted_Volume[i]) * self.factor2d * self.w * linalgebra.norm(X) * self.e[i,p] * deck.geometry.volumes[p]

                    if deck.dim == 3:
                        self.dilatation[i] += (3. / self.Weighted_Volume[i]) * self.w * linalgebra.norm(X) * self.e[i,p] * deck.geometry.volumes[p]

    ## Compute the dilatation and and also the scalar extension state for each node
    # @param deck The input deck
    # @param data_solver Data from the peridynamic problem/solving class
    # @param y The actual nodes' position
    def compute_dilatation(self, deck, data_solver, y):
        ## Dilatation at each node
        self.dilatation = sharedmem.empty((deck.num_nodes),dtype=np.float64)
        ## Extension between Node "i" and Node "p" within its family
        self.e = sharedmem.empty((deck.num_nodes, deck.num_nodes),dtype=np.float64)

        threads = deck.num_threads
        part = int(deck.num_nodes/threads)

        processes = []

        for i in range(0,threads):
            start = i * part
            if i < threads - 1:
                end = (i+1) * part
            else:
                end = deck.num_nodes
            processes.append(Process(target=self.compute_dilatation_slice, args=(deck, data_solver, y, start, end)))
            processes[i].start()

        for p in processes:
            p.join()

    ## Compute the global internal force density at each node
    # @param deck The input deck
    # @param data_solver Data from the peridynamic problem/solving class
    # @param y The actual nodes' position
    # @param start Starting Id of the loop
    # @param end Ending Id of the loop
    def compute_f_int_slice(self, deck, data_solver, y, start, end, data):
        for i in range(start, end):
            index_x_family = data_solver.neighbors.get_index_x_family(i)
            for p in index_x_family:
                Y = y[p,:] - y[i,:]
                X = deck.geometry.nodes[p,:] - deck.geometry.nodes[i,:]

                # Compute the direction vector between Node_p and Node_i
                M = Y / linalgebra.norm(Y)

                if deck.dim == 1:
                    # PD material parameter
                    alpha = self.Young_Modulus / self.Weighted_Volume[i]
                    ## Scalar force state
                    self.t = alpha * self.w * self.e[i,p]

                if deck.dim == 2:
                    # PD material parameter
                    # Plane stress
                    alpha_s = (9. / self.Weighted_Volume[i]) * (self.K + ((self.Nu + 1.)/(2. * self.Nu - 1.))**2 * self.Mu / 9.)
                    # Plane strain
                    #alpha_s = (9. / self.Weighted_Volume[i]) * (self.K + self.Mu / 9.)

                    alpha_d = (8. / self.Weighted_Volume[i]) * self.Mu
                    # Scalar force state
                    e_s = self.dilatation[i] * linalgebra.norm(X) / 3.
                    e_d = self.e[i, p] - e_s

                    t_s = (2. * self.factor2d * alpha_s - (3. - 2. * self.factor2d) * alpha_d) * self.w * e_s / 3.
                    t_d = alpha_d * self.w * e_d
                    self.t = t_s + t_d

                if deck.dim == 3:
                    # PD material parameter
                    alpha_s = (9. / self.Weighted_Volume[i]) * self.K
                    alpha_d = (15. / self.Weighted_Volume[i]) * self.Mu
                    # Scalar force state
                    e_s = self.dilatation[i] * linalgebra.norm(X) / 3.
                    e_d = self.e[i, p] - e_s
                    t_s = alpha_s * self.w * e_s
                    t_d = alpha_d * self.w * e_d
                    self.t = t_s + t_d

                #lock.acquire()
                data[i,:] += self.t * M * deck.geometry.volumes[p]
                data[p,:] += -self.t * M * deck.geometry.volumes[i]
                #lock.release()

    ## Compute the global internal force density at each node
    # @param deck The input deck
    # @param data_solver Data from the peridynamic problem/solving class
    # @param y The actual nodes' position
    def compute_f_int(self, deck, data_solver, y):
        ## Internal force density at each node
        self.f_int = sharedmem.empty((deck.num_nodes, deck.dim),dtype=np.float64)
        #self.f_int.fill(0.0)
        #lock = Lock()
        threads = deck.num_threads
        part = int(deck.num_nodes/threads)

        processes = []
        data = []
        for i in range(0,threads):
            start = i * part
            if i < threads - 1:
                end = (i+1) * part
            else:
                end = deck.num_nodes
            data.append(sharedmem.empty((deck.num_nodes, deck.dim),dtype=np.float64))
            #data[i].fill(0)
            processes.append(Process(target=self.compute_f_int_slice, args=(deck, data_solver, y, start, end, data[i])))
            processes[i].start()

        for p in processes:
            p.join()

        for i in range(0,threads):
            self.f_int += data[i]