# snapshotalyzer-30000
Demo project to manage AWS EC2 instance snapshots

## About

This project is a demo, and uses boto3 to manage AWS EC2 instance snapshots.

## Configuring

shotty uses configuration file created by the AWS CLI e.g.

`aws configure --profile shotty`

## Running

`pipenv run python "shotty/shotty.py <--profile=PROFILE_NAME> <command> <subcommand> <--project=PROJECT>"`

*profile* aws profile under which we wish to run the commands
*command* is instances, volumes, or snapshots
*subcommand* depends on commands
*project* is optional
