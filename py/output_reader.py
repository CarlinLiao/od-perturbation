import sys
import traceback

import pandas as pd

from py.od_perturber import od_perturber

def capacity_reader(networkFileName):
    """
    Pulls link capacity data from the TNTP data format.  In keeping with
    this format, the zones/centroids are assumed to have the lowest node
    IDs (1, 2, ..., numZones).
    """
    try:
        capacities = pd.Series()

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
                capacities[linkID] = float(data[2])
        
        return capacities
        
    except IOError:
        print("\nError reading network file %s" % networkFile)
        traceback.print_exc(file=sys.stdout) 

def output_reader(outputFilename, networkFileName=None, numZones=0):
    '''
    Process output from `tap-b` and returns resulting DataFrame and total system travel time TSTT

    numZones:   The number of zones in the network, used to filter out centroid connectors.
                Ignored if value passed is None, 0, or the same number as there are nodes.
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
        df['capacity'] = capacity_reader(networkFileName)
        
    if numZones < numNodes: # there are centroid connectors, so remove those
        df.drop(df.index[((heads <= numZones) | (tails <= numZones))], 0, inplace=True)
    
    tstt = (df['cost']*df['flow']).sum()

    if networkFileName:
        weighted_vc = (df['flow']**2 / (df['capacity'] * df['flow'].sum())).mean()
        return df, tstt, weighted_vc
    else:
        return df, tstt
