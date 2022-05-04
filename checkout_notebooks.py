# Databricks notebook source
# MAGIC %pip install databricks-cli

# COMMAND ----------

# MAGIC %run ./deploy_utils

# COMMAND ----------

dbutils.widgets.removeAll()
dbutils.widgets.text("repo_branch", "", "Repo:Branch")
dbutils.widgets.text("proj_dir", "", "Project Directory")
dbutils.widgets.text("target_dir", "", "Target Directory")
# dbutils.widgets.text("overwrite", "False", "Overwrite")

# COMMAND ----------

repo_branch = dbutils.widgets.get("repo_branch")
repo_name, branch_name = repo_branch.split(":")
repo_name = repo_name.strip()
branch_name = branch_name.strip()
proj_dir = dbutils.widgets.get("proj_dir").strip("/")
target_dir = dbutils.widgets.get("target_dir").rstrip("/")
notebook_overwrite = True #eval(dbutils.widgets.get("overwrite"))
print(f"check out from {repo_name}: {branch_name} to {target_dir} {notebook_overwrite}")

# COMMAND ----------

# MAGIC %md Repo settings

# COMMAND ----------

git_user = "lyu"
git_token = dbutils.secrets.get(scope = "deploy_scope", key = "git_token")

# COMMAND ----------

# MAGIC %md ### check out from github

# COMMAND ----------

work_dir = create_work_dir()

# COMMAND ----------

clone_and_checkout(repo_name, branch_name, work_dir, git_user, git_token)

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
print(f"import {src_dir} to {target_dir}")

# COMMAND ----------

if notebook_overwrite:
  try:
    ws.list_objects(target_dir)
    ws.delete(target_dir, True)
  except Exception as e: print(e)

# COMMAND ----------

ws.import_workspace_dir(src_dir, target_dir, overwrite=False, exclude_hidden_files=True)

# COMMAND ----------

clean_up(work_dir)

# COMMAND ----------

