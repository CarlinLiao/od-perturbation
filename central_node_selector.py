import matplotlib.pyplot as plt
import pandas as pd
import numpy as np 

def central_node_selector(nodeFilename, proportion=.25, make_plot=True, show_plot=True):
    '''
    Select some provided proportion of nodes closest to the center and return 
    both a set of node IDs and, optionally, a plot of the selected nodes.
    '''

    df = pd.read_csv(nodeFilename, delim_whitespace=True, index_col=0, usecols=['Node', 'X', 'Y'])

    # define the map
    xmin = df['X'].min()
    xmax = df['X'].max()
    ymin = df['Y'].min()
    ymax = df['Y'].max()

    # find distance of each node to center and select for given proportion of closest nodes
    xdel = xmax-xmin
    ydel = ymax-ymin
    xc = xmin + xdel/2
    yc = ymin + ydel/2
    df['distsq'] = (df['X']-xc)**2 + (df['Y']-yc)**2
    df.sort_values('distsq', inplace=True)
    nodes = set(df.index[0:int(df.shape[0]*proportion)].to_list())

    # plot to verify
    if make_plot:
        fig = plt.figure(figsize=(10,10*(ydel/xdel)))
        selected_nodes = df.index.isin(nodes)
        plt.scatter(df.loc[~selected_nodes,'X'], df.loc[~selected_nodes,'Y'], c='k')
        plt.scatter(df.loc[selected_nodes,'X'], df.loc[selected_nodes, 'Y'], c='r')
        plt.axis('off')
        if show_plot:
            plt.show()
        return nodes, fig
    else:
        return nodes
