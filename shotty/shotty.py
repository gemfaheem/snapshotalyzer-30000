import boto3
import botocore
import click

def initiate_session(profile):
    session = boto3.Session(profile_name = profile)
    ec2 = session.resource('ec2')
    return ec2

def filter_instances(ec2, project, instance):
    instances = []

    instances = ec2.instances.all()
    if project:
        filters = [{'Name':'tag:Project','Values':[project]}]
        instances = instances.filter(Filters=filters)
    if instance:
        filters = [{'Name':'instance-id','Values':[instance]}]
        instances = instances.filter(Filters=filters)

    return instances

def is_instance_running(i):
    if i.state['Name'] == 'running':
        return True
    else:
        return False

def filter_running_instances(ec2, project, instanace):
    instances = filter_instances(ec2, project, instanace)
    filters = [{'Name':'instance-state-name','Values':['running']}]
    instances = instances.filter(Filters=filters)

    return instances

def has_pending_snapshot(volume):
    snapshots = list(volume.snapshots.all())
    return snapshots and snapshots[0].state == 'pending'

@click.group()
@click.option('--profile', default = 'shotty', help = 'Profile name to instantiate a session')
@click.pass_context
def cli(ctx, profile):
	"""establish session params"""
	ctx.ensure_object(dict)
	ctx.obj['PROFILE'] = profile
	#ctx.obj['REGION'] = region


# def cli(profile):
#     """Shotty manages snapshots"""
    #initiate_session(profile)

@cli.group('snapshots')
def snapshots():
    """Commands for snapshots"""

@snapshots.command('list')
@click.option('--project', default = None, help = 'Only snapshots for project (tag Project:<name>)')
@click.option('--instance', default = None, help = 'Only list snapshots for instance provided')
@click.option('--all', 'list_all',default = False, is_flag=True, help = 'List all snapshots for each volume and not just the most recent')
@click.pass_context
def list_snapshots(ctx, project, instance, list_all):
    "List EC2 volumes snapshots"
    ec2 = initiate_session(ctx.obj['PROFILE'])
    instances = filter_instances(ec2, project, instance)

    for i in instances:
        for v in i.volumes.all():
            for s in v.snapshots.all():
                print (', '.join((
                    s.id,
                    v.id,
                    i.id,
                    s.state,
                    s.progress,
                    s.start_time.strftime("%c")
                )))

                if s.state == 'completed' and not list_all: break
    return


@cli.group('volumes')
def volumes():
    """Commands for volumes"""

@volumes.command('list')
@click.option('--project', default = None, help = 'Only volumes for project (tag Project:<name>)')
@click.option('--instance', default = None, help = 'Only volumes for instance provided.')
@click.pass_context
def list_volumes(ctx, project, instance):
    "List EC2 volumes"

    ec2 = initiate_session(ctx.obj['PROFILE'])
    instances = filter_instances(ec2, project, instance)

    for i in instances:
        for v in i.volumes.all():
            print (', '.join((
                v.id,
                i.id,
                v.state,
                str(v.size) + "GiB",
                v.encrypted and "Encrypted" or "Not Encrypted"
            )))
    return


@cli.group('instances')
def instances():
    """Commands for instances"""

@instances.command('snapshot', help="Create snapshots of all volumes")
@click.option('--project', default = None, help = 'Only instances for project (tag Project:<name>)')
@click.option('--instance', default = None, help = 'Only snapshots for instance provided')
@click.option('--force', 'force_snapshot',default = False, is_flag=True, help = 'Create instance volume snapshot only when used with --force option')
@click.pass_context
def create_snapshot(ctx, project, instance, force_snapshot):
    "Create snapshots for EC2 instances"

    ec2 = initiate_session(ctx.obj['PROFILE'])
    instances = filter_instances(ec2, project, instance)
    #r_instances = filter_running_instances(ec2, project, instance)

    if force_snapshot:
        for i in instances:

            isinstrunning = is_instance_running(i)

            print("Stopping {0} ...".format(i.id))
            i.stop()
            i.wait_until_stopped()

            for v in i.volumes.all():
                if has_pending_snapshot(v):
                    print("     Skipping {0}, snapshot already in progress".format(v.id))
                    continue
                try:
                    print("    Creating snapshot of {0}".format(v.id))
                    v.create_snapshot(Description="Created by SnapshotAlyzer 30000")
                except  botocore.exceptions.ClientError as e:
                    print("Problem occured while creating snapshot for volume {0}. ".format(v.id) + str(e))
                    continue

                if (isinstrunning):
                    print("Starting {0} ...".format(i.id))

                    i.start()
                    i.wait_until_running()

                    print("Job done!")

    else:
        print("Snapshot creation declined. Use --force to create snapshot")
        print("Job declined!")
    return


@instances.command('list')
@click.option('--project', default = None, help = 'Only instances for project (tag Project:<name>)')
@click.option('--instance', default = None, help = 'Describes instance details')
@click.pass_context
def list_instances(ctx, project, instance):
    "List EC2 instances"

    ec2 = initiate_session(ctx.obj['PROFILE'])
    instances = filter_instances(ec2, project, instance)

    for i in instances:
        tags = {t['Key']: t['Value'] for t in i.tags or []}
        print(', '.join((
        i.id,
        i.instance_type,
        i.placement['AvailabilityZone'],
        i.state['Name'],
        i.public_dns_name,
        tags.get('Project', '<no project>'))))
    return

@instances.command('stop')
@click.option('--project', default = None, help = 'Only instances for project (tag Project:<name>)')
@click.option('--instance', default = None, help = 'Stop only instance provided')
@click.option('--force', 'force_stop',default = False, is_flag=True, help = 'Stop instances only when used with --force option')
@click.pass_context
def stop_instances(ctx, project, instance, force_stop):
    "Stop EC2 instances"

    ec2 = initiate_session(ctx.obj['PROFILE'])
    instances = filter_instances(ec2, project, instance)

    for i in instances:

        try:
            if force_stop:
                print("Stopping {0}...".format(i.id))
                i.stop()
            else:
                print("Stopping {0} declined. Use --force to stop".format(i.id))

        except botocore.exceptions.ClientError as e:
            print("Could not stop {0}. ".format(i.id) + str(e))
            continue

    return

@instances.command('start')
@click.option('--project', default = None, help = 'Only instances for project (tag Project:<name>)')
@click.option('--instance', default = None, help = 'Start only instance provided')
@click.option('--force', 'force_start',default = False, is_flag=True, help = 'Start instances only when used with --force option')
@click.pass_context
def start_instances(ctx, project, instance, force_start):
    "Start EC2 instances"

    ec2 = initiate_session(ctx.obj['PROFILE'])
    instances = filter_instances(ec2, project, instance)

    for i in instances:
        try:
            if force_start:
                print("Starting {0}...".format(i.id))
                i.start()
            else:
                print("Starting {0} declined. Use --force to stop".format(i.id))
        except botocore.exceptions.ClientError as e:
            print("Could not start {0}. ".format(i.id) + str(e))
            continue

    return

@instances.command('reboot')
@click.option('--project', default = None, help = 'Only instances for project (tag Project:<name>)')
@click.option('--instance', default = None, help = 'Reboot only for instance provided')
@click.option('--force', 'force_reboot',default = False, is_flag=True, help = 'Reboot instances only when used with --force option')
@click.pass_context
def reboot_instances(ctx, project, instance, force_reboot):
    "Reboot EC2 instances"

    ec2 = initiate_session(ctx.obj['PROFILE'])
    instances = filter_instances(ec2, project, instance)

    for i in instances:
        try:
            if force_reboot:
                print("Rebooting {0}...".format(i.id))
                i.reboot()
            else:
                print("Rebooting {0} declined. Use --force to stop".format(i.id))
        except botocore.exceptions.ClientError as e:
            print("Could not reboot {0}. ".format(i.id) + str(e))
            continue

    return

if __name__ == '__main__':
    cli(obj={})

    #print("Hello, world!")
