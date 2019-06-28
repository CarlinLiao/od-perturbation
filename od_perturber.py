import os
import sys
import traceback

import numpy as np

class od_perturber():
   """
   Takes a TNTP-formatted origin-destination (OD) table (also known as a trip table) 
   and perturbs it randomly according to either the normal or uniform distribution.

   Adapted in large part from Stephen Boyles's TNTP-reading implementation.
   """

   def __init__(self, 
                demandFileName, 
                perturbType, 
                norm_mean=1, 
                norm_sd=.1, 
                uniform_low=.9, 
                uniform_high=1.1,
                nodesPerturbedAlways=[],
                nodesPerturbedIfOrig=[],
                nodesPerturbedIfDest=[]):
      """
      perturbType :                 choose between normal ("normal") or uniform ("uniform") distributed random perturbations
      norm_mean, norm_sd :          parameters to use for normally distributed perturbations
      uniform_low, uniform_high :   parameters to use for uniformly distributed perturbations

      At least one of nodesPerturbedAlways, nodesPerturbedIfOrig, nodesPerturbedIfDest must be provided to do selective perturbation.
      If all three are empty, perturbation will be applied to all nodes.
      
      nodesPerturbedAlways :        node IDs that will be perturbed if it's an origin OR a destination
      nodesPerturbedIfOrig :        node IDs that will be perturbed ONLY if it's an origin
      nodesPerturbedIfDest :        node IDs that will be perturbed ONLY if it's a destination
      """

      if perturbType == "normal":
         self.mu = norm_mean
         self.sd = norm_sd
      elif perturbType == "uniform":
         self.a = uniform_low
         self.b = uniform_high
      else:
         raise ValueError("perturbType needs to be normal or uniform")
      self.perturbType = perturbType

      self.__readDemandFile(demandFileName)
      nodelocs = None
      self.__perturb(nodesPerturbedAlways=nodesPerturbedAlways,
                     nodesPerturbedIfOrig=nodesPerturbedIfOrig,
                     nodesPerturbedIfDest=nodesPerturbedIfDest)
      self.__dump_new_trips(demandFileName)
   
   class __BadFileFormatException(Exception):
      """
      This exception is raised if a network or demand file is in the wrong format or
      expresses an invalid network.
      """
      pass  

   @staticmethod
   def __readMetadata(lines):
      """
      Read metadata tags and values from a TNTP file, returning a dictionary whose
      keys are the tags (strings between the <> characters) and corresponding values.
      The last metadata line (reading <END OF METADATA>) is stored with a value giving
      the line number this tag was found in.  You can use this to proceed with reading
      the rest of the file after the metadata.
      """
      metadata = dict()
      lineNumber = 0
      for line in lines:
         lineNumber += 1
         line.strip()
         commentPos = line.find("~")
         if commentPos >= 0: # strip comments
            line = line[:commentPos]
         if len(line) == 0:
            continue

         startTagPos = line.find("<")
         endTagPos = line.find(">")
         if startTagPos < 0 or endTagPos < 0 or startTagPos >= endTagPos:
            print("Error reading this metadata line, ignoring: '%s'" % line)
         metadataTag = line[startTagPos+1 : endTagPos]
         metadataValue = line[endTagPos+1:]
         if metadataTag == 'END OF METADATA':
            metadata['END OF METADATA'] = lineNumber
            return metadata
         metadata[metadataTag] = metadataValue.strip()
         
      print("Warning: END OF METADATA not found in file")
      return metadata

   def __readDemandFile(self, demandFileName):
      """
      Reads demand (OD matrix) data from a file in the TNTP format.
      """
      try:
         with open(demandFileName, "r") as demandFile:
            fileLines = demandFile.read().splitlines()
            self.totalDemand = 0

            # Set default parameters for metadata, then read
            self.totalDemandCheck = None

            metadata = self.__readMetadata(fileLines)      
            try:
               totalDemandCheck = float(metadata['TOTAL OD FLOW'])
               self.numZones = int(metadata['NUMBER OF ZONES'])

            except KeyError: # KeyError
               print("Warning: Not all metadata present in demand file, error checking will be limited.")
            
            # self.odmatrix = [[None for i in range(self.numZones)] for i in range(self.numZones)]
            self.odmatrix = np.empty((self.numZones, self.numZones))
            # self.odmatrix.fill(np.nan)

            for line in fileLines[metadata['END OF METADATA']:]:
               # Ignore comments and blank lines
               line = line.strip()
               commentPos = line.find("~")
               if commentPos >= 0: # strip comments
                  line = line[:commentPos]
               if len(line) == 0:
                  continue                  
                  
               data = line.split() 

               if data[0] == 'Origin':
                  origin = int(data[1])
                  continue               

               # Two possibilities, either semicolons are directly after values or there is an intervening space
               if len(data) % 3 != 0 and len(data) % 4 != 0:
                  print("Demand data line not formatted properly:\n %s" % line)
                  raise self.__BadFileFormatException
                                    
               for i in range(int(len(data) // 3)):
                  destination = int(data[i * 3])
                  check = data[i * 3 + 1]
                  demand = data[i * 3 + 2]
                  demand = float(demand[:len(demand)-1])
                  if check != ':' : 
                     print("Demand data line not formatted properly:\n %s" % line)
                     raise self.__BadFileFormatException
                  # ODID = str(origin) + '->' + str(destination)
                  # self.ODpair[ODID] = OD(origin, destination, demand)
                  # print(origin, destination)
                  # print(self.numZones)
                  self.odmatrix[origin-1][destination-1] = demand
                  self.totalDemand += demand      
                                    
      except IOError:
         print("\nError reading demand file %s" % demandFile)
         traceback.print_exc(file=sys.stdout)
      
      if totalDemandCheck != None:
         if not np.isclose(self.totalDemand, totalDemandCheck):
            print("Warning: Total demand is %f compared to metadata value %f" % ( self.totalDemand, totalDemandCheck))

   def __perturb(self, nodesPerturbedAlways, nodesPerturbedIfOrig, nodesPerturbedIfDest):

      if (len(nodesPerturbedAlways) > 0) or (len(nodesPerturbedIfOrig) > 0) or (len(nodesPerturbedIfDest) > 0):
         # origin is rows, destination is cols
         
         # combine always perturb nodes with origin or destination perturbation nodes as sets to prevent repeats
         nodesPerturbedAlways = set([i-1 for i in nodesPerturbedAlways])
         nodesPerturbedIfOrig = set([i-1 for i in nodesPerturbedIfOrig])
         nodesPerturbedIfDest = set([i-1 for i in nodesPerturbedIfDest])
         origsToPerturb = list(nodesPerturbedAlways.union(nodesPerturbedIfOrig))
         destsToPerturb = list(nodesPerturbedAlways.union(nodesPerturbedIfDest))

         # mark all OD pairs with called out origin nodes for perturbing, then do the same for destination nodes
         perturbMask = np.zeros(self.odmatrix.shape, dtype=bool)
         perturbMask[origsToPerturb, :] = True
         perturbMask[:, destsToPerturb] = True
         print(perturbMask)
      else:
         perturbMask = np.ones(self.odmatrix.shape, dtype=bool)

      if self.perturbType == "normal":
         self.odmatrix[perturbMask] *= np.random.normal(self.mu, self.sd, self.odmatrix[perturbMask].shape)
      elif self.perturbType == "uniform":
         self.odmatrix[perturbMask] *= np.random.uniform(self.a, self.b, self.odmatrix[perturbMask].shape)
      
      self.odmatrix[self.odmatrix < 0] = 0 # TODO: how to handle perturbing near-zero?
      self.odmatrix = np.around(self.odmatrix, 6)
      self.totalDemand = self.odmatrix.sum()
   
   def __dump_new_trips(self, filename):
      """
      Assuming the original filename ended with .tntp
      """

      with open("trips_perturbed.tntp", "w") as outFile:
         outFile.write(
            '<NUMBER OF ZONES> {}\n'.format(self.numZones) +
            '<TOTAL OD FLOW> {}\n'.format(self.totalDemand) +
            '<END OF METADATA>\n\n\n'
         )
         
         for i in range(self.odmatrix.shape[0]):
            outFile.write('Origin  {}\n'.format(i+1))
            line = ""
            for j in range(self.odmatrix.shape[1]):
               line += "{:>9} : {:>15}; ".format(j+1,self.odmatrix[i][j])
               if (j+1)%5==0:
                  line += '\n'
            outFile.write(line + '\n')
