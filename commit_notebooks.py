# Databricks notebook source
# MAGIC %run ./deploy_utils

# COMMAND ----------

dbutils.widgets.removeAll()
dbutils.widgets.text("repo_branch", "", "Repo:Branch")
dbutils.widgets.text("proj_dir", "", "Project Directory")
dbutils.widgets.text("source_dir", "", "Source Directory")
dbutils.widgets.text("commit_comment", "", "Comment")

# COMMAND ----------

repo_branch = dbutils.widgets.get("repo_branch")
repo_name, branch_name = repo_branch.split(":")
repo_name = repo_name.strip()
branch_name = branch_name.strip()
proj_dir = dbutils.widgets.get("proj_dir").strip("/")
source_dir = dbutils.widgets.get("source_dir").rstrip("/")
commit_comment = dbutils.widgets.get("commit_comment")
print(f"commit notebooks from {source_dir} to {repo_name}: {branch_name}/{proj_dir}")

# COMMAND ----------

user_name = "lyu"
user_email = "li.yu@uscis.dhs.gov"
user_token = dbutils.secrets.get(scope = "deploy_scope", key = "git_token")

# repo_name = "data_quality_tool"
# branch_name =  "data_quality_impl" #"data_quality_impl => test_new_branch"
# proj_name = "other_proj"

# source_notebook_dir = "/DBIS_ADMIN_AREA/CON1/CON1(ECC3LAN - DataQuality)/dataQuality"
# source_notebook_dir = "/Users/lyu/dbis_projs_src/other_proj"
# commit_comment = "add more features"

# COMMAND ----------

work_dir = create_work_dir()

# COMMAND ----------

clone_and_checkoutbranch(repo_name, branch_name, work_dir, user_name, user_token, user_name, user_email)

# COMMAND ----------

export_notebooks(source_dir, os.path.join(work_dir, repo_name, proj_dir))

# COMMAND ----------

commit_and_push(repo_name, branch_name, work_dir, commit_comment, user_name, user_email)

# COMMAND ----------

