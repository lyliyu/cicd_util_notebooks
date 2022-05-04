### Overview

In this framework, there are three simple notebooks to perform CI/CD tasks from within Databrick workspace:

* checkout_notebooks
* commit_notebooks
* deploy_pipeline

The **checkout_notebooks** and **commit_notebooks** help developers check out and commit code changes without having to use git commands. However, they do NOT support the concurrent code development in the same folder. If you have multiple developers working on the same folder, you will need to sync changes using git commands or Databricks git integration.

The **checkout_notebooks** checks out code from the specified git repo and branch to a randomized local tmp folder. Then it will import the code/notebooks to the specified target directory in a Databricks workspace. 

Please note, if you already have code changes in the target directory, you can check out changes and sync with your target directory, if the changes are in different folders. You cannot update the notebooks in the same directory, if the notebooks are changes from both Github and your workspace.

The **commit_notebooks** exports notebooks from the specified workspace directory (source), and checks them into the specified Github branch. If the branch is named as "master=>branch1", the **commit_notebooks** will merge the updates from the master branch to branch1. Then it will apply the notebooks in your source directory to branch1. Lastly, it will push the branch to the Git repo.

Please note, the code merge only works on folder level. If there are changes from both master branch and the workspace directory within the same directory, you will need to do this using git commands or Github integration.

The **deploy_pipeline** checks out code using git hash and a sub-directory and deploy the notebooks to the target directory in workspace. Jobs will be created if job definitions are specified at deploy/jobs. The notebook locations and cluster information can be overriden by the devops who perform the deployment.

There will be one **deploy_pipeline** for each repo. The project directories under the repo will be speicified as a parameter to the pipeline.

**Please note** that to use the notebooks, you will need to clone your own notebooks and change the github user and token as the first step.

### New Feature Development

#### Import the directory from Git repo to workspace

When to develop new features, a new feature branch will need to be created from master branch.

The notebook code will be checked out from the master branch and imported to a workspace(target) directory using the **checkout_notebooks**.

Parameters:
* *Repo:Branch* defines github repo and the master branch the feature branch is based off. e.g. dbis-databricks-devops: ci-pipeline
* *Project Directory* defines the poject directory within the repo. e.g. Workspace/globali590. This can even be a subfolder of Workspace/globali590 if you only need to work on that specific subfolder.
* *Target Directory* defines the target directeory in Databricks workspace the notebooks/folders will be imported to.

#### Create the new feature branch and commit the changes to the branch 

Now you have up-to-date notebook from ci-pipeline (master) branch. You can start develop on your notebooks in the target directory.

When you are done, you will need to commit your notebooks to a new feature branch (e.g. branch1).

To do this, you will need to use **commit_notebooks**

Parameters:
* *Repo:Branch* defines github repo and the feature branch. You can merge new changes from the master branch in the same process. e.g. dbis-databricks-devops: ci-pipeline => branch1
This means that new changes will be merged from the ci-pipeline branch to branch1 before applying changes from the notebooks. Branch1 will be created if it is new.

* *Source Directory* defines the workspace directory where the notebooks you have been workin on. The notebooks/folders in this directory will be committed to Github
* *Project Directory* defines the poject directory within the repo. e.g. Workspace/globali590. This can even be a subfolder of Workspace/globali590 if you only need to work on that specific subfolder. Your notebook changes will be commited to this directory.
* *Comment* defines the comment for the commit

#### Create a PR
When you created the new feature branch and commit your changes, you can keep using the parameters above to commit new changes to the created feature branch.

When you are done with development, you can create a Pull Request on Github to merge your new feature branch to master.

When the code review is done, admin will merge your PR to the master branch.

### Job Definitions

The jobs can be defined from UI and then export to JSON. The JSON code under settings will be copied to pasted to deploy/jobs

This is an example of deploy/job

```
driver_job = {
        "email_notifications": {},
        "name": "Job_c3lan_data_quality",
        "max_concurrent_runs": 1,
        "tasks": [
            {
                "existing_cluster_id": "{{cluster_id}}",
                "notebook_task": {
                    "notebook_path": "{{target_dir}}/drivers/rawLayer/checkDriverRaw",
                    "base_parameters": {
                        "wQualityCheckSite": "nsc"
                    }
                },
                "email_notifications": {},
                "task_key": "Task_c3lan_nsc_data_quality"
            }
        ]
}
 
jobs = [driver_job]

import json

dbutils.notebook.exit(json.dumps({
  "Status": "OK",
  "jobs": jobs
}))
```

In the example above, the `{{target_dir}}` will be replaced with the parameter defined in your deploy_pipeline notebook. The cluster settings will be replaced by cluster_conf defined in your deploy_pipeline during deployment.

### Deployment

The **deploy_pipeline** will deploy your notebooks and jobs to staging or prod environments.

As a developer, you can run your own **deploy_pipeline** notebook for testing purpose on staging env. However only admins and devops will be able to run the pipelin in prod.

The parameters you will need to change for every run are:
* *Git Hash*: the code version to deploy
* *Project Directory: the subfolder under workspace target directory for the whole repo. e.g. Workspace/globali590

The parameters you will need to only set up once in the notebook:

`target_root = "/DBIS_ADMIN_AREA/CON1/CON1(ECC3LAN - DataQuality)" # the workspace directory for the whole repo`
`target_proj_dir = proj_dir #change this if the sub directory (proj_dir) in github is different from deployment target directory`
`job_params = {
  "target_dir": os.path.join(target_root, target_proj_dir) # this is going to replace the notebook location in the job definition
}`
`cluster_conf = {"existing_cluster_id": "1113-180731-purrs217"}`
`# cluster_conf = {"new_cluster": create_cluster_settings()}`
