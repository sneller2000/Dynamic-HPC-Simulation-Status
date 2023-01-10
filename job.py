#!/usr/bin/env python
# coding: utf-8

# Import general libraries
import os
import re
import h5py as h5
import numpy as np
import pandas as pd
from functools import total_ordering
from datetime import datetime, timedelta, time

# ----------------------------------------------------------------------------------------------------------- #

@total_ordering
class job:

    # Enable comparisons between jobs
    #
    # If you want it to compare based on something other than folder name,
    # it's an easy switch
    def _is_valid_operand(self, other):
        return (hasattr(other, "folder_name"))
    def __lt__(self, other):
        if not self._is_valid_operand(other):
            return NotImplemented
        return ((self.folder_name < other.folder_name))

    # Initialize all relevant instance variables
    def __init__(self):
    
        # Pull the:
        # 1) folder name, from os.getcwd()
        # 2) directory name, from os.getcwd()
        # 3) description, from the velodyne card --- UNUSED ---
        # 4) output file, from whatever most recent .o###### file there is
        # 5) run duration, from the velodyne card
        self.folder_name = self.set_folder_name()
        self.directory_name = self.set_directory_name()
        self.description = self.get_description()
        self.output_file = self.set_output_file()
        self.duration = self.get_duration()

        # Set up timing information:
        #
        # We initialize everything to None / False and then use get_timing_data()
        # to set all our values correctly
        self.completed = False
        self.canceled = False
        self.cancellation_time = None
        self.start_real_time = None
        self.elapsed = None
        self.time_finished = None
        self.current_deformation = None
        self.HPC_code = None
        self.timing_data = self.get_timing_data()
                   
    # METHOD BORROWED FROM https://thispointer.com/python-get-last-n-lines-of-a-text-file-like-tail-command/
    # Very important to use this to keep memory accesses minimal
    def get_last_n_lines(self, file_name, N):
        # Create an empty list to keep the track of last N lines
        list_of_lines = []
        # Open file for reading in binary mode
        with open(file_name, 'rb') as read_obj:
            # Move the cursor to the end of the file
            read_obj.seek(0, os.SEEK_END)
            # Create a buffer to keep the last read line
            buffer = bytearray()
            # Get the current position of pointer i.e eof
            pointer_location = read_obj.tell()
            # Loop till pointer reaches the top of the file
            while pointer_location >= 0:
                # Move the file pointer to the location pointed by pointer_location
                read_obj.seek(pointer_location)
                # Shift pointer location by -1
                pointer_location = pointer_location -1
                # read that byte / character
                new_byte = read_obj.read(1)
                # If the read byte is new line character then it means one line is read
                if new_byte == b'\n':
                    # Save the line in list of lines
                    list_of_lines.append(buffer.decode()[::-1])
                    # If the size of list reaches N, then return the reversed list
                    if len(list_of_lines) == N:
                        return list(reversed(list_of_lines))
                    # Reinitialize the byte array to save next line
                    buffer = bytearray()
                else:
                    # If last read character is not eol then add it in buffer
                    buffer.extend(new_byte)
            # As file is read completely, if there is still data in buffer, then its first line.
            if len(buffer) > 0:
                list_of_lines.append(buffer.decode()[::-1])
        # return the reversed list
        return list(reversed(list_of_lines))
                  
    # METHOD BORROWED FROM https://stackoverflow.com/questions/18422127/python-read-text-file-from-second-line-to-fifteenth
    # Very important to use this to keep memory accesses minimal
    def get_first_n_lines(self, file_name, N):   
        from itertools import islice
        list_of_lines = []
        with open(file_name) as fin:
            for line in islice(fin, 0, N + 1):
                list_of_lines.append(line)
        return list_of_lines
    
    def set_folder_name(self):
        return os.getcwd().split("/")[-1:][0]
    
    def set_directory_name(self):
        return os.getcwd()
    
    # To get the description, we look only at the first 25 lines of the velodyne card
    # If it's not working, increase this to > 25 lines
    # 
    # OR
    #
    # Check that you start your description with:   "Problem Title"
    # and end your description with:                "Title" or "Subtitle"
    #
    # @return the description written in the velodyne.card file, or the reason why it couldn't find your description
    #
    # If it's parsing weirdly, change the line with all the .replaces--I left them all separately for visual clarity
    def get_description(self):
        description = None
        try:
            file_name = self.directory_name + "/velodyne.card"
            lines = self.get_first_n_lines(file_name, 25)
            extracted = False
            extracting = False
            for line in lines:
                if extracting:
                    if "title" in line.lower():
                        extracting = False
                        extracted = True
                        break
                    description = description + line + "\n"
                if "problem title" in line.lower():
                    extracting = True
                    description = ""
            # Parse out unwanted characters
            description = description.replace("!", "").replace("*", "").replace("\t", "").replace("\n", "").replace("-", "")
            # Remove spaces at the beginning, in a terrible solution (sorry!)
            while description[0] == " ":
                description = description[1:]
            if description == None or extracted == False:
                raise AssertionError()
        except Exception as e:
            print("description not found", e)
            description = "Description not found in first 25 lines of velodyne.card. Method looks for line including \"Problem Title\" and " + \
                "ends with line including \"Title\"."
        return description
    
    # To get the duration, we look only at the first 250 lines of the velodyne card
    # If it's not working, increase this to > 250 lines
    # 
    # OR
    #
    # Check that you start your description with:   "Problem Title"
    # and end your description with:                "Title" or "Subtitle"
    #
    # @return the description written in the velodyne.card file, or the reason why it couldn't find your description
    #
    # If it's parsing weirdly, change the line with all the .replaces--I left them all separately for visual clarity
    def get_duration(self):
        duration = None
        try:
            file_name = self.directory_name + "/velodyne.card"
            lines = self.get_first_n_lines(file_name, 250)
            extracted = False
            for line in lines:
                if "termination time" in line.lower():
                    duration = re.search(r'\d+.\d*', line).group(0)
                    duration = round(float(re.search(r'\d+.\d*', line).group(0)), 5)
                    extracted = True
                    break
            if duration == None or extracted == False:
                raise AssertionError()
            if duration == 0:
                print("Extracted duration was 0 seconds.")
                raise AssertionError
        except Exception as e:
            print("Duration not found in first 250 lines of velodyne.card. Method looks for line including \"Termination time\".\n\t" + repr(e))
        return duration
    
    # This will look for all our .o###### files and then choose
    # the file with the maximum extension (i.e., the most recent one)
    #
    # @return the file location of our most recent .o file
    def set_output_file(self):
        try:
            files = os.listdir()
            output_files = list()
            extensions = list()
            for file in files:
                if re.search(".o\d+",file):
                    output_files.append(file)
                    extensions.append(int(file[-6:])) ## for a presumed 6 digit job code
            return [file for file in output_files if str(max(extensions)) in file][0]
        except Exception as e:
            print("ERROR output file not found: \n\t> " + str(e))
    
    # This will pull our HPC code, which is just the digits at the end of our output file
    def get_HPC_code(self):
        try:
            files = os.listdir()
            output_files = list()
            extensions = list()
            for file in files:
                if re.search(".o\d+",file):
                    output_files.append(file)
                    extensions.append(int(file[-6:])) ## for a presumed 6 digit job code
            return max(extensions)
        except Exception as e:
            print("ERROR output file not found: \n\t> " + str(e))
    
    # Here we pull in our timing information from our most recent status.timestep file
    #
    # @return current_rt:   current real time, as a DateTime object
    #         start_time:   start real time, as a DateTime object
    #         timestep:     the current timestep, as a float
    #
    def get_current_start_timestep_times(self):
        file_path = self.directory_name + "/" + self.get_recent_timestep()
        #print("Searching " + file_path + " for runtime information...")
        first_lines = self.get_first_n_lines(file_path, 2) ## returns lines 0 and 1, which are the labels and first row respectively
        last_line = self.get_last_n_lines(file_path, 2)[0]
        
        start_real_time = " ".join(first_lines[1].split()[0:2]).replace(",","")
        current_real_time = " ".join(last_line.split()[0:2]).replace(",","")
        timestep = float(last_line.split()[3].replace(",","")) 
                
        start_rt = datetime.strptime(start_real_time, '%Y/%m/%d %H:%M:%S')
        current_rt = datetime.strptime(current_real_time, '%Y/%m/%d %H:%M:%S')
        return (current_rt, start_rt, timestep)
    
    # Find the most recent timestep file
    def get_recent_timestep(self):
        files = os.listdir()
        timestep_files = [f for f in files if "status.timestep" in f]
        return max(timestep_files)
    
    # Look for a completion code in the output file
    # Here we look for the key words "Total Computation Time:" in the last 15 lines of the output file
    #
    # @return a boolean (finished vs. unfinished)
    def is_completed(self):
        if self.completed == False:
            try:
                file_name = self.directory_name + "/" + self.output_file
                lines = self.get_last_n_lines(file_name, 15)
                found_completion_code = False
                for line in lines:
                    if "Total Computation Time:" in line:
                        try:
                            total_comp_time = str(re.search('[+-]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)', line).group(0))
                            if total_comp_time is not None:
                                found_completion_code = True
                                break
                        except Exception as e:
                            print("ERROR: " + str(e))
                if found_completion_code:
                    self.completed = True
                return found_completion_code
            except Exception as e:
                print(e)
        else:
            return True
    
    # Look for a cancellation code in the output file
    # Here we look for the key words "slurmstepd: error: \*\*\* (.*)ON compute(.*) CANCELLED AT (.*)" 
    # in the last 15 lines of the output file
    #
    # @return a boolean (canceled vs. uncanceled)
    def is_canceled(self):
        if self.canceled == False:
            try:
                file_name = self.directory_name + "/" + self.output_file
                last_lines = self.get_last_n_lines(file_name, 15)
                for line in last_lines:
                    match = re.search(r'slurmstepd: error: \*\*\* (.*)ON compute(.*) CANCELLED AT (.*) \*\*\*', line)
                    found_cancellation_code = bool(match)
                    if found_cancellation_code:
                        cancellation_time = match.group(3).replace("T", " ")
                        self.cancellation_time = cancellation_time
                        self.cancelled = True
                        break
                return found_cancellation_code
            except Exception as e:
                print(e)
        else:
            return True
    
    # Return a pandas DataFrame with relevant job tracking information
    #
    # columns=['HPC Code', 'Job Name','Percent','Start Time','Elapsed','Remaining','End Time','Description']
    #
    # @return a pandas DataFrame
    #
    def get_timing_data(self):
        df = pd.DataFrame(columns=['HPC Code', 'Job Name','Percent','Start Time','Elapsed','Remaining','End Time','Description'])
        # As far as I'm aware, this case will never happen if we initialize the job from scratch each time
        if self.completed and not self.canceled:
            df.loc[0] = [self.HPC_code, self.folder_name, 100.00, self.start_real_time, self.elapsed, "COMPLETE", self.time_finished, self.description]
        else:
            # Pull in data from get_current_start_timestep_times()
            times = self.get_current_start_timestep_times()
            current_real_time = times[0]
            start_real_time = times[1]
            timestep = times[2]
            
            # Initialize self.start_real_time
            self.start_real_time = start_real_time
            
            # Extrapolate when we think the job will be complete
            elapsed_time = current_real_time - start_real_time
            percent = timestep / self.duration * 100
            time_remaining = (elapsed_time / (percent / 100)) - elapsed_time
            end_time = time_remaining + current_real_time
            
            # Initialize our HPC code
            self.HPC_code = self.get_HPC_code()
            
            # Update whether we think the run is completed, canceled, or still going
            is_completed = self.is_completed()
            is_canceled = self.is_canceled()
            
            # Return values based on the job status
            if is_completed and not is_canceled:
                self.elapsed = elapsed_time
                self.time_finished = current_real_time
                df.loc[0] = [self.HPC_code, self.folder_name, 100.00, self.start_real_time, self.elapsed, "COMPLETE", self.time_finished, self.description]
            elif is_canceled:
                self.elapsed = elapsed_time
                self.time_finished = current_real_time
                df.loc[0] = [self.HPC_code, self.folder_name, percent, self.start_real_time, self.elapsed, "CANCELED", self.cancellation_time, self.description]
            else:
                self.elapsed = elapsed_time
                self.time_finished = end_time
                df.loc[0] = [self.HPC_code, self.folder_name, percent, self.start_real_time, elapsed_time, time_remaining, end_time, self.description]
        return(df)
    
    # Return a pandas representation of our timehist file
    #
    # Edit it to have it point to your relevant data
    def get_timehist(self):
        try:
            timehist_loc = self.directory_name + "/timehist.h5"
            timehist = h5.File(timehist_loc,'r')
            
            try:
                arr = np.array(timehist.get('/LoadCell/Lattice_Center/Data'))
                df = pd.DataFrame(arr)
                print("    > Successfully extracted LoadCell data.")
            except Exception as e:
                print("ERROR: unable to pull data from " + self.folder_name + "/timehist.h5/LoadCell/Lattice_Center/Data. \n\t" + str(e))
              
            df['Job Name'] = self.folder_name
            return df
        except Exception as e:
            print("ERROR: could not retrieve data from timehist.h5. \n\t" + str(e))
    
    # Return a pandas representation of our simon file
    #
    # Edit it to have it point to your relevant data
    def get_simon(self):
        try:
            simon_loc = self.directory_name + "/simon.h5"
            simon = h5.File(simon_loc,'r')
            
            try:
                arr = np.array(simon.get('/physical_quantities/Data'))
                df = pd.DataFrame(arr)
                print("    > Successfully extracted data from simon.h5.")
            except Exception as e:
                print("ERROR: unable to pull data from " + self.folder_name + "/simon.h5/physical_quantities/Data. \n\t" + str(e))
            
            df['Job Name'] = self.folder_name
            return df
        except Exception as e:
            print("ERROR: could not retrieve data from simon.h5. \n\t" + str(e))
    
    # Return a pandas representation of our deletion file
    #
    # Edit it to have it point to your relevant data    
    def get_deletion(self):
        try:
            deletion_loc = self.directory_name + "/deletion.h5"
            deletion = h5.File(deletion_loc,'r')
            deletions = deletion.get("Deletion")
            try:
                df = pd.DataFrame(columns=['time','Reason'])
                for dset in list(deletions.keys()):
                    path = str(dset) + "/Data"
                    print("Trying", path)
                    arr = np.array(deletions.get(path))
                    sub_df = pd.DataFrame(arr)
                    sub_df['Reason'] = dset
                    df = pd.concat((sub_df, df))
                    print("    > Successfully extracted data from deletion.h5/" + str(dset))
            except Exception as e:
                print("ERROR: unable to pull data from " + self.folder_name + "/deletion.h5. \n\t" + str(e))
            
            df['Job Name'] = self.folder_name
            return df
        except Exception as e:
            print("ERROR: could not retrieve data from deletion.h5. \n\t" + str(e))