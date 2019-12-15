# Proof of Concept for mocking resource data into Capital One Cloud Custodian.

The Cloud Custodian policy language can be hard to understand.
Also, finding resources that exist in AWS which match the policy, is also a challenge.
This PoC mocks the JSON data that the AWS would return, 
and inserts directly into the `.cache` file that Cloud Custodian uses.