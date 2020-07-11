from setuptools import setup

setup(
    name = 'snapshotanalyzer_30000',
    version = '0.3',
    author = 'Faheem Ahmed Khan',
    author_email = 'gemfaheem.khan@gmail.com',
    description = 'SnapshotAlyzer 30000 is a tool to manage AWS EC2 snapshots',
    license = 'GPLv3+',
    packages = ['shotty'],
    url = "https://github.com/gemfaheem/snapshotalyzer-30000",
    install_requires = [
        'click',
        'boto3'
    ],
    entry_points = '''
        [console_scripts]
        shotty=shotty.shotty:cli
    ''',
)
