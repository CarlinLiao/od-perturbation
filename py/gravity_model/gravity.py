import numpy as np
import networkx as nx
from scipy.special import binom

import os
   
def write_od_matrix(od_matrix):

    with open("trips_next.tntp", "w") as outFile:
        outFile.write(
        '<NUMBER OF ZONES> {}\n'.format(576) +
        '<TOTAL OD FLOW> {}\n'.format(od_matrix.sum().sum()) +
        '<END OF METADATA>\n\n\n'
        )
        
        for i in range(od_matrix.shape[0]):
            outFile.write('Origin  {}\n'.format(i+1))
            line = ""
            for j in range(od_matrix.shape[1]):
                line += "{:>9} : {:>15}; ".format(j+1,od_matrix[i][j])
                if (j+1)%5==0:
                    line += '\n'
            outFile.write(line + '\n')

def gen_od_matrix(adj_factors, S, E, L_inv, param_matrix=1):
    '''
    Helper function for od matrix construction
    '''
    od_matrix = adj_factors*(np.outer(S,E))*L_inv*param_matrix
    od_matrix = (od_matrix.T/(adj_factors*E*L_inv*param_matrix).sum(axis=1)).T
    adj_factors *= E/od_matrix.sum(axis=0)
    return od_matrix, adj_factors

def od_matrix_from_params(od_params):
    '''
    od_params is the same size as the number of unique OD pairs
    (so, half the OD matrix minus the diagonal (# of origins/destinations choose 2))
    '''
    
    dirname = os.path.dirname(__file__)

    # load in fixed parameters and initialize OD matrix
    S = np.load(os.path.join(dirname, 'fp_start.npy'))
    E = np.load(os.path.join(dirname, 'fp_endin.npy'))
    L_inv = np.load(os.path.join(dirname, 'fp_shrtp.npy'))
    param_matrix = np.zeros((len(S), len(S)))
    adj_factors = np.ones(len(S))
    
    # check if od_params are of correct size
    param_count = int(binom(len(S), 2))
    if len(od_params) != param_count:
        raise ValueError(f'od_params must be of size {param_count}')
    if np.any(od_params<=0):
        raise ValueError('all od_params entries must be positive')
    
    # fill the param matrix
    i = 0
    for j in range(1,param_matrix.shape[0]+1):
        param_matrix[j-1,j:] = od_params[i:i+param_matrix.shape[0]-j]
        i += param_matrix.shape[0]-j
    param_matrix += param_matrix.T # turn into a symmetrical matrix
        
    od_matrix, adj_factors = gen_od_matrix(adj_factors, S, E, L_inv, param_matrix)
    
    breaker = 1
    while not np.allclose(od_matrix.sum(axis=0), E, rtol=0):
        od_matrix, adj_factors = gen_od_matrix(adj_factors, S, E, L_inv, param_matrix)
        
        breaker += 1
        if breaker>1000:
            break
    
    write_od_matrix(od_matrix)
    return od_matrix
   