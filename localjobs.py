#!/usr/bin/env python
# coding: utf-8

# Import general libraries
import os

# Import custom scripts
from job import job

# ----------------------------------------------------------------------------------------------------------- #

# This will search through the current folder and attempt to make a Job object for any folder
# that has a Velodyne card in it
#
# This could be changed to search for a few files and only make a job if they all exist (i.e., only attempt
# instantation if there's an output file too)
#
# @return a list of job objects
def return_jobs():
    jobs = list()
    search_terms, excluded_terms = get_input()
    for folder in get_relevant_folders(search_terms, excluded_terms):
        os.chdir(folder)
        files_list = os.listdir()
        found_velodyne = False
        for file in files_list:
            if "velodyne.card" in file:
                found_velodyne = True
                break
        try:
            if found_velodyne:
                new_job = job()
                jobs.append(new_job)
        except Exception as e:
            print("ERROR: could not pull job from " + folder + ".\n\t" + repr(e))
        os.chdir("../")
    return jobs

# Simply asks the users for search terms and exclusion terms
# 
# @return a list of search terms (str) and excluded terms (str)
def get_input():
    search_terms = input("\nEnter search terms, separated by spaces: \t")
    search_terms = search_terms.split()
    excluded_terms = input("Enter excluded terms, separated by spaces: \t")
    excluded_terms = excluded_terms.split()
    return search_terms, excluded_terms

# This will look through the current directory and get all folders that 
# 1) have at least one of the key terms in the name (if there are no key terms, select all) and
# 2) have no excluded terms in the name (if there are no excluded terms, ignore this)
#
# @return a list of strings for the relevant subfolders in the current working directory
def get_relevant_folders(search_terms, excluded_terms):
    # Locate directory and relevant subfolders
    directory = os.getcwd()
    subfolders = list()
    for i in os.listdir():
        if os.path.isdir(i):
            subfolders.append(i)

    # Add all relevant folders to a list object
    potential_folders = list()
    select_all = len(search_terms) == 0
    for folder in subfolders:
        if select_all:
            potential_folders.append(folder)
        elif any([term in folder for term in search_terms]):
             potential_folders.append(folder)

    # Remove excluded folders
    relevant_folders = list()
    for folder in potential_folders:
        if not any([term in folder for term in excluded_terms]):
            relevant_folders.append(folder)
    
    return relevant_folders

# This will search through the current folder and attempt to make a Job object for any folder
# that has a Velodyne card in it
#
# This could be changed to search for a few files and only make a job if they all exist (i.e., only attempt
# instantation if there's an output file too)
#
# THE DIFFERENCE BETWEEN THIS METHOD AND THE OTHER ONE IS THIS IS INTENDED FOR USE WITH GLOBALJOBS
# AND GLOBALJOBSPARALLEL TO USE THE SAME SEARCH TERMS THROUGHOUT
#
# @return a list of job objects
def return_jobs_given_terms(search_terms, excluded_terms):
    jobs = list()
    
    # Attempt to create a job for every relevant subfolder in the current working directory
    for folder in get_relevant_folders(search_terms, excluded_terms):
        os.chdir(folder)
        files_list = os.listdir()
        found_velodyne = False
        for file in files_list:
            if "velodyne.card" in file:
                found_velodyne = True
                break
        try:
            if found_velodyne:
                new_job = job()
                jobs.append(new_job)
        except Exception as e:
            print("ERROR: could not pull job from " + folder + ".\n\t" + repr(e))
        os.chdir("../")
    
    # Print information to the console
    num_jobs = len(jobs)
    if(num_jobs > 0):
        if(num_jobs > 1):
            print("    > " + str(len(jobs)) + " jobs loaded from " + os.getcwd() + ".")
        elif(num_jobs == 1):
            print("    > " + str(len(jobs)) + " job loaded from " + os.getcwd() + ".")
    return jobs
    
# ----------------------------------------------------------------------------------------------------------- #