import subprocess

from py.od_perturber import od_perturber
from py.output_reader import output_reader
from py.gravity_model.gravity import od_matrix_from_params

def tap_trial(netFileName, true_flows, params, skip_solving=False):
    '''
    Generate a new TSTT calculation for a specific network, trip demands, and perturbation combination.
    '''
    od = od_matrix_from_params(params)
    if skip_solving:
        return od
    subprocess.run("tap-b/bin/tap " + netFileName + " trips_next.tntp >/dev/null", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_reader("full_log.txt", netFileName, true_flows=true_flows)
    # if not returnDataFrame:
    #     results = results[1:]
    # if returnODinfo:
    #     results = list(results)
    #     results.extend((od.totalDemand, od.odmatrix))
    #     results = tuple(results)
    # return results