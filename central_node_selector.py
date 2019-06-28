import matplotlib.pyplot as plt
import pandas as pd
import numpy as np 

def central_node_selector(nodeFilename, proportion=.25, make_plot=True):
    '''
    Select the 
    '''
    if proportion >= .5 or proportion <= 0:
        raise ValueError('Proportion must be between 0 and .5 exclusive.')

    df = pd.read_csv(nodeFilename, delim_whitespace=True, index_col=0, usecols=['Node', 'X', 'Y'])

    # define the map
    xmin = df['X'].min()
    xmax = df['X'].max()
    ymin = df['Y'].min()
    ymax = df['Y'].max()

    # define coords of bounding box to return
    excludefactor = .5-proportion/2
    xexcludelen = excludefactor*(xmax-xmin)
    xboxmin = xmin + xexcludelen
    xboxmax = xmax - xexcludelen
    yexcludelen = excludefactor*(ymax-ymin)
    yboxmin = ymin + yexcludelen
    yboxmax = ymax - yexcludelen

    # select for nodes
    nodes = set(df[(df['X'] > xboxmin) & (df['X'] < xboxmax) & (df['Y'] > yboxmin) & (df['Y'] < yboxmax)].index.to_list())

    # plot to verify
    if make_plot:
        fig = plt.figure(figsize=(10,10*(yexcludelen/xexcludelen)))
        selected_nodes = df.index.isin(nodes)
        plt.scatter(df.loc[~selected_nodes,'X'], df.loc[~selected_nodes,'Y'], c='k')
        plt.scatter(df.loc[selected_nodes,'X'], df.loc[selected_nodes, 'Y'], c='r')
        plt.axis('off')
        plt.show()
        return nodes, fig
    else:
        return nodes
