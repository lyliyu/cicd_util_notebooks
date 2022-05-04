# Databricks notebook source
MIN_JOB_DUR_HRS = 0.5
SKIP_SIGHTINGS = 5
CLUSTER_ID = "" # if empty, all clusters will be included.

# COMMAND ----------

from databricks_cli import *
from databricks_cli.sdk import *
from databricks_cli.workspace.api import *
from databricks_cli.jobs.api import *
from databricks_cli.runs.api import *

TOKEN = dbutils.entry_point.getDbutils().notebook().getContext().apiToken().get()
HOST = dbutils.entry_point.getDbutils().notebook().getContext().apiUrl().get()

client = ApiClient(token = TOKEN, host = HOST, verify = False)
jobs_client = JobsApi(client)
runs_client = RunsApi(client)

# COMMAND ----------

created_jobs = jobs_client.list_jobs()["jobs"]

# COMMAND ----------

from datetime import datetime, timezone, date
from dateutil.relativedelta import relativedelta
from dateutil import tz
to_zone = tz.gettz('America/New_York')

today = date.today()
yesterday = today - relativedelta(days=1)

# COMMAND ----------

intervals = []
for j in created_jobs:
  js = j['settings']
  if 'schedule' in js and js['schedule']['pause_status'] == "UNPAUSED":
    run_hist = runs_client.list_runs(j["job_id"], True, True, 0, 25)
    if "runs" not in run_hist: continue
    skipped = 0
    for r in run_hist["runs"]:
      dur_hrs = (r["end_time"] - r["start_time"])/(1000*3600.0)
      if dur_hrs < MIN_JOB_DUR_HRS: 
        if skipped >= SKIP_SIGHTINGS:
          print(f"Job {j['job_id']} skipped after skipping {skipped} short-runs.")
          break
        else :
          skipped += 1
          continue
      start_time = datetime.fromtimestamp(r["start_time"]//1000, to_zone)
      start_date = start_time.date()
      end_time = datetime.fromtimestamp(r["end_time"]//1000, to_zone)
      if start_date == yesterday:
        if (CLUSTER_ID == "") or ("existing_cluster_id" in js and js["existing_cluster_id"] == CLUSTER_ID):
          intervals.append([js['name'], start_time, end_time])
          print(js['name'], start_time, end_time)
    #     print(run_hist)
          break

# COMMAND ----------

# importing package
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

fig, ax = plt.subplots(figsize=(20, 20), constrained_layout=True)
ax.xaxis.set_minor_locator(mdates.HourLocator())
ax.xaxis.set_major_formatter(
    mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
ax.grid(True)
ax.set_title(CLUSTER_ID)

#ax.yaxis.set_visible(False)
for i, segment in enumerate(intervals):
  job_id, start, end = segment
  x = [start, end]
  y = [str(job_id), str(job_id)]
  plt.plot(x, y)
plt.show()

# COMMAND ----------


