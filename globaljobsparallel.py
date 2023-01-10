#!/usr/bin/env python
# coding: utf-8

# Import general libraries
import os
import time
import pandas as pd
import datetime as datetime
from multiprocessing import Pool

# Import custom scripts
import localjobs

# ----------------------------------------------------------------------------------------------------------- #

# For every folder in the current working directory, call localjobs.py's return_jobs_given_terms
#
# If it's on auto mode, it will have no search or exclusion terms and simply grab everything
# If it's off auto mode, it will ask the user for search terms
#
# @return a list of lists of jobs
#
# This method is faster than globaljobs.py's version because it uses a pool of interns to run each job
# in order to distribute the work
#
# Each intern is responsible for a subfolder of jobs
def return_all_jobs(auto):

    # Grab timing information, just for fun
    start_time = time.time()
    print()
    print("Running parallel implementation to get all global jobs...")
    print()
    
    # We use global variables for the search and exclusion terms for the mapping of pooled scripts
    global search_terms
    global excluded_terms
    if auto:
        search_terms = ""
        excluded_terms = ""
    else:
        search_terms, excluded_terms = localjobs.get_input()

    # We're going to grab all the subfolders...
    subfolders = list()
    for i in os.listdir():
        if os.path.isdir(i):
            subfolders.append(i)
    subfolders.sort()

    # Then create a child task for each subfolder and map that to our run_subfolder method
    # which will move the task into the relevant folder and grab all the jobs...
    #
    # The child task only returns a list of jobs if the length is greater than 0
    pool = Pool(maxtasksperchild=1)
    jobs = pool.map(run_subfolder, subfolders)
    jobs = list(filter(None, jobs))
    pool.close()
    pool.join()
    
    # Print timing information, just for fun
    print()
    elapsed = time.time() - start_time
    print("Completed. Elapsed time was " + "{:.2f}".format(elapsed) + " seconds.")
    print()
    return jobs
    
# We map each subfolder to this method, which just moves into the directory and gets the jobs
#
# @return a list of jobs IFF len(list) > 0
def run_subfolder(folder):
    print("    > Getting jobs from " + str(folder))
    os.chdir(folder)
    subfolder_jobs = localjobs.return_jobs_given_terms(search_terms, excluded_terms)
    os.chdir("../")
    if(len(subfolder_jobs) > 0):
        return subfolder_jobs 
        
# ----------------------------------------------------------------------------------------------------------- #