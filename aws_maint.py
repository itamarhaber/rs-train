import boto3

def vpc_cleanup(region, vpcid):
    """Remove VPC from AWS
    Set your region/access-key/secret-key from env variables or boto config.
    :param vpcid: id of vpc to delete
    """
    if not vpcid or not region:
        return
    print('Removing VPC ({}) from AWS {}'.format(vpcid, region))
    ec2 = boto3.resource('ec2', region_name=region)
    ec2client = ec2.meta.client
    vpc = ec2.Vpc(vpcid)
    # detach and delete all gateways associated with the vpc
    for gw in vpc.internet_gateways.all():
        vpc.detach_internet_gateway(InternetGatewayId=gw.id)
        gw.delete()
    # delete all route table associations
    for rt in vpc.route_tables.all():
        for rta in rt.associations:
            if not rta.main:
                rta.delete()
    # delete any instances
    for subnet in vpc.subnets.all():
        for instance in subnet.instances.all():
            instance.terminate()
    # delete our endpoints
    for ep in ec2client.describe_vpc_endpoints(
            Filters=[{
                'Name': 'vpc-id',
                'Values': [vpcid]
            }])['VpcEndpoints']:
        ec2client.delete_vpc_endpoints(VpcEndpointIds=[ep['VpcEndpointId']])
    # delete our security groups
    for sg in vpc.security_groups.all():
        if sg.group_name != 'default':
            sg.delete()
    # delete any vpc peering connections
    for vpcpeer in ec2client.describe_vpc_peering_connections(
            Filters=[{
                'Name': 'requester-vpc-info.vpc-id',
                'Values': [vpcid]
            }])['VpcPeeringConnections']:
        ec2.VpcPeeringConnection(vpcpeer['VpcPeeringConnectionId']).delete()
    # delete non-default network acls
    for netacl in vpc.network_acls.all():
        if not netacl.is_default:
            netacl.delete()
    # delete network interfaces
    for subnet in vpc.subnets.all():
        for interface in subnet.network_interfaces.all():
            interface.delete()
        subnet.delete()
    # finally, delete the vpc
    ec2client.delete_vpc(VpcId=vpcid)


def list_vpcs_in_all_regions():
  # Create a Boto3 session
  session = boto3.Session(profile_name='CTO_AdminAccess', region_name='us-east-1')

  # Get a list of all regions
  ec2_client = session.client('ec2')
  # regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]
  regions = ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2']

  # Iterate through each region and list VPCs
  for region in regions:
    print(f"Region: {region}")
    regional_ec2_client = session.client('ec2', region_name=region)
    regional_cf_client = session.client('cloudformation', region_name=region)

    # List all VPCs in the region
    try:
      vpcs = regional_ec2_client.describe_vpcs()
      for vpc in vpcs['Vpcs']:
        # Get vpc name tag if it exists
        if 'Name' not in vpc:
          vpc['Name'] = ''
        if vpc['Name'] == '' and 'Tags' in vpc:
          for tag in vpc['Tags']:
            if tag['Key'] == 'Name':
              vpc['Name'] = tag['Value']
    except Exception as e:
      print(f"  Error accessing region vpcs {region}: {e}")
    print(f"  VPC ID: {vpc['VpcId']}  Name: {vpc['Name']}")
    if vpc['Name'].find('teenage-teal-6xy0f') > -1:
      vpc_cleanup(region, vpc['VpcId'])

    try:
      # Get all cloudformation stacks in the region
      stacks = regional_cf_client.describe_stacks()
      for stack in stacks['Stacks']:
        print(f"  Stack: {stack['StackName']}")
    except Exception as e:
      print(f"  Error accessing region stacks {region}: {e}")
    if stack['StackName'].find('itamar') > -1:
      print(f"    Deleting stack {stack['StackName']}")
      regional_cf_client.delete_stack(StackName=stack['StackName'])

# Run the function
list_vpcs_in_all_regions()
