
# VPC

Amazon Virtual Private Cloud (Amazon VPC) enables you to launch AWS resources into a virtual network that you've defined. This virtual network closely resembles a traditional network that you'd operate in your own data center, with the benefits of using the scalable infrastructure of AWS.

## Input Parameters

| Variable | Description | Default Value | Data Type |
|---|---|---|---|
| pNumberOfAzs | How many AZs would you like to deploy? | 2 | Number
| pAz1 | Availability Zone 1. Don't leave it blank. | .+ | |
| pAz2 | Availability Zone 2. Don't leave it blank, even if you are only deploying in a single AZ. | .+ | |
| pSpecifyManualCidrs | Choosing false will automatically set the CIDRs incrementally. Choosing true will allow you to choose your own CIDRs below. | false | bool |
| pVpcCidrPrefix | Assumes /16 and sets public, private, and data subnet CIDRs incrementally. If specifying your own CIDRs, please enter the first two octets of your specified CIDR.  | 10.10 | String |
| pCreatePrivateSubnets | Should private subnets be created? | True | bool |
| pCreateDataSubnets | Should data subnets be created? | True| bool |
| pPublicSubnet1octet | Public Subnet 1 (_._.XX.0/24). First 2 octets taken from VPC CIDR Prefix above. Leave blank if not specifying manual CIDRs. | false | String |
| pPublicSubnet2octet | Public Subnet 2 (_._.XX.0/24). First 2 octets taken from VPC CIDR Prefix above. Leave blank if not specifying manual CIDRs. | false | String |
| pPrivateSubnet1octet | Private Subnet 1 (_._.XX.0/24). First 2 octets taken from VPC CIDR Prefix above. Leave blank if not specifying manual CIDRs. | false | String |
| pPrivateSubnet2octet | Private Subnet 2 (_._.XX.0/24). First 2 octets taken from VPC CIDR Prefix above. Leave blank if not specifying manual CIDRs. | false | String |
| pDataSubnet1octet | Data Subnet 1 (_._.XX.0/24). First 2 octets taken from VPC CIDR Prefix above. Leave blank if not specifying manual CIDRs. | false | String |
| pDataSubnet2octet | Data Subnet 2 (_._.XX.0/24). First 2 octets taken from VPC CIDR Prefix above. Leave blank if not specifying manual CIDRs.  | false| String |
| pCustomDomain | Custom Internal Domain for DHCP. AmazonProvidedDNS will be used as standby. | false | bool |
| pDhcpInternalDomain | Create KMS EBS Key? | | String |
| pDc01Ip | Domain Controller Private IP for DHCP Option Set | | String |
| pDc02Ip | Domain Controller Private IP for DHCP Option Set  | | String |
| pDc03Ip | Domain Controller Private IP for DHCP Option Set | | String |
| pFlowlogRetention | Days VPC Flowlogs are retained in CloudWatch. | 7 | Number |
| pS3VpcEndpoint | Enable VPC Endpoint S3. | true | bool |
| pEcrEndpoint | Enable VPC Endpoint ECR. | true | bool |
| pEnvironmentTag | Environment type for default resource tagging | development | String |

## Outputs

| Name                              | Description                           |
|-----------------------------------|---------------------------------------|
| Version | This Cloudformation template's version |
| vpcId | VPC ID |
| vpcCidr | VPC CIDR |
| pubSubnet01Id | Public Subnet 01 ID |
| pubSubnet02Id | Public Subnet 02 ID |
| privSubnet01Id | Private Subnet 01 ID |
| privSubnet02Id | Private Subnet 02 ID |
| privDataSubnet01Id| Private Data Subnet 01 ID |
| privDataSubnet02Id | Private Data Subnet 02 ID |
| routeTablePubSubnetAz01 | Public Subnet 01 Route Table ID |
| routeTablePubSubnetAz02 | Public Subnet 02 Route Table ID |
| routeTablePrivSubnetAz01| Private Subnet 01 Route Table ID |
| routeTablePrivSubnetAz02 | Private Subnet 02 Route Table ID |
| routeTablePrivDataSubnetAz01 | Private Data Subnet 01 Route Table ID |
| routeTablePrivDataSubnetAz02 | Private Data Subnet 02 Route Table ID |
| naclAssocPubSubnetAz01 | Public Subnet 01 NACL |
| naclAssocPubSubnetAz02 | Public Subnet 02 NACL |
| naclPrivSubnetAz01 | Private Subnet 01 NACL |
| naclPrivSubnetAz02 | Private Subnet 02 NACL |
| naclPrivDataSubnetAz01 | Private Data Subnet 01 NACL |
| naclPrivDataSubnetAz02 | Private Data Subnet 02 NACL |
