#!/usr/bin/env python
# coding: utf-8

# Import general libraries
import os
import sys
import time
import pandas as pd

# Import custom scripts
import getstatuses as get_stat
import globaljobsparallel as globaljobs

# ----------------------------------------------------------------------------------------------------------- #

# For timing information
start_time = time.time()

# If the command lines arguments have "auto" as the first term,
# we want to run in automatic mode--no asking for search terms and
# excluded terms
auto = False
try:
    if len(sys.argv) > 1:
        if(sys.argv[1] == "auto"):
            auto = True
            # Change this line to the directory in which you want to search for jobs <---------------- EDIT
            os.chdir("/beegfs/interns/esnell/Unit_Cells/")
except Exception as e:
    print(e)

# Get jobs using the parallelized implementation of global jobs
#
# This will return a list of lists of jobs
# Each sublist represents a folder with several Velodyne run folders inside it
#
statuses = list()
# Use the mode specified by the command line arguments
for job_list in globaljobs.return_all_jobs(auto):
    # Get the job statuses for each job list returned by global jobs
    statuses.append(get_stat.get_statuses(job_list))

# Format pandas DataFrame
#
# We concatenate all the job statuses from each job list together into one big dataframe
statuses = pd.concat(statuses, axis = 0)
statuses.reset_index()

# Print HTML output
#
# We then ask our getstatuses.py script to write an HTML page with our job status information
# Note that we pass in the start time so the website updates with the total script run time
get_stat.print_to_HTML(statuses, start_time)

# ----------------------------------------------------------------------------------------------------------- # 