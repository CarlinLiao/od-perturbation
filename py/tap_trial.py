import subprocess

from py.od_perturber import od_perturber
from py.output_reader import output_reader

def tap_trial(
            netFileName,
            demandFileName, 
            perturbType="normal", 
            norm_mean=1, 
            norm_sd=.1, 
            uniform_low=.9, 
            uniform_high=1.1,
            nodesPerturbedAlways=[],
            nodesPerturbedIfOrig=[],
            nodesPerturbedIfDest=[],
            returnDataFrame=False,
            returnODinfo=False
):
    '''
    Generate a new TSTT calculation for a specific network, trip demands, and perturbation combination.
    '''
    od = od_perturber(
        demandFileName, 
        perturbType, 
        norm_mean, 
        norm_sd, 
        uniform_low, 
        uniform_high,
        nodesPerturbedAlways,
        nodesPerturbedIfOrig,
        nodesPerturbedIfDest
    )
    subprocess.run("tap-b/bin/tap " + netFileName + " trips_perturbed.tntp >/dev/null", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    results = output_reader("full_log.txt", netFileName, numZones=od.numZones)
    if not returnDataFrame:
        results = results[1:]
    if returnODinfo:
        results = list(results)
        results.extend((od.totalDemand, od.odmatrix))
        results = tuple(results)
    return results