import sys
import traceback

import pandas as pd

from py.od_perturber import od_perturber

def net_reader(networkFileName):
    """
    Pulls link capacity data from the TNTP data format.  In keeping with
    this format, the zones/centroids are assumed to have the lowest node
    IDs (1, 2, ..., numZones).
    """
    try:
        df = pd.DataFrame(columns=['capacity', 'length'])

        with open(networkFileName, "r") as networkFile:
            fileLines = networkFile.read().splitlines()
            
            metadata = od_perturber._od_perturber__readMetadata(fileLines)      
                            
            for line in fileLines[od_perturber._od_perturber__readMetadata(fileLines)['END OF METADATA']:]:
                # Ignore comments and blank lines
                line = line.strip()
                commentPos = line.find("~")
                if commentPos >= 0: # strip comments
                    line = line[:commentPos]
                
                if len(line) == 0:
                    continue                  
                    
                data = line.split() 
                if len(data) < 11 or data[10] != ';' :
                    print("Link data line not formatted properly:\n '%s'" % line)
                    raise od_perturber._od_perturber__BadFileFormatException
                    
                # Create link                                
                linkID = '(' + str(data[0]).strip() + "," + str(data[1]).strip() + ')'
                df.loc[linkID] = [float(data[2]), float(data[3])]
        
        return df
        
    except IOError:
        print("\nError reading network file %s" % networkFile)
        traceback.print_exc(file=sys.stdout) 

def output_reader(outputFilename, networkFileName=None, numZones=0, true_flows=None, focus_link=None):
    '''
    Process output from `tap-b` and returns resulting DataFrame and total system travel time TSTT

    numZones:   The number of zones in the network, used to filter out centroid connectors.
                Ignored if value passed is None, 0, or the same number as there are nodes.
    true_flows: pandas Series of flows with link IDs matching those of the input network.
    focus_link: Link ID to return V/C value for. (Base case's most congested link suggested.)
    '''
    df = pd.read_csv(outputFilename, sep=' ', index_col=1, skiprows=2, header=None, names=[
        'ID',
        'link',
        'flow',
        'cost',
        'der'
    ]).drop('ID', 1)
    pairs = df.index.str[1:-1].str.split(',').str
    heads = pd.to_numeric(pairs[0])
    tails = pd.to_numeric(pairs[1])
    numNodes = pd.DataFrame([heads, tails]).values.max()

    if networkFileName:
        df[['capacity', 'length']] = net_reader(networkFileName)
        
    if numZones < numNodes: # there are centroid connectors, so remove those
        df.drop(df.index[((heads <= numZones) | (tails <= numZones))], 0, inplace=True)
    
    tstt = (df['cost']*df['flow']).sum()
    toReturn = [df, tstt]

    if networkFileName:
        weighted_vc = (df['flow']**2 / (df['capacity'] * df['flow'].sum())).mean()
        vmt = (df['flow']*df['length']).sum()
        toReturn += [weighted_vc, vmt]
    
    if true_flows is not None:
        link_flows_within_1pc = ((df['flow']/true_flows - 1).abs() <= 0.01).sum()/df.shape[0]
        toReturn.append(link_flows_within_1pc)
    
    if focus_link:
        focus_link_vc = df.loc[focus_link, 'flow']/df.loc[focus_link, 'capacity']
        toReturn.append(focus_link_vc)

    return tuple(toReturn)
