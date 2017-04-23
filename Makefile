TEMPLATE:=template/$(STACK).template
PARAMETERS:=$(PARAM_PATH)/$(STACK).json
AWS_REGION:=$(REGION)
AWS_PROFILE:=default

create:
	@which aws || pip install awscli
	aws cloudformation create-stack --stack-name $(STACK_NAME) --template-body file://`pwd`/$(TEMPLATE) --parameters file://$(PARAMETERS) --capabilities CAPABILITY_NAMED_IAM --profile $(AWS_PROFILE) --region $(AWS_REGION)

update:
	aws cloudformation update-stack --stack-name $(STACK_NAME) --template-body file://`pwd`/$(TEMPLATE) --parameters file://$(PARAMETERS) --capabilities CAPABILITY_NAMED_IAM --profile $(AWS_PROFILE) --region $(AWS_REGION)

events:
	aws cloudformation describe-stack-events --profile $(AWS_PROFILE) --region $(AWS_REGION) --stack-name $(STACK_NAME) --output text --query 'StackEvents[*].[ResourceStatus,LogicalResourceId,ResourceType,Timestamp]' | sort -k4r | column -t

watch:
	 watch --interval 2 "bash -c 'make events | head -25'"

output:
	@which jq || ( which brew && brew install jq || which apt-get && apt-get install jq || which yum && yum install jq || which choco && choco install jq)
	aws cloudformation describe-stacks --stack-name $(STACK_NAME) --profile $(AWS_PROFILE) --region $(AWS_REGION) | jq -r '.Stacks[].Outputs'

delete:
	aws cloudformation delete-stack --stack-name $(STACK_NAME) --profile $(AWS_PROFILE) --region $(AWS_REGION)
