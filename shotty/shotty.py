import boto3
import botocore
import click

def initiate_session(profile):
    session = boto3.Session(profile_name = profile)
    ec2 = session.resource('ec2')
    return ec2

def filter_instances(ec2, project):
    instances = []

    if project:
        filters = [{'Name':'tag:Project','Values':[project]}]
        instances = ec2.instances.filter(Filters=filters)
    else:
        instances = ec2.instances.all()

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
@click.option('--all', 'list_all',default = False, is_flag=True, help = 'List all snapshots for each volume and not just the most recent')
@click.pass_context
def list_snapshots(ctx, project, list_all):
    "List EC2 volumes snapshots"
    ec2 = initiate_session(ctx.obj['PROFILE'])
    instances = filter_instances(ec2, project)

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
@click.pass_context
def list_volumes(ctx, project):
    "List EC2 volumes"

    ec2 = initiate_session(ctx.obj['PROFILE'])
    instances = filter_instances(ec2, project)

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
@click.option('--force', 'force_snapshot',default = False, is_flag=True, help = 'Create instance volume snapshot only when used with --force option')
@click.pass_context
def create_snapshot(ctx, project, force_snapshot):
    "Create snapshots for EC2 instances"

    ec2 = initiate_session(ctx.obj['PROFILE'])
    instances = filter_instances(ec2, project)

    for i in instances:
        if force_snapshot:
            print("Stopping {0} ...".format(i.id))
            i.stop()
            i.wait_until_stopped()

            for v in i.volumes.all():
                if has_pending_snapshot(v):
                    print("     Skipping {0}, snapshot already in progress".format(v.id))
                    continue
                print("    Creating snapshot of {0}".format(v.id))
                v.create_snapshot(Description="Created by SnapshotAlyzer 30000")

            print("Starting {0} ...".format(i.id))

            i.start()
            i.wait_until_running()

            print("Job done!")

        else:
            print("Snapshot of instance {0} volume declined. Use --force to create snapshot".format(i.id))
            print("Job declined!")

    return


@instances.command('list')
@click.option('--project', default = None, help = 'Only instances for project (tag Project:<name>)')
@click.pass_context
def list_instances(ctx,project):
    "List EC2 instances"

    ec2 = initiate_session(ctx.obj['PROFILE'])
    instances = filter_instances(ec2, project)

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
@click.option('--force', 'force_stop',default = False, is_flag=True, help = 'Stop instances only when used with --force option')
@click.pass_context
def stop_instances(ctx, project, force_stop):
    "Stop EC2 instances"

    ec2 = initiate_session(ctx.obj['PROFILE'])
    instances = filter_instances(ec2, project)

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
@click.option('--force', 'force_start',default = False, is_flag=True, help = 'Start instances only when used with --force option')
@click.pass_context
def start_instances(ctx, project, force_start):
    "Start EC2 instances"

    ec2 = initiate_session(ctx.obj['PROFILE'])
    instances = filter_instances(ec2, project)

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
@click.option('--force', 'force_reboot',default = False, is_flag=True, help = 'Reboot instances only when used with --force option')
@click.pass_context
def reboot_instances(ctx, project, force_reboot):
    "Reboot EC2 instances"

    ec2 = initiate_session(ctx.obj['PROFILE'])
    instances = filter_instances(ec2, project)

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
