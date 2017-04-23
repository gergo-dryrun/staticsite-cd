# Quickstart Hosting Static Site on AWS Part 2: CI/CD
###### Cloudformation stack suite to deploy AWS CodePipeline setup for static sites


This project includes a master CloudFormation template that bundles up independent stacks:

 * Service roles needed by CodePipeline CodeBuild and custom AWS Lambda function
 * CodePipeline setup with github commit trigger, CodeBuild and custom AWS Lambda publishing artifacts to s3.

#### Prerequisites

* You will need to have the infrastructure boilerplate configured as described in [Part 1](https://dryrun.cloud/2017/quickstart-hosting-static-site-on-aws-part-1-infrastructure/)
* Valid `buildspec.yaml` inside your staticsite github repository. See [jekyll sample](#buildspec)

#### Setup
You can get started by deploying the stack.

[<img src="https://s3-eu-west-1.amazonaws.com/quickstart-cloudtrail-to-elasticsearch/cloudformation-launch-stack.png">](https://console.aws.amazon.com/cloudformation/home?#/stacks/new?stackName=staticsite-cd&templateURL=https://s3-eu-west-1.amazonaws.com/dryrun.cloud-resources/2017-04-23-getting-started-static-sites-cd/template/master.template)

![Master parameters](https://s3-eu-west-1.amazonaws.com/dryrun.cloud-resources/2017-04-23-getting-started-static-sites-cd/screenshots/staticsite-cd-master-parameters.png)

If you are not a big fan of launching stacks from the console, you can clone this repo and the `Makefile` should provide you with what you need. I recommend keeping the parameters somewhere secure due to the sensitive nature of the github token.

```bash
# To create stack
make STACK_NAME=staticsite-cd STACK=master PARAM_PATH=`pwd`/parameters REGION=us-west-1 create
# To poll for events
make STACK_NAME=staticsite-cd STACK=master REGION=us-east-1 watch
# To see the stack outputs
make STACK_NAME=staticsite-cd STACK=master REGION=us-east-1 output
# To update the stack
make STACK_NAME=staticsite-cd STACK=master PARAM_PATH=`pwd`/parameters REGION=us-east-1 update
# To delete the stack
make STACK_NAME=staticsite-cd REGION=us-east-1 delete
```

The master stack will create 2 stacks.

* `pipeline-roles.template` contains the minimum set of roles needed by AWS Services to do the work on your behalf. Soon enough we'll have [service linked roles](https://aws.amazon.com/blogs/security/introducing-an-easier-way-to-delegate-permissions-to-aws-services-service-linked-roles/) for every AWS Service, which should greatly simplify or maybe even eliminate this template.
* `pipeline.template` contains the CodePipeline definition and custom lambda function for publishing files to s3.

### CodePipeline configuration

![CodePipeline](https://s3-eu-west-1.amazonaws.com/dryrun.cloud-resources/2017-04-23-getting-started-static-sites-cd/screenshots/code-pipeline.png)

There are 3 mandatory stages:

* **Source**
* **Build**
* **Production**

If you opted for staging environment you will get another stage in between **Build** and **Production**, called **Staging** (I know, very inspired naming)

The **Source** stage is configured with your github repo token and every time you do a commit, the hook will trigger the pipeline.

 <a name="buildspec"></a> The **Build** stage uses CodeBuild to execute the commands defined in your `buildspec.yml`. It expects to find a `buildspec.yml` file at the root of the project.

```yaml
version: 0.0
containers:
    LambdaFunctions:
        phases:
            during_build:
                commands:
                    - gem install jekyll
                    - jekyll build
        artifacts:
            files:
                - _site/**/*
```

The **Staging** stage will invoke a lambda function, passing in the `_site.zip` artifact and s3 destination. The lambda unpacks the artifact and does an `aws s3 sync` with the staging bucket.

There's an additional `Manual Approval` step, which uses SNS to send an e-mail containing a hyperlink to the environment and awaits user response. This should be an IP whitelisted environment where you can validate that the site looks and behaves as you expect it to.

![Manual Approval](https://s3-eu-west-1.amazonaws.com/dryrun.cloud-resources/2017-04-23-getting-started-static-sites-cd/screenshots/approval-mail.png)

You can `Reject` or `Approve` the changes, leaving a comment justifying the action.

If approved, the **Production** stage will invoke the same lambda but this time with the production bucket as destination.

And Voilà!, your latest changes are live and the best part of it is that everything is automated, no more worrying about aws credentials and syncing up folders. Long live CodePipeline!

#### Tips & gotchas
Current setup expects that the result of your static site build process defined in [buildspec](#buildspec) generates a `_site` directory.

Depending on which jekyll template you use, the buildspec `commands` might also differ slightly, just use the ones that work on your local machine.

[Boto3 still does not](https://github.com/boto/boto3/issues/358) have an equivalent of `aws s3 sync`. Luckily I already faced the challenge of porting [awscli to lambda](https://github.com/gergo-debreczeni/alfredbot/blob/master/alfred/alfred.py#L63), so that came in handy.

***

 [1] <http://docs.aws.amazon.com/codepipeline/latest/userguide/reference-pipeline-structure.html>

 [2] <http://docs.aws.amazon.com/codepipeline/latest/userguide/actions-invoke-lambda-function.html>

 [3] <http://docs.aws.amazon.com/codepipeline/latest/userguide/approvals-action-add.html>
