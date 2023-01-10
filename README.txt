This is a Python 3.7 wrapper to check your job statuses in Velodyne. It'll search in a pattern like this:

Current Folder
	- Subfolder 1
		- Velodyne Run #1
		- Velodyne Run #2
		- ...
	- Subfolder 2
		- Velodyne Run #1
		- Velodyne Run #2
		- ...
	- etc

To adapt to your specific library, you'll need to do two things:

1) Go to line 28 in globalstatus.py and change it to whatever your local directory is ("Current Folder", in the example)
2) Go to lines 16 and 17 in getstatuses.py and change the location to wherever you want--this is where it'll print an HTML file with all your job information