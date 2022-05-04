# Databricks notebook source
# MAGIC %pip install databricks-cli

# COMMAND ----------

# MAGIC %run ./deploy_utils

# COMMAND ----------

dbutils.widgets.removeAll()
dbutils.widgets.text("git_hash", "", "Git Hash")
dbutils.widgets.text("proj_dir", "", "Project Directory")

# COMMAND ----------

git_hash = dbutils.widgets.get("git_hash")
proj_dir = dbutils.widgets.get("proj_dir").strip("/")

# COMMAND ----------

target_root = "/Users/lyu/dbis_projs" # "/DBIS_ADMIN_AREA/CON1/CON1(ECC3LAN - DataQuality)"
target_proj_dir = proj_dir #change this if sub directory (proj_dir) in github is different from deployment target directory

# COMMAND ----------

# MAGIC %md ### Environment Variables

# COMMAND ----------

# MAGIC %md Job Parameters

# COMMAND ----------

import os

job_params = {
  "target_dir": os.path.join(target_root, target_proj_dir)
#   "target_dir": "/DBIS_ADMIN_AREA/CON1/CON1(ECC3LAN - DataQuality)/dataQuality"
}

# COMMAND ----------

cluster_conf = {"existing_cluster_id": "1113-180731-purrs217"}
# cluster_conf = {"new_cluster": create_cluster_settings()}

# COMMAND ----------

# MAGIC %md Repo settings

# COMMAND ----------

repo_name = "data_quality_tool"
# git_hash = "data_quality_impl"

git_user = "lyu"
git_token = dbutils.secrets.get(scope = "deploy_scope", key = "git_token")

# COMMAND ----------

# MAGIC %md Job Definitions

# COMMAND ----------

job_conf_path = os.path.join(job_params["target_dir"], "deploy/jobs")
print(job_conf_path)

# COMMAND ----------

# MAGIC %md Intrinsic settings

# COMMAND ----------

notebook_overwrite = False

# COMMAND ----------

# MAGIC %md ### check out from github

# COMMAND ----------

work_dir = create_work_dir()

# COMMAND ----------

clone_and_checkout(repo_name, git_hash, work_dir, git_user, git_token)

# COMMAND ----------

# MAGIC %md ### Import to workspace

# COMMAND ----------

from databricks_cli import *
from databricks_cli.sdk import *
from databricks_cli.workspace.api import *
from databricks_cli.jobs.api import *

TOKEN = dbutils.entry_point.getDbutils().notebook().getContext().apiToken().get()
HOST = dbutils.entry_point.getDbutils().notebook().getContext().apiUrl().get()

client = ApiClient(token = TOKEN, host = HOST, verify = False)
job_client = JobsApi(client)
ws = WorkspaceApi(client)

# COMMAND ----------

src_dir = os.path.join(work_dir, repo_name, proj_dir)
target_dir = job_params["target_dir"]
print(f"import {src_dir} to {target_dir}")

# COMMAND ----------

try:
  ws.list_objects(target_dir)
  ws.delete(target_dir, True)
except Exception as e: print(e)

# COMMAND ----------

ws.import_workspace_dir(src_dir, target_dir, overwrite=notebook_overwrite, exclude_hidden_files=True)

# COMMAND ----------

# MAGIC %md ### Deploy jobs

# COMMAND ----------

try:
  ws.list_objects(job_conf_path)
except Exception as e:
  print("No jobs to deploy.")
  clean_up(work_dir)
  dbutils.notebook.exit(0)

# COMMAND ----------

jobs_json = dbutils.notebook.run(job_conf_path, 3600)

# COMMAND ----------

for k, v in job_params.items():
  target = "{{" + str(k) + "}}"
  print(target)
  jobs_json = jobs_json.replace(target, v)

# COMMAND ----------

jobs_json

# COMMAND ----------

jobs_to_deploy = json.loads(jobs_json)["jobs"]

# COMMAND ----------

for job_conf in jobs_to_deploy:
  inject_cluster_conf(job_conf, cluster_conf)

# COMMAND ----------

jobs_to_deploy

# COMMAND ----------

if not jobs_to_deploy:
  print("Warning: There is no job to deploy.")
  clean_up(work_dir)
  dbutils.notebook.exit(0)

# COMMAND ----------

created_jobs = job_client.list_jobs()["jobs"]
for jd in jobs_to_deploy:
  if find_job_by_name(created_jobs, jd['name']):
    print(f"Job {jd['name']} already created.")
  else:
    print(f"Create job {jd['name']}")
    
    job_client.create_job(json=jd)

# COMMAND ----------

clean_up(work_dir)