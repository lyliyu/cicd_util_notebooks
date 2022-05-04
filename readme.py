# Databricks notebook source
# MAGIC %md ### Overview

# COMMAND ----------

# MAGIC %md In this framework, there are three simple notebooks to perform CI/CD tasks from within Databrick workspace:
# MAGIC 
# MAGIC * checkout_notebooks
# MAGIC * commit_notebooks
# MAGIC * deploy_pipeline

# COMMAND ----------

# MAGIC %md The **checkout_notebooks** and **commit_notebooks** help developers check out and commit code changes without having to use git commands. However, they do NOT support the concurrent code development in the same folder. If you have multiple developers working on the same folder, you will need to sync changes using git commands or Databricks git integration.

# COMMAND ----------

# MAGIC %md The **checkout_notebooks** checks out code from the specified git repo and branch to a randomized local tmp folder. Then it will import the code/notebooks to the specified target directory in a Databricks workspace. 
# MAGIC 
# MAGIC Please note, if you already have code changes in the target directory, you can check out changes and sync with your target directory, if the changes are in different folders. You cannot update the notebooks in the same directory, if the notebooks are changes from both Github and your workspace.

# COMMAND ----------

# MAGIC %md The **commit_notebooks** exports notebooks from the specified workspace directory (source), and checks them into the specified Github branch. If the branch is named as "master=>branch1", the **commit_notebooks** will merge the updates from the master branch to branch1. Then it will apply the notebooks in your source directory to branch1. Lastly, it will push the branch to the Git repo.
# MAGIC 
# MAGIC Please note, the code merge only works on folder level. If there are changes from both master branch and the workspace directory within the same directory, you will need to do this using git commands or Github integration.

# COMMAND ----------

# MAGIC %md The **deploy_pipeline** checks out code using git hash and a sub-directory and deploy the notebooks to the target directory in workspace. Jobs will be created if job definitions are specified at deploy/jobs. The notebook locations and cluster information can be overriden by the devops who perform the deployment.
# MAGIC 
# MAGIC There will be one **deploy_pipeline** for each repo. The project directories under the repo will be speicified as a parameter to the pipeline.

# COMMAND ----------

# MAGIC %md **Please note** that to use the notebooks, you will need to clone your own notebooks and change the github user and token as the first step.

# COMMAND ----------

# MAGIC %md ### New Feature Development

# COMMAND ----------

# MAGIC %md #### Import the directory from Git repo to workspace
# MAGIC 
# MAGIC When to develop new features, a new feature branch will need to be created from master branch.
# MAGIC 
# MAGIC The notebook code will be checked out from the master branch and imported to a workspace(target) directory using the **checkout_notebooks**.
# MAGIC 
# MAGIC Parameters:
# MAGIC * *Repo:Branch* defines github repo and the master branch the feature branch is based off. e.g. dbis-databricks-devops: ci-pipeline
# MAGIC * *Project Directory* defines the poject directory within the repo. e.g. Workspace/globali590. This can even be a subfolder of Workspace/globali590 if you only need to work on that specific subfolder.
# MAGIC * *Target Directory* defines the target directeory in Databricks workspace the notebooks/folders will be imported to.

# COMMAND ----------

# MAGIC %md #### Create the new feature branch and commit the changes to the branch 
# MAGIC 
# MAGIC Now you have up-to-date notebook from ci-pipeline (master) branch. You can start develop on your notebooks in the target directory.
# MAGIC 
# MAGIC When you are done, you will need to commit your notebooks to a new feature branch (e.g. branch1).
# MAGIC 
# MAGIC To do this, you will need to use **commit_notebooks**
# MAGIC 
# MAGIC Parameters:
# MAGIC * *Repo:Branch* defines github repo and the feature branch. You can merge new changes from the master branch in the same process. e.g. dbis-databricks-devops: ci-pipeline => branch1
# MAGIC This means that new changes will be merged from the ci-pipeline branch to branch1 before applying changes from the notebooks. Branch1 will be created if it is new.
# MAGIC 
# MAGIC * *Source Directory* defines the workspace directory where the notebooks you have been workin on. The notebooks/folders in this directory will be committed to Github
# MAGIC * *Project Directory* defines the poject directory within the repo. e.g. Workspace/globali590. This can even be a subfolder of Workspace/globali590 if you only need to work on that specific subfolder. Your notebook changes will be commited to this directory.
# MAGIC * *Comment* defines the comment for the commit

# COMMAND ----------

# MAGIC %md #### Create a PR
# MAGIC When you created the new feature branch and commit your changes, you can keep using the parameters above to commit new changes to the created feature branch.
# MAGIC 
# MAGIC When you are done with development, you can create a Pull Request on Github to merge your new feature branch to master.
# MAGIC 
# MAGIC When the code review is done, admin will merge your PR to the master branch.

# COMMAND ----------

# MAGIC %md ### Job Definitions
# MAGIC 
# MAGIC The jobs can be defined from UI and then export to JSON. The JSON code under settings will be copied to pasted to deploy/jobs
# MAGIC 
# MAGIC This is an example of deploy/job
# MAGIC 
# MAGIC ```
# MAGIC driver_job = {
# MAGIC         "email_notifications": {},
# MAGIC         "name": "Job_c3lan_data_quality",
# MAGIC         "max_concurrent_runs": 1,
# MAGIC         "tasks": [
# MAGIC             {
# MAGIC                 "existing_cluster_id": "{{cluster_id}}",
# MAGIC                 "notebook_task": {
# MAGIC                     "notebook_path": "{{target_dir}}/drivers/rawLayer/checkDriverRaw",
# MAGIC                     "base_parameters": {
# MAGIC                         "wQualityCheckSite": "nsc"
# MAGIC                     }
# MAGIC                 },
# MAGIC                 "email_notifications": {},
# MAGIC                 "task_key": "Task_c3lan_nsc_data_quality"
# MAGIC             }
# MAGIC         ]
# MAGIC }
# MAGIC  
# MAGIC jobs = [driver_job]
# MAGIC 
# MAGIC import json
# MAGIC 
# MAGIC dbutils.notebook.exit(json.dumps({
# MAGIC   "Status": "OK",
# MAGIC   "jobs": jobs
# MAGIC }))
# MAGIC ```

# COMMAND ----------

# MAGIC %md In the example above, the `{{target_dir}}` will be replaced with the parameter defined in your deploy_pipeline notebook. The cluster settings will be replaced by cluster_conf defined in your deploy_pipeline during deployment.

# COMMAND ----------

# MAGIC %md ### Deployment
# MAGIC 
# MAGIC The **deploy_pipeline** will deploy your notebooks and jobs to staging or prod environments.
# MAGIC 
# MAGIC As a developer, you can run your own **deploy_pipeline** notebook for testing purpose on staging env. However only admins and devops will be able to run the pipelin in prod.
# MAGIC 
# MAGIC The parameters you will need to change for every run are:
# MAGIC * *Git Hash*: the code version to deploy
# MAGIC * *Project Directory: the subfolder under workspace target directory for the whole repo. e.g. Workspace/globali590
# MAGIC 
# MAGIC The parameters you will need to only set up once in the notebook:
# MAGIC 
# MAGIC `target_root = "/DBIS_ADMIN_AREA/CON1/CON1(ECC3LAN - DataQuality)" # the workspace directory for the whole repo`
# MAGIC `target_proj_dir = proj_dir #change this if the sub directory (proj_dir) in github is different from deployment target directory`
# MAGIC `job_params = {
# MAGIC   "target_dir": os.path.join(target_root, target_proj_dir) # this is going to replace the notebook location in the job definition
# MAGIC }`
# MAGIC `cluster_conf = {"existing_cluster_id": "1113-180731-purrs217"}`
# MAGIC `# cluster_conf = {"new_cluster": create_cluster_settings()}`

# COMMAND ----------

