# Azure Python SDK samples
### to run:
#### Step 1: Authentication

az login

az ad sp create-for-rbac --name "mbservprin1”

Export values (can use setx for windows command prompt):

export AZURE_TENANT_ID="bae50a1b-a7f-xxxxx"

export AZURE_CLIENT_ID="e1156021-c619-xxxx-b6e5-xxxxxxx"

export AZURE_CLIENT_SECRET="Pe41dqZn+37VN-xxxxxxxxxxxx"

export AZURE_SUBSCRIPTION_ID="cc71f0b1-6fa4-408c-xxxxxxxxxxx"



#### Step2:
`$ pip install -r requirements.txt`

`$ python createWindowsVM.py`
