#!/usr/bin/env python
# coding: utf-8

# Import general libraries
import os
import re
import pandas as pd
from datetime import datetime, timedelta

# ----------------------------------------------------------------------------------------------------------- #

def print_to_HTML(statuses, start_time):
    import time
    
    statuses.reset_index()
    home_location = "/beegfs/interns/esnell/Unit_Cells/Home1.html" # <----------------------- EDIT LOCATION
    about_location = "/beegfs/interns/esnell/Unit_Cells/About1.html" # <--------------------- EDIT LOCATION
    try:
    
        # CLEAR CONTENTS OF HOME FILE
        try:
            file = open(home_location,"r+")
            file.truncate(0)
            file.close()
        except Exception as e:
            print("ERROR CLEARING HOME FILE:")
            print("\t" + str(e))
    
        # SET PANDAS OPTIONS
        pd.set_option('colheader_justify', 'center')

        # SET UP HTML OUTPUT STRING
        table, countdowns, countups = get_html_table(statuses, get_categories(statuses))
        
        # WRITE HOME PAGE
        with open(home_location, 'a') as f:
            home_page = return_home_page(home_location, about_location, table, countdowns, countups)
            home_page = home_page.replace("&lt;", "<").replace("&gt;", ">")
            run_time = "{:.2f}".format(time.time() - start_time) + " seconds"
            home_page = home_page.replace("EMBED_RUN_TIME", run_time)
            f.write(home_page)
        
        # WRITE ABOUT PAGE
        with open(about_location, 'w') as f:
            f.write(return_about_page(home_location, about_location))
        
    except Exception as e:
        print(e)

# remove truncation of table elements
pd.set_option('display.max_colwidth', -1)
# ignore chained assignment warnings created by subsetting statuses into complete, running, canceled
pd.options.mode.chained_assignment = None  # default='warn'

def insert_countdown_code(string):
    time = string.split("&&&")[0]
    name = string.split("&&&")[1]
    return "COUNTDOWN_START" + time + "COUNTDOWN_END" + "JOB_CODE_START" + str(name) + "JOB_CODE_END"
    
def insert_countup_code(string):
    time = string.split("&&&")[0]
    name = string.split("&&&")[1]
    return "COUNTUP_START" + time + "COUNTUP_END" + "JOB_CODE_START" + str(name) + "JOB_CODE_END"

def format_datetime(time):
    return time.strftime('%b %d %y %H:%M:%S')

def insert_green_background(item):
    return "BG_SET_GREEN" + str(item)
    
def format_timedelta(timedelta_obj):
    days, seconds = timedelta_obj.days, timedelta_obj.seconds
    hours = str(days * 24 + seconds // 3600).zfill(2)
    minutes = str((seconds % 3600) // 60).zfill(2)
    seconds = str((seconds % 60)).zfill(2)
    return ":".join((hours, minutes, seconds))

def format_percent(percent):
    return '{:0.1f}%'.format(percent)
    
def format_float(flt):
    return '{:.3f}'.format(flt)

def insert_progress_bar_code(percent):
    text = '{:.2f}'.format(percent) + "%"
    show = "PROGRESSBAR_START" + '{:03.0f}'.format(percent) + "PROGRESSBAR_END"
    return insert_hover(text, show)

def get_categories(statuses):
    job_names = list()
    for name in statuses['Job Name'].tolist():
        ## UGLY CODING BUT I DON'T REALLY CARE
        name = name.replace("BG_SET_GREEN", "")
        vals = re.split(', |_|-|!', name[3:])
        for val in vals:
            job_names.append(val)
        
    import collections
    seen = set()
    duplicates = set()
    for val in job_names:
        if val in seen:
            duplicates.add(val)
        else:
            seen.add(val)
    return sorted(duplicates)

def insert_hover(text, show):
    return """<div class="tooltip">""" + show + """<span class="tooltiptext">""" + text + """</span></div>"""

def get_statuses(joblist):
    
    # COLLECT ALL JOBS INTO DATAFRAME
    statuses = list()
    for job in joblist:
        statuses.append(job.timing_data)
    statuses = pd.concat(statuses, axis = 0)

    # columns=['HPC Code', 'Job Name','Percent','Start Time','Elapsed','Remaining','End Time','Description']
    
    # FORMAT PROGRESS w/ HOVER
    statuses['Progress'] = statuses['Percent'].map(lambda pct: insert_progress_bar_code(pct))
    
    # FIND RUNNING JOBS
    cancelmask = statuses.Remaining == "CANCELED"
    completemask = statuses.Remaining == "COMPLETE"
    runningmask = ~(cancelmask | completemask)

    # CREATE NEW DATAFRAMES TO AVOID NEED FOR LOC LATER ON
    running = statuses.loc[runningmask]
    complete = statuses.loc[completemask]
    canceled = statuses.loc[cancelmask]  
     
    # INSERT JAVASCRIPT TIMERS
    running['Remaining'] = running['End Time'].astype(str) + "&&&" + running['Job Name'].astype(str)
    running['Remaining'] = running['Remaining'].map(lambda string: insert_countdown_code(string))
    running['Elapsed'] = running['Start Time'].astype(str) + "&&&" + running['Job Name'].astype(str)
    running['Elapsed'] = running['Elapsed'].map(lambda string: insert_countup_code(string))
   
    # FORMAT RUNNING JOBS TO HAVE LIGHT GREEN FONT
    running = running.applymap(lambda name: insert_green_background(str(name)))
    
    # REFORM TABLE
    statuses = pd.concat((running, complete, canceled), axis=0)
    
    # FORMAT JOB NAME w/ HOVER (IMPLENTATION OFF B/C TOOLTIPS APPEAR BEHIND OTHER TABLE TEXT)
    ## statuses['Job Name'] = statuses.apply(lambda x: insert_hover(x['Description'], x['Job Name']), axis=1)

    # DROP UNUSED COLUMNS
    statuses = statuses[['HPC Code', 'Job Name', 'Elapsed', 'Remaining', 'Progress']]
    
    return statuses
        
def get_html_table(statuses, categories):
    dropdown = """
         <div class="dropdowns">
            <select id="joblist" onchange="dropdown()">
              <option>SELECT JOB FILTER</option>
    """
    dropdown_end = """
            </select>
            <div id="dropdown-padding">
            </div>
            <select id="jobstatus" onchange="dropdown()" class='form-control'>
              <option>SELECT JOB STATUS</option>
              <option>Running</option>
              <option>Complete</option>
              <option>Canceled</option>
            </select>
            <div id="dropdown-padding">
            </div>
            <button onclick="resetDropdowns()" id="reset"><i class="fa-solid fa-sync fa-spin"></i></button>
          </div>
    """
    
    spacer = "\n<div style=\"height: 10px; overflow: hidden; width: 100%;\"></div>"
    
    for category in categories:
        dropdown = dropdown + "<option>" + str(category) + "</option>\n"
    dropdown = dropdown + dropdown_end + "\n</select>"
    
    output_table = dropdown  + spacer + "\n" + statuses.to_html(classes='mystyle', index=False)
    
    # ORDER IS IMPORTANT FOR RegEx SEARCHES
    output_table = embed_green_background(output_table)
    output_table = create_progress_bars(output_table)
    output_table, countdowns = embed_countdowns(output_table)
    output_table, countups = embed_countups(output_table)
    output_table = enable_sorting(output_table)
    
    output_table = output_table.replace("<table border=","<table id=\"dataframe\" border=")
    
    return output_table, countdowns, countups
    
def create_progress_bars(html_string):
    html_string = html_string.replace("PROGRESSBAR_START", "<progress value=\"")
    return html_string.replace("PROGRESSBAR_END", "\" max=\"100\"></progress>")
    
def embed_countdowns(html_string):
    countdowns = "<script>"
    for match in re.finditer(">COUNTDOWN_START(.*)COUNTDOWN_ENDJOB_CODE_START(.*)JOB_CODE_END", html_string):
        if len(match.groups()) > 0 and match.group(1) != "0":
            date = match.group(1)
            code = match.group(2)
                
            # Update HTML to have ID element in right spot
            html_embedding = " id=\"" + code + "CD\">"
            js_embedding = "countdown(\"" + date + "\",\"" + code + "CD\")"
            html_string = re.sub(match.group(0), html_embedding, html_string)
                
            # Update JS to embed countdown element @ ID
            countdowns = countdowns + "\n\t" + js_embedding
    countdowns = countdowns + "\n" + "</script>" 
    return html_string, countdowns

def embed_countups(html_string):
    countups = "<script>"
    for match in re.finditer(">COUNTUP_START(.*)COUNTUP_ENDJOB_CODE_START(.*)JOB_CODE_END", html_string):
        if len(match.groups()) > 0 and match.group(1) != "0":
            date = match.group(1)
            code = match.group(2)
                
            # Update HTML to have ID element in right spot
            html_embedding = " id=\"" + code + "CU\">"
            js_embedding = "countup(\"" + date + "\",\"" + code + "CU\")"
            html_string = re.sub(match.group(0), html_embedding, html_string)
                
            # Update JS to embed countdown element @ ID
            countups = countups + "\n\t" + js_embedding
    countups = countups + "\n" + "</script>" 
    return html_string, countups

def embed_green_background(html_string):
    html_string = html_string.replace(">BG_SET_GREEN", " style=\"color: #6c9c98\">") 
    html_string = re.sub("&gt;BG_SET_GREEN", " style=\"color: #6c9c98\">", html_string)
    return html_string

def enable_sorting(html_string):
    i = 0
    for match in re.finditer(r'<th>(.*)</th>', html_string): 
        # ONLY LOOK FOR TAGS WITH INFORMATION IN THEM
        if(len(match.group(1)) > 0) and match.group(1) != "0":
            sort_function = "<th onclick=\"sort(" + str(i) + ")\">" + match.group(1) + "</th>"
            html_string = re.sub(match.group(0), sort_function, html_string)
            i += 1

    return html_string

def return_javascript():
    return """
<script>
  let goose1 = document.getElementById("goose1");
  let goose2 = document.getElementById("goose2");
  let goose3 = document.getElementById("goose3");
  let goose4 = document.getElementById("goose4");
  let goose5 = document.getElementById("goose5");
  let sleep1 = document.getElementById("gooseSleep1");
  let sleep2 = document.getElementById("gooseSleep2");
  let sleep3 = document.getElementById("gooseSleep3");

  goose1.style.display = "none";
  goose2.style.display = "none";
  goose3.style.display = "none";
  goose4.style.display = "none";
  goose5.style.display = "none";
  sleep1.style.display = "none";
  sleep2.style.display = "none";
  sleep3.style.display = "none";

  function countdown(date, ID) {
    var countDownDate = new Date(date).getTime();
    var x = setInterval(function() {
      var now = new Date().getTime();
      var distance = countDownDate - now;
      var days = Math.floor(distance / (1000 * 60 * 60 * 24));
      var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
      var seconds = Math.floor((distance % (1000 * 60)) / 1000);

      document.getElementById(ID).innerHTML = days + " days " + hours + ":" + minutes + ":" + seconds;
      if (distance < 0) {
        clearInterval(x);
        document.getElementById(ID).innerHTML = "COMPLETE";
      }
    }, 1000);
  }

  function countup(date, ID) {
    var countUpDate = new Date(date).getTime();
    var x = setInterval(function() {
      var now = new Date().getTime();
      var distance = now - countUpDate;
      var days = Math.floor(distance / (1000 * 60 * 60 * 24));
      var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
      var seconds = Math.floor((distance % (1000 * 60)) / 1000);

      document.getElementById(ID).innerHTML = days + " days " + hours + ":" + minutes + ":" + seconds;
      if (distance < 0) {
        clearInterval(x);
        document.getElementById(ID).innerHTML = "INVALID TIME";
      }
    }, 1000);
  }

  function dropdown() {
    var nameinput, namefilter, statusinput, statusfilter, table, tr, i;
    nameinput = document.getElementById("joblist");
    namefilter = nameinput.value.toUpperCase();
    statusinput = document.getElementById("jobstatus");
    statusfilter = statusinput.value.toUpperCase();
    table = document.getElementById("dataframe");
    tr = table.getElementsByTagName("tr");
    for (i = 0; i < tr.length; i++) {
      var tdName, tdStatus, jobvalid, statusvalid, td_id, isRunning;
      tdName = tr[i].getElementsByTagName("td")[1];
      tdStatus = tr[i].getElementsByTagName("td")[3];
      isRunning = false
      try {
        let td_id = tdStatus.id;
        if (td_id) {
          if (td_id.indexOf("CU") > -1 || td_id.indexOf("CD") > -1) {
            isRunning = true;
          }
        }
      } catch (error) {}
      if (tdName && tdStatus) {
        jobvalid = tdName.innerHTML.toUpperCase().indexOf(namefilter.toUpperCase()) > -1 || namefilter == "SELECT JOB FILTER";
        statusvalid = tdStatus.innerHTML.toUpperCase().indexOf(statusfilter.toUpperCase()) > -1 || statusfilter == "SELECT JOB STATUS";
        var runningANDrunning = isRunning && statusfilter.toUpperCase() == "RUNNING";
        statusvalid = statusvalid || (isRunning && statusfilter.toUpperCase() == "RUNNING");
        if (jobvalid && statusvalid) {
          tr[i].style.display = "";
        } else {
          tr[i].style.display = "none";
        }
      }
    }
  }

  function resetDropdowns() {
    var elements = document.getElementsByTagName('select');
    for (var i = 0; i < elements.length; i++) {
      elements[i].selectedIndex = 0;
    }
    var table = document.getElementById("dataframe");
    var tr = table.getElementsByTagName("tr");
    for (i = 0; i < tr.length; i++) {
      var td, tr;
      td = tr[i].getElementsByTagName("td")[1];
      if (td) {
        tr[i].style.display = "";
      }
    }
  }

  sort_direction = true

  function sort(element) {
    sort_direction = !sort_direction
    var table, rows, switching, i, x, y, shouldSwitch;
    table = document.getElementById("dataframe");
    switching = true;
    /*Make a loop that will continue until
    no switching has been done:*/
    while (switching) {
      //start by saying: no switching is done:
      switching = false;
      rows = table.rows;
      /*Loop through all table rows (except the
      first, which contains table headers):*/
      for (i = 1; i < (rows.length - 1); i++) {
        //start by saying there should be no switching:
        shouldSwitch = false;
        /*Get the two elements you want to compare,
        one from current row and one from the next:*/
        x = rows[i].getElementsByTagName("td")[element];
        y = rows[i + 1].getElementsByTagName("td")[element];
        //check if the two rows should switch place:
        if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase() && sort_direction) {
          //if so, mark as a switch and break the loop:
          shouldSwitch = true;
          break;
        } else if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase() && !sort_direction) {
          //if so, mark as a switch and break the loop:
          shouldSwitch = true;
          break;
        }
      }
      if (shouldSwitch) {
        /*If a switch has been marked, make the switch
        and mark that a switch has been done:*/
        rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
        switching = true;
      }
    }
  }

  const onMouseMove = (e) => {
    goose1.style.left = e.pageX + 'px';
    goose1.style.top = e.pageY + 22 + 'px';
    goose2.style.left = e.pageX + 'px';
    goose2.style.top = e.pageY + 22 + 'px';
    goose3.style.left = e.pageX + 'px';
    goose3.style.top = e.pageY + 22 + 'px';
    goose4.style.left = e.pageX + 'px';
    goose4.style.top = e.pageY + 22 + 'px';
    goose5.style.left = e.pageX + 'px';
    goose5.style.top = e.pageY + 22 + 'px';
    sleep1.style.left = e.pageX + 'px';
    sleep1.style.top = e.pageY + 22 + 'px';
    sleep2.style.left = e.pageX + 'px';
    sleep2.style.top = e.pageY + 22 + 'px';
    sleep3.style.left = e.pageX + 'px';
    sleep3.style.top = e.pageY + 22 + 'px';
  }

  document.addEventListener('mousemove', onMouseMove);

  var gooseVis = false;

  function toggleGoose() {
    gooseVis = !gooseVis;
    if (gooseVis) {
      document.body.style.cursor = "none";
      document.getElementById("goose1").style.display = "";
    } else {
      document.body.style.cursor = "";
      document.getElementById("goose1").style.display = "none";
    }
  }

  const onMouseClick = (e) => {
    let goose = document.getElementById("goose1");
    let gooseVis = goose.style.display == "";
    if (gooseVis) {
      cursorClickSwapGoose();
      return;
    }
  }

  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async function cursorClickSwapGoose() {
    let goose1 = document.getElementById("goose1");
    let goose2 = document.getElementById("goose2");
    let goose3 = document.getElementById("goose3");
    let goose4 = document.getElementById("goose4");
    let goose5 = document.getElementById("goose5");
    goose1.style.display = "none";
    goose2.style.display = "";
    await sleep(60);
    goose2.style.display = "none";
    goose3.style.display = "";
    await sleep(60);
    goose3.style.display = "none";
    goose2.style.display = "";
    await sleep(60);
    goose2.style.display = "none";
    goose4.style.display = "";
    await sleep(75);
    goose4.style.display = "none";
    goose5.style.display = "";
    await sleep(75);
    goose5.style.display = "none";
    goose1.style.display = "";
  }

  let table = document.getElementById("dataframe");
  table.addEventListener('click', onMouseClick);

  function waitingMouseMove() {
    return new Promise((resolve) => {
      document.addEventListener('mousemove', onMoveHandler);
      document.addEventListener('click', onMoveHandler);
      document.addEventListener('keydown', onMoveHandler);
      function onMoveHandler(e) {
          document.removeEventListener('keydown', onMoveHandler);
          document.addEventListener('click', onMoveHandler); 
          document.addEventListener('keydown', onMoveHandler);
          resolve();
      }
    });
  }
 
  var timeout;
  document.onmousemove = document.onmouseclick = document.onkeydown = function(){
    clearTimeout(timeout);
    timeout = setTimeout(function(){gooseSleep();}, 8000);
  }

  async function gooseSleep() {
    let goose1 = document.getElementById("goose1");
    let gooseVis = goose1.style.display == "";
    if (gooseVis) {
      let sleep1 = document.getElementById("gooseSleep1");
      let sleep2 = document.getElementById("gooseSleep2");
      let sleep3 = document.getElementById("gooseSleep3");
      goose1.style.display = "none";
      sleep1.style.display = "";
      await sleep(60);
      sleep1.style.display = "none";
      sleep2.style.display = "";
      await sleep(60);
      sleep2.style.display = "none";
      sleep3.style.display = "";
      await waitingMouseMove();
      await sleep(60);
      sleep3.style.display = "none";
      sleep2.style.display = "";
      await sleep(60);
      sleep2.style.display = "none";
      sleep1.style.display = "";
      await sleep(60);
      sleep1.style.display = "none";
      goose1.style.display = "";
    }
  }

</script>
        """
   
def return_CSS_styling():
    return """
<!-- CREDIT TO @PickJBennett FOR WAVE BACKGROUND AND GOOSE JAVASCRIPT -->
<style>
  @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@700&family=Quicksand&display=swap');

  :root {
    -webkit-box-sizing: border-box;
    -moz-box-sizing: border-box;
    -ms-box-sizing: border-box;
    -o-box-sizing: border-box;
    box-sizing: border-box;
    cursor: default;
    -webkit-user-select: none;
    -moz-user-select: none;
    -ms-user-select: none;
    -o-user-select: none;
    user-select: none;
  }

  *,
  :before,
  :after {
    -webkit-box-sizing: inherit;
    -moz-box-sizing: inherit;
    -ms-box-sizing: inherit;
    -o-box-sizing: inherit;
    box-sizing: inherit;
  }

  html,
  body {
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    left: 0;
    display: block;
    width: 100%;
    height: 100%;
  }

  html {
    overflow: hidden;
  }

  body {
    margin: 0;
    overflow: auto;
    overflow-x: hidden;
    overflow-y: scroll;
    -webkit-overflow-scrolling: touch;
    -moz-overflow-scrolling: touch;
    -ms-overflow-scrolling: touch;
    -o-overflow-scrolling: touch;
    overflow-scrolling: touch;
    -ms-overflow-style: ms-autohiding-scrollbar;
  }

  #page-wrap {
    position: relative;
    display: block;
    clear: both;
    background: none;
    color: #000;
    text-decoration: none;
    padding: 3rem 0;
    width: 100%;
    height: 100%;
  }

  #inner-wrap {
    position: absolute;
    top: 3rem;
    left: 0;
    right: 0;
    bottom: 3rem;
    display: table;
    width: 100%;
    height: 100%;
    min-height: 322px;
    overflow: visible;
  }

  .waves {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: block;
    min-width: 100%;
    min-height: 15%;
    margin: auto 0;
  }

  img,
  svg {
    display: block;
    overflow: visible;
    pointer-events: none;
  }

  .group:before,
  .group:after {
    content: "";
    display: table;
    clear: both;
  }

  .group {
    zoom: 1;
  }

  .page-header {
    width: 100%;
    padding: 10px 16px;
    background-color: #8286ab;
  }

  html {
    overflow-y: scroll;
  }

  body {
    margin: 0px;
    padding: 0px;
    font-family: 'Cormorant Garamond', serif;
    background-color: #fdfdfe;
  }

  * {
    box-sizing: border-box;
  }

  header {
    width: 100%;
    height: 5vh;
    display: inline-block;
    flex-direction: column;
    align-items: center;
  }

  header h2 {
    position: relative;
    left: 25%;
    width: 50%;
    font-size: 40px;
    font-weight: bold;
    color: transparent;
    -webkit-background-clip: text;
    background-clip: text;
  }

  header .header-1 {
    background-image: repeating-radial-gradient(farthest-side at 5px 5px, #4d4d4d, #8286ab, #252b54);
  }

  p,
  li {
    font-family: 'Quicksand', sans-serif;
    position: relative;
    left: 25%;
    width: 50%;
    font-size: 18px;
  }

  @page {

    margin: 100px 25px;
    size: letter portrait;

    @top-left {
      content: element(pageHeader);
    }

    @bottom-left {
      content: element(pageFooter);
    }
  }

  #pageHeader {
    position: running(pageHeader);
  }

  #pageFooter {
    position: running(pageFooter);
  }

  .button {
    font-weight: bold;
    background-color: transparent;
    border-width: 0px;
    color: white;
    text-align: center;
    text-decoration: none;
    align-items: center;
    font-size: 16px;
    margin: 4px 2px;
    cursor: pointer;
    width: 80px;
    height: 40px;
    display: inline-block;
  }

  .button::hover {
    font-weight: bold;
  }

  .header-buttons {
    font-family: 'Quicksand', sans-serif;
    font-weight: bold;
    text-align: center;
    font-size: 16px;
    display: inline-block;
  }

  .dropdowns {
    position: relative;
    display: flex;
    left: 10%;
  }

  #joblist,
  #jobstatus {
    font-size: 16px;
    padding: 12px 12px 12px 12px;
    border: thin solid #ddd;
    font-family: 'Quicksand', sans-serif;
    width: 37%;
    box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
  }

  #reset {
    font-size: 16px;
    font-family: 'Quicksand', sans-serif;
    width: 5%;
    text-align: center;
    background-color: transparent;
    background-repeat: no-repeat;
    cursor: pointer;
    border: thin solid #ddd;
    overflow: hidden;
    box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
  }

  #dropdown-padding {
    width: 0.5%;
  }

  #dataframe {
    z-index: 1;
    position: relative;
    border-collapse: collapse;
    width: 80%;
    margin-left: auto;
    margin-right: auto;
    border: thin solid #ddd;
    font-size: 18px;
    box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
  }

  .mystyle td,
  th {
    padding: 5px;
    text-align: center;
    font-family: 'Quicksand', sans-serif;
    background-color: rgba(255, 255, 255, 0.85);
  }

  .mystyle tr:hover {
    background: #c8cada;
    font-weight: bold;
  }

  #footer {
    z-index: 2;
    position: fixed;
    height: 60px;
    background-color: white;
    bottom: 0px;
    left: 0px;
    right: 0px;
    margin-bottom: 0px;
    box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
  }

  .footer {
    left: 2%;
    width: 100%;
  }

  .tooltip {
    position: relative;
    display: inline-block;
    z-index: 4;
  }

  .tooltip .tooltiptext {
    visibility: hidden;
    background-color: white;
    color: #000;
    text-align: center;
    border-radius: 6px;
    padding: 15px 15px;
    /* Position the tooltip */
    position: absolute;
    z-index: 4;
  }

  progress[value] {
    /* Reset the default appearance */
    -webkit-appearance: none;
  }

  progress[value]::-webkit-progress-value::before {
    content: '100%';
    position: relative;
  }

  ::-webkit-progress-bar {
    background-color: transparent;
  }

  progress[value]::-webkit-progress-value {
    background:
      -webkit-linear-gradient(-45deg,
        transparent 33%, rgba(0, 0, 0, .1) 33%,
        rgba(0, 0, 0, .1) 66%, transparent 66%),
      -webkit-linear-gradient(top,
        rgba(255, 255, 255, .25),
        rgba(235, 235, 235, .75)),
      -webkit-linear-gradient(left, #8286ab, #8286ab);

    border-radius: 2px;
    background-size: 35px 20px, 100% 100%, 100% 100%;
  }

  .tooltip:hover .tooltiptext {
    visibility: visible;
    left: 105%;
    widtH: 100%;
    font-size: 16px;
    border-style: solid;
    border-width: thin;
    border-color: #8286ab;
  }

  #goose1,
  #goose2,
  #goose3,
  #goose4,
  #goose5,
  #gooseSleep1,
  #gooseSleep2,
  #gooseSleep3
  {
    position: absolute;
    z-index: 3;
    transform: translate(-50%, -50%);
    height: 100px;
    width: 125px;
  }

</style>
"""

def return_header(home_location, about_location, wave):
    # Create the html page header with links between the home and about page
    # Embed the pretty wave in the html background if wave is True
    # Create the goose button
    if wave:
        wave_text = return_wave()
    else:
        wave_text = ""
    return return_goose() + """
    <div class="page-header" id="myHeader">
	<div style="height: 10px; overflow: hidden; width: 100%;"></div>
        <header id="pageHeader"> """ + wave_text + """
            <div style="height: 10px; overflow: hidden; width: 100%;"></div>
            <div class="header-buttons">
                <a class="button" href="
""" + \
                home_location + \
                """
                ">HOME</a>
	    	    <a class="button" href="
                """ + \
                about_location + \
                """
                ">ABOUT</a>
                <a class="button" onclick="toggleGoose()"><i class="fa-solid fa-feather-pointed"></i></a>
	        </div>
            <div style="height: 5px; overflow: hidden; width: 100%;"></div>
        </header>
    </div>
    """

def return_goose():
    # Access the goose images from Eric's imgur
    # Add a link to allow access to Font Awesome icons
    return """
  <script src="https://kit.fontawesome.com/a72cbe7dc2.js" crossorigin="anonymous"></script>
  <img id="goose1" src="https://i.imgur.com/944FjfE.png" alt="Goose!" />
  <img id="goose2" src="https://i.imgur.com/XYEg2dM.png" alt="Goose!" />
  <img id="goose3" src="https://i.imgur.com/KZcFu1Y.png" alt="Goose!" />
  <img id="goose4" src="https://i.imgur.com/3TUmL41.png" alt="Goose!" />
  <img id="goose5" src="https://i.imgur.com/muAA3za.png" alt="Goose!" />
  <img id="gooseSleep1" src="https://i.imgur.com/cnApVFD.png" alt="Zzz!" />
  <img id="gooseSleep2" src="https://i.imgur.com/70m7z6a.png" alt="Zzz!" />
  <img id="gooseSleep3" src="https://i.imgur.com/KaKqirc.png" alt="Zzz!" />    
    """

def return_wave():
    # CREDIT TO @PickJBennett FOR WAVE BACKGROUND AND JAVASCRIPT
    # Makes a nice little wavy background
    return """
    <div id="inner-wrap"><svg class="waves" xmlns="http://www.w3.org/2000/svg" width="1440" height="321.75" viewBox="0 0 960 214.5" preserveAspectRatio="xMinYMid meet">
        <defs>
          <style>
            .waves>path {
              -webkit-animation: a 17390ms ease-in-out infinite alternate-reverse both;
              -moz-animation: a 17390ms ease-in-out infinite alternate-reverse both;
              -ms-animation: a 17390ms ease-in-out infinite alternate-reverse both;
              -o-animation: a 17390ms ease-in-out infinite alternate-reverse both;
              animation: a 17390ms ease-in-out infinite alternate-reverse both;
              -webkit-animation-timing-function: cubic-bezier(.25, 0, .75, 1);
              -moz-animation-timing-function: cubic-bezier(.25, 0, .75, 1);
              -ms-animation-timing-function: cubic-bezier(.25, 0, .75, 1);
              -o-animation-timing-function: cubic-bezier(.25, 0, .75, 1);
              animation-timing-function: cubic-bezier(.25, 0, .75, 1);
              -webkit-will-change: transform;
              -moz-will-change: transform;
              -ms-will-change: transform;
              -o-will-change: transform;
              will-change: transform
            }

            .waves>path:nth-of-type(1) {
              -webkit-animation-duration: 20580ms;
              -moz-animation-duration: 20580ms;
              -ms-animation-duration: 20580ms;
              -o-animation-duration: 20580ms;
              animation-duration: 20580ms
            }

            .waves>path:nth-of-type(2) {
              -webkit-animation-delay: -2690ms;
              -moz-animation-delay: -2690ms;
              -ms-animation-delay: -2690ms;
              -o-animation-delay: -2690ms;
              animation-delay: -2690ms;
              -webkit-animation-duration: 13580ms;
              -moz-animation-duration: 13580ms;
              -ms-animation-duration: 13580ms;
              -o-animation-duration: 13580ms;
              animation-duration: 13580ms
            }

            g>path:nth-of-type(1) {
              -webkit-animation-delay: -820ms;
              -moz-animation-delay: -820ms;
              -ms-animation-delay: -820ms;
              -o-animation-delay: -820ms;
              animation-delay: -820ms;
              -webkit-animation-duration: 10730ms;
              -moz-animation-duration: 10730ms;
              -ms-animation-duration: 10730ms;
              -o-animation-duration: 10730ms;
              animation-duration: 10730ms
            }

            .waves>path:nth-of-type(1),
            g>path:nth-of-type(2) {
              -webkit-animation-direction: alternate;
              -moz-animation-direction: alternate;
              -ms-animation-direction: alternate;
              -o-animation-direction: alternate;
              animation-direction: alternate
            }

            @-webkit-keyframes a {
              0% {
                -webkit-transform: translateX(-750px);
                transform: translateX(-750px)
              }

              100% {
                -webkit-transform: translateX(-20px);
                transform: translateX(-20px)
              }
            }

            @-moz-keyframes a {
              0% {
                -moz-transform: translateX(-750px);
                transform: translateX(-750px)
              }

              100% {
                -moz-transform: translateX(-20px);
                transform: translateX(-20px)
              }
            }

            @-ms-keyframes a {
              0% {
                -ms-transform: translateX(-750px);
                transform: translateX(-750px)
              }

              100% {
                -ms-transform: translateX(-20px);
                transform: translateX(-20px)
              }
            }

            @-o-keyframes a {
              0% {
                -o-transform: translateX(-750px);
                transform: translateX(-750px)
              }

              100% {
                -o-transform: translateX(-20px);
                transform: translateX(-20px)
              }
            }

            @keyframes a {
              0% {
                -webkit-transform: translateX(-750px);
                -moz-transform: translateX(-750px);
                -ms-transform: translateX(-750px);
                -o-transform: translateX(-750px);
                transform: translateX(-750px)
              }

              100% {
                -webkit-transform: translateX(-20px);
                -moz-transform: translateX(-20px);
                -ms-transform: translateX(-20px);
                -o-transform: translateX(-20px);
                transform: translateX(-20px)
              }
            }

          </style>
          <linearGradient id="a">
            <stop stop-color="#c8dad8" />
            <stop offset="0.2" stop-color="#c8cada" />
            <stop offset="0.4" stop-color="#dac8ca" />
            <stop offset="0.6" stop-color="#dad8c8" />
          </linearGradient>
        </defs>
        <path fill="url(#a)" d="M2662.6 1S2532 41.2 2435 40.2c-19.6-.2-37.3-1.3-53.5-2.8 0 0-421.3-59.4-541-28.6-119.8 30.6-206.2 75.7-391 73.3-198.8-2-225.3-15-370.2-50-145-35-218 37-373.3 36-19.6 0-37.5-1-53.7-3 0 0-282.7-36-373.4-38C139 26 75 46-1 46v106c17-1.4 20-2.3 37.6-1.2 130.6 8.4 210 56.3 287 62.4 77 6 262-25 329.3-23.6 67 1.4 107 22.6 193 23.4 155 1.5 249-71 380-62.5 130 8.5 209 56.3 287 62.5 77 6 126-18 188-18 61.4 0 247-38 307.4-46 159.3-20 281.2 29 348.4 30 67 2 132.2 6 217.4 7 39.3 0 87-11 87-11V1z" />
        <path fill="#F2F5F5" d="M2663.6 73.2S2577 92 2529 89c-130.7-8.5-209.5-56.3-286.7-62.4s-125.7 18-188.3 18c-5 0-10-.4-14.5-.7-52-5-149.2-43-220.7-39-31.7 2-64 14-96.4 30-160.4 80-230.2-5.6-340.4-18-110-12-146.6 20-274 36S820.4 0 605.8 0C450.8 0 356 71 225.2 62.2 128 56 60.7 28-.3 11.2V104c22 7.3 46 14.2 70.4 16.7 110 12.3 147-19.3 275-35.5s350 39.8 369 43c27 4.3 59 8 94 10 13 .5 26 1 39 1 156 2 250-70.3 381-62 130.5 8.2 209.5 56.3 286.7 62 77 6.4 125.8-18 188.3-17.5 5 0 10 .2 14.3.6 52 5 145 49.5 220.7 38.2 32-5 64-15 96.6-31 160.5-79.4 230.3 6 340 18.4 110 12 146.3-20 273.7-36l15.5-2V73l1-.5z" />
        <g fill="none" stroke="#E2E9E9" stroke-width="1">
          <path d="M0 51.4c3.4.6 7.7 1.4 11 2.3 133.2 34 224.3 34 308.6 34 110.2 0 116.7 36.6 229.8 26 113-11 128.7-44 222-42.6C865 73 889 38 1002 27c113-10.8 119.6 25.6 229.8 25.6 84.4 0 175.4 0 308.6 34 133 34.2 277-73 379.4-84.3 204-22.5 283.6 128.7 283.6 128.7" />
          <path d="M0 6C115.7-6 198.3 76.6 308 76.6c109.6 0 131.8-20 223-28.3 114.3-10.2 238.2 0 238.2 0s124 10.2 238.3 0c91-8.2 113.2-28 223-28S1425 103 1541 91c115.8-11.8 153.3-69 269.3-84.6 116-15.5 198.4 71 308 71 109.8 0 131.8-20 223-28 114-10.2 237.7 0 237.7 0s37.4 2.4 82.8 3.7" />
        </g>
      </svg>
    </div>    
    """

def return_about_page(home_location, about_location):
    # Returns the about page that explains how the script works
    home_location = home_location.replace("/beegfs", "")
    about_location = about_location.replace("/beegfs", "")
    return "<!DOCTYPE html>" + return_CSS_styling() + \
"""
<html>
    """ + return_header(home_location, about_location, False) + """
    <head>
	<title>About this Script</title>
    </head>
    <body><div class="content">
        <div class="body">
	    <div style="height: 10px; overflow: hidden; width: 100%;"></div>
            <header><h2 class="header-1">ABOUT:</h2></header>
            <p>
                This tool uses a Python 3.7 wrapper to evaluate Velodyne folders as "job" objects and show HPC run statuses. 
                It will search for all subfolders in your current working directory and, if they have key files like 
                <em>velodyne.card</em>, <em>status.timestep</em>, and your <em>.o###### </em>output file, will pull 
                in useful information. Necessary libraries include but are not limited to pandas, OS, and datetime.
                <br /><br />Using a pandas DataFrame of run information, the script generates a local .html file with embedded JavaScript functionality. 
                The information in this webpage will be updated each time you run the script.
            </p>
            <header><h2 class="header-1">HOW TO USE:</h2></header>
            <p> You can either call the globalstatus.py script within the desired directory every time you want an update,
                or you can schedule a crontab job to run the script on auto mode. If the script run time is > 10 seconds, maybe
                don't run it automatically.</br></br>
                
                If not... how to run automatically:
                
                <ul>
                    <li>Change globalstatus.py to chdir() to your desired directory when running auto mode.</li>
                    <li>You'll want a file lock to prevent the script from running if it is already going. 
                        We use <a href="https://stackoverflow.com/questions/2366693/run-cron-job-only-if-it-isnt-already-running">flock</a> for this purpose.
                        Create a file called flock.locfile somewhere in your directory.
                    </li>
                    <li>Crontab: run "crontab -e" in your linux environment and then insert </br></br>
                        "*/15 8-17 * * 1-5 /usr/bin/flock -n [flock.locfile LOCATION] /opt/Software/python/3.7/bin/python3 [globalstatus.py LOCATION] auto"</br></br>
                    </li>
                    <li>This will run the globalstatus.py script on auto mode at certain intervals. In this example:
                        </br></br>
                        <ul>
                            <li>*/15 means every 15 minutes during...</li>
                            <li>8-17 means 8 am to 5 pm during...</li>
                            <li>* means every month</li>
                            <li>* means every year</li>
                            <li>1-5 means Monday-Friday.</li>
                        </ul>
                        </br>
                        If you want to create your own timing and are struggling, I recommend <a href="https://crontab.guru/">Crontab Guru</a>.
                    </li>
                </ul>
            </p>
            <header><h2 class="header-1">TROUBLESHOOTING:</h2></header>
            <p>There are five main components to the script:</p>
                <ul>
                    <li>job.py</li>
                    <li>localjobs.py</li>
                    <li>globaljobs.py</li>
                    <li>getstatuses.py</li>
                    <li>globalstatus.py</li>
                </ul>
            <p>
                The job file is a wrapper for your Velodyne files. 
                It reads in information from the Velodyne input / output files into a job object. </br></br>
                
                Localjobs provides OS functionality to search within your /beegfs/users/ folder for potential 
                Velodyne runs. This functionality is one layer deep in that it only looks for folders 
                within the directory from which you call it. </br></br>
                
                Globaljobs makes the functionality two layers deep by calling localjobs for each folder 
                within the current working directory. </br></br>
                
                Getstatuses, when given a list of jobs, will extract information from the job objects and 
                print the information to a user-friendly .html file with embedded JavaScript functionality. </br></br>
                
                Globalstatus runs the whole operation. It pulls in jobs from globaljobs, then calls the
                necessary methods in getstatuses to create the html pages.
            </p>
            <header><h2 class="header-1">NOTES ON EDITING SCRIPT:</h2></header>
            <p>
                If you want the website to display different information, all you need to do is: </br>
            </p>
                <ul>
                    <li>First, edit get_timing_info() in the job.py file to return what you want</li>
                    <li>Second, edit the get_statuses(joblist) method in getstatuses.py to display your new information in the table</li>
                </ul>
            <p>
                When reading information from Velodyne files, make sure to employ the methods get_first_n_lines() 
                and get_last_n_lines() instead of using readlines() to avoid unnecessary memory accesses.<br/><br/>
                
                Getstatuses.py interacts directly with the job.timing_info field generated by get_timing_info() in the 
                job constructor. Thus, any changes to what job.get_timing_info() returns will likely mean you have to 
                change the getstatuses.py file.<br /><br />
                
                Recursive job searching functionality is possible with os.walk(), 
                but not implemented.</span><br /><br />
                
                Adding functionality using other scripts to batch process results is easy. Simply use the Job access 
                and mutate methods (write your own based on template methods, if needed) to get the information you need. 
                Localjobs will return all local jobs, or you can use globaljobs to read in jobs from two layers deep.
                Once you have the Job objects, you can do things like call job.get_timehist() to return the timehist.h5
                information as a pandas dataframe.
            </p>
            <header><h2 class="header-1">GOAL FUNCTIONALITY:</h2></header>
            <p>
            Additional features:
            </p>
                <ul>
                    <li>Search bar</li>
                    <li>Corvid logo</li>
                    <li>Fix the tooltip CSS so that we can have the job description appear when you hover the job name. Currently it appears behind the text.</li>
                </ul>
	    <div style="height: 85px; overflow: hidden; width: 100%;"></div>
        <div id="footer">
            <p class="footer">Tool developed by <a href="mailto:eric.snell@corvidtec.com">Eric Snell</a>.""" + " | Last Updated: " + str(datetime.now().strftime("%I:%M %p")) + """</p>
        </div>
        </div>
    </div>
    </body>
</html>
""" + return_javascript()

def return_home_page(home_location, about_location, table, countdowns, countups):
    # Returns a nice little home page
    home_location = home_location.replace("/beegfs", "")
    about_location = about_location.replace("/beegfs", "")
    return "<!DOCTYPE html>" + return_CSS_styling() + \
"""
<html>
    """ + return_header(home_location, about_location, True) + """
    <head>
	<title>Velodyne Job Statuses</title>
    </head>
    <body class="no-header-page  wsite-page-about  full-width-body-off header-overlay-on alt-nav-off  wsite-theme-light"><div class="wrapper">
        <div class="body">
            <div style="height: 10px; overflow: hidden; width: 100%;"></div>
            <div class="wsite-spacer" style="height:10px;"></div>
            <div class="myTABLE">""" + \
                table + \
            """</div>
            <div style="height: 70px; width: 100%;"></div>
            <div id="footer">
                <p class="footer">Tool developed by <a href="mailto:eric.snell@corvidtec.com">Eric Snell</a>.""" + " | Last Updated: " + str(datetime.now().strftime("%I:%M %p")) + " | Script Run Time: EMBED_RUN_TIME" + """</p>
            </div>
        </div></div>
    </body>
</html>
""" + return_javascript() + countdowns + countups

# ----------------------------------------------------------------------------------------------------------- #