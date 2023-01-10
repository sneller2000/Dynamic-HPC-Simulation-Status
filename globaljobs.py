#!/usr/bin/env python
# coding: utf-8

# Import general libraries
import os
import pandas as pd

# Import custom scripts
import localjobs

# ----------------------------------------------------------------------------------------------------------- #

# For every folder in the current working directory, call localjobs.py's return_jobs_given_terms
#
# If it's on auto mode, it will have no search or exclusion terms and simply grab everything
# If it's off auto mode, it will ask the user for search terms
#
# @return a list of lists of jobs
def return_all_jobs(auto):
    if auto:
        search_terms = ""
        excluded_terms = ""
    else:
        search_terms, excluded_terms = localjobs.get_input()
        print()

    subfolders = list()
    for i in os.listdir():
        if os.path.isdir(i):
            subfolders.append(i)

    jobs = list()
    for folder in subfolders:
        os.chdir(folder)
        subfolder_jobs = localjobs.return_jobs_given_terms(search_terms, excluded_terms)
        if(len(subfolder_jobs) > 0):
            jobs.append(subfolder_jobs)
        os.chdir("../")
     
    return jobs
    
# ----------------------------------------------------------------------------------------------------------- #
