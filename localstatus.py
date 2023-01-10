#!/usr/bin/env python
# coding: utf-8

# Import general libraries
import pandas as pd

# Import custom scripts
import localjobs
import getstatuses as get_stat

# ----------------------------------------------------------------------------------------------------------- #

# Get jobs
joblist = localjobs.return_jobs()

# Format pandas DataFrame
statuses = get_stat.get_statuses(joblist)
statuses = statuses.sort_values(by=['Remaining'])
statuses.reset_index()

# Print HTML output
get_stat.print_to_HTML(statuses)

# ----------------------------------------------------------------------------------------------------------- #