# Databricks notebook source
import os, shutil, uuid
from databricks_cli import *
from databricks_cli.sdk import *
from databricks_cli.workspace.api import *
import subprocess, sys
import json

# COMMAND ----------

def create_work_dir():
  deploy_uuid = str(uuid.uuid4())
  work_dir = "/tmp/{}".format(deploy_uuid)
  print("work_dir: {}".format(work_dir))
  if not os.path.exists(work_dir):
    os.mkdir(work_dir)
  return work_dir

# COMMAND ----------

def clean_up(workDir: str):
  shutil.rmtree(workDir)

# COMMAND ----------

def create_git_clone_url(repoName: str, git_username: str, git_token: str):
#   git_username = dbutils.secrets.get(scope = "deploy_scope", key = "git_user")
#   git_token = dbutils.secrets.get(scope = "deploy_scope", key = "git_token")
  git_url = f"https://{git_username}:{git_token}@git.uscis.dhs.gov/USCIS/{repoName}.git"
  return git_url


# COMMAND ----------

def clone_and_checkout(repoName: str, gitHash: str, workDir: str, gitUser: str, gitToken: str):
#   branches = [br.strip() for br in gitHash.split("=>")]
  git_url = create_git_clone_url(repoName, gitUser, gitToken)
  lines = '''
#!/bin/bash
set -e

mkdir -p {workspace} && cd {workspace}
if [ -d ./{repo_name} ]; then
  rm -rf ./{repo_name}
fi
echo "git clone from {git_url}"
git clone {git_url}
cd {repo_name}
echo "cd {repo_name}"
git checkout {git_hash}
echo "git checkout {git_hash}"
git branch
'''.format(repo_name=repoName, git_url=git_url, git_hash=gitHash, workspace=workDir)

  with open("{}/git_checkout.sh".format(workDir), "w+") as f:
    f.writelines(lines)
    
  process = subprocess.Popen(["bash", "{}/git_checkout.sh".format(work_dir)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  sys.stdout.write(process.communicate()[0])
  
  if process.returncode != 0:
    clean_up(workDir)
    raise Exception("git clone step returns with error.")

# COMMAND ----------

def clone_and_checkoutbranch(repoName: str, gitHash: str, workDir: str, gitUser: str, gitToken: str, userName, userEmail):
  branches = [br.strip() for br in gitHash.split("=>")]
  git_url = create_git_clone_url(repoName, gitUser, gitToken)
  lines = '''
#!/bin/bash
set -e

git config --global user.name "{userName}"
git config --global user.email "{userEmail}"
mkdir -p {workspace} && cd {workspace}
if [ -d ./{repo_name} ]; then
  rm -rf ./{repo_name}
fi
echo "git clone from {git_url}"
git clone {git_url}
cd {repo_name}
echo "cd {repo_name}"
echo "git checkout {git_hash}"
git checkout {git_hash}
echo "git pull"
git pull
echo "checkout {new_branch}"
if [[ ! -z "{new_branch}" ]]; then
  echo "new branch {new_branch}"
  branchfound=$(git branch --all | grep -i {new_branch} |wc -l)
  echo "branch found: $branchfound"
  if [[ "$branchfound" == 0 ]]; then
    echo "there is a new branch to create {new_branch}"
    git checkout -b {new_branch}
  else
    echo "branch {new_branch} exists"
    git checkout {new_branch}
    echo "git merge -m 'updates from {git_hash}' {git_hash}"
    git merge -m "updates from {git_hash}" {git_hash} 
  fi
fi
git branch
'''.format(repo_name=repoName, git_url=git_url, git_hash=branches[0], 
           new_branch=branches[1] if len(branches)>1 else "", workspace=workDir, userName=userName, userEmail=userEmail)

  with open("{}/git_checkout.sh".format(workDir), "w+") as f:
    f.writelines(lines)
    
  process = subprocess.Popen(["bash", "{}/git_checkout.sh".format(work_dir)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  sys.stdout.write(process.communicate()[0])
  
  if process.returncode != 0:
    #clean_up(workDir)
    raise Exception("git clone step returns with error.")

# COMMAND ----------

def find_job_by_name(jobs, name):
  ls = list(filter(lambda job: job['settings']['name'] == name, jobs))
  return True if len(ls) > 0 else False

# COMMAND ----------

def export_notebooks(sourceDir: str, workDir: str):
  TOKEN = dbutils.entry_point.getDbutils().notebook().getContext().apiToken().get()
  HOST = dbutils.entry_point.getDbutils().notebook().getContext().apiUrl().get()

  client = ApiClient(token = TOKEN, host = HOST, verify = False)
  ws = WorkspaceApi(client)
  ws.export_workspace_dir(sourceDir, workDir, overwrite=True)

# COMMAND ----------

def commit_and_push(repoName, branch, workDir, commitComments: str, userName, userEmail):
#   cxt = json.loads(dbutils.notebook.entry_point.getDbutils().notebook().getContext().toJson())
#   user_name = cxt["tags"]["user"]
  branches = [br.strip() for br in branch.split("=>")]
  cur_branch = branches[1] if len(branches)>1 else branches[0]
  lines = f'''
#!/bin/bash
set -e
git config --global user.name "{userName}"
git config --global user.email "{userEmail}"
cd {workDir}/{repoName}
echo "git add -A && git commit -m '{commitComments}'"
git add -A && git commit -m "{commitComments}"
echo "git push -u origin {cur_branch}"
git push -u origin {cur_branch}
'''

  with open("{}/git_commit.sh".format(workDir), "w+") as f:
    f.writelines(lines)
    
  process = subprocess.Popen(["bash", "{}/git_commit.sh".format(workDir)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  sys.stdout.write(process.communicate()[0])

# COMMAND ----------

def create_cluster_settings(minWorkers: int=2, maxWorkers: int=8, nodeType: str="i3.2xlarge"):
  return {
    "autoscale": {
        "min_workers": minWorkers,
        "max_workers": maxWorkers
    },
    "cluster_name": "",
    "spark_version": "9.1.x-scala2.12",
    "spark_conf": {},
    "aws_attributes": {
        "first_on_demand": 1,
        "availability": "SPOT_WITH_FALLBACK",
        "zone_id": "us-east-1c",
        "spot_bid_price_percent": 100,
        "ebs_volume_count": 0
    },
    "node_type_id": nodeType,
    "ssh_public_keys": [],
    "custom_tags": {},
    "spark_env_vars": {
        "PYSPARK_PYTHON": "/databricks/python3/bin/python3"
    },
    "enable_elastic_disk": False,
    "cluster_source": "JOB",
    "init_scripts": []
  }

# COMMAND ----------

def remove_cluster_conf(jobTaskConf):
  if "existing_cluster_id" in jobTaskConf:
    del jobTaskConf["existing_cluster_id"]
  if "new_cluster" in jobTaskConf:
    del jobTaskConf["new_cluster"]

# COMMAND ----------

def inject_cluster_conf(jobConf, clusterConf):
  if "tasks" in jobConf and len(jobConf["tasks"]) > 0:
    for task_conf in jobConf["tasks"]:
      remove_cluster_conf(task_conf)
      task_conf[list(clusterConf.keys())[0]] = list(clusterConf.values())[0]
  else:
    remove_cluster_conf(jobConf)
    jobConf[list(clusterConf.keys())[0]] = list(clusterConf.values())[0]
  return jobConf

# COMMAND ----------

