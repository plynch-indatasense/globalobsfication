## get a list of all AWS regions
import boto3
session = boto3.session.Session()
ec2_client = session.client(service_name="ec2", region_name="us-east-1")
# all_regions = ec2_client.describe_regions()
# list_of_regions = []
for each_region in all_regions['Regions']:
    list_of_regions.append(each_region['RegionName'])
print(list_of_regions)

## deploy a VPC with a different single subnet in each region and an internet gateway
for each_region in list_of_regions:
    ec2_client = session.client(service_name="ec2", region_name=each_region)
    vpc = ec2_client.create_vpc(CidrBlock='10.0.0.0/16')
    vpc_id = vpc['Vpc']['VpcId']
    subnet = ec2_client.create_subnet(CidrBlock='10.0.1.0/24', VpcId=vpc_id)
    subnet_id = subnet['Subnet']['SubnetId']
    igw = ec2_client.create_internet_gateway()
    igw_id = igw['InternetGateway']['InternetGatewayId']
    ec2_client.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
    route_table = ec2_client.create_route_table(VpcId=vpc_id)
    route_table_id = route_table['RouteTable']['RouteTableId']
    ec2_client.create_route(DestinationCidrBlock='0.0.0.0/0', GatewayId=igw_id, RouteTableId=route_table_id)
    ec2_client.associate_route_table(RouteTableId=route_table_id, SubnetId=subnet_id)
    print(f"VPC {vpc_id} created in {each_region} with subnet {subnet_id} and internet gateway {igw_id}")

## deploy a security group in each region with a single inbound rule for SSH
for each_region in list_of_regions:
    ec2_client = session.client(service_name="ec2", region_name=each_region)
    vpc_response = ec2_client.describe_vpcs()
    vpc_id = vpc_response['Vpcs'][0]['VpcId']
    security_group = ec2_client.create_security_group(GroupName='SSH', Description='SSH access', VpcId=vpc_id)
    security_group_id = security_group['GroupId']
    ec2_client.authorize_security_group_ingress(GroupId=security_group_id, IpProtocol='tcp', CidrIp='0.0.0.0/0', FromPort=22, ToPort=22)
    print(f"Security group {security_group_id} created in {each_region} for VPC {vpc_id}")

## deploy an EC2 instance in each region with a single tag
for each_region in list_of_regions:
    ec2_client = session.client(service_name="ec2", region_name=each_region)
    vpc_response = ec2_client.describe_vpcs()
    vpc_id = vpc_response['Vpcs'][0]['VpcId']
    subnet_response = ec2_client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    subnet_id = subnet_response['Subnets'][0]['SubnetId']
    instance = ec2_client.run_instances(ImageId='XXXXXXXXXXXXXXXXXXXXX', InstanceType='t2.micro', MaxCount=1, MinCount=1, SubnetId=subnet_id, SecurityGroupIds=[security_group_id])
    instance_id = instance['Instances'][0]['InstanceId']
    ec2_client.create_tags(Resources=[instance_id], Tags=[{'Key': 'Name', 'Value': 'StandupEC2'}])
    print(f"EC2 instance {instance_id} created in {each_region} with subnet {subnet_id} and security group {security_group_id}")

