#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""vagrant_run

Usage:
  vagrant_run run [options]
  vagrant_run ssh [options]
  vagrant_run destroy [options]
  vagrant_run exports [options]

Options:
  --aws-json <path>          Path to file defining AWS-related variables [default: aws.json].
  --aws-profile <path>       Path to file defining AWS-related variables [default: jhu_ue1].
  --skip-slack               Don't send message to Slack.
  --no-destroy-on-error      Keep instance running on error.
  --no-creds-file            Don't pass AWS credentials file to EC2 host.
  --slack-ini <ini>          ini file for Slack webhooks [default: ~/.k2bench/slack.ini].
  --slack-section <section>  ini file load_aws_json()section for log aggregator [default: slack].
  -a, --aggregate            Enable log aggregation.
  -h, --help                 Show this screen.
  --debug                    Show debug information.
  --version                  Show version.
"""

""" ~/.k2bench/slack.ini file should look like this:
[slack]
tstring=TXXXXXXXX
bstring=BXXXXXXXX
secret=XXXXXXXXXXXXXXXXXXXXXXXX
"""

import os
import sys
import requests
import json
from docopt import docopt
try:
    from configparser import RawConfigParser
except ImportError:
    from ConfigParser import RawConfigParser
    sys.exc_clear()


def slack_webhook_url(ini_fn, section='slack'):
    tstring, bstring, secret = read_slack_config(ini_fn, section=section)
    return 'https://hooks.slack.com/services/%s/%s/%s' % (tstring, bstring, secret)


def read_slack_config(ini_fn, section='slack'):
    cfg = RawConfigParser()
    cfg.read(ini_fn)
    if section not in cfg.sections():
        raise RuntimeError('No [%s] section in log ini file "%s"' % (section, ini_fn))
    tstring, bstring, secret = cfg.get(section, 'tstring'), cfg.get(section, 'bstring'), cfg.get(section, 'secret')
    return tstring, bstring, secret


def load_aws_json(json_fn, profile):
    js = json.loads(open(json_fn, 'rt').read())
    if profile not in js['profile']:
        raise RuntimeError('No such profile as "%s" in AWS config "%s"' % (profile, json_fn))
    app = js['application']
    js_prof = js['profile'][profile]
    region = js_prof['region']
    subnet = js_prof['subnet'][list(js_prof['subnet'].keys())[0]]
    security_group = js_prof['security_group']
    keypair = js_prof['keypair']
    bid_price = None
    inst = js['app']['instance_type']
    if 'bid_price' in js['ec2']['instance_type'][inst] and \
            region in js['ec2']['instance_type'][inst]['bid_price']:
        bid_price = js['ec2']['instance_type'][inst]['bid_price'][region]
    aws_profile = js_prof['profile']
    arch = js['ec2']['instance_type'][inst]['arch']
    ami = js['ec2']['ami'][region][arch]
    return app, region, subnet, security_group, ami, keypair, bid_price, inst, aws_profile


def print_exports(aws_json, profile):
    app, region, subnet, security_group, ami, keypair, bid_price, instance_type, aws_profile = \
        load_aws_json(aws_json, profile)
    h = {'VAGRANT_APPLICATION': app,
         'VAGRANT_AWS_PROFILE': aws_profile,
         'VAGRANT_AWS_REGION': region,
         'VAGRANT_AWS_SUBNET_ID': subnet,
         'VAGRANT_AWS_SECURITY_GROUP': security_group,
         'VAGRANT_AWS_AMI': ami,
         'VAGRANT_AWS_EC2_KEYPAIR': keypair,
         'VAGRANT_AWS_EC2_INSTANCE_TYPE': instance_type,
         'VAGRANT_AWS_EC2_BID_PRICE': bid_price}
    for k, v in sorted(h.items()):
        print('export %s=%s' % (k, v))


def run(command, skip_slack, ini_fn, section, aws_json, profile, no_destroy, no_make_creds, debug):
    if not os.path.exists(aws_json):
        raise RuntimeError('AWS json file "%s" does not exist' % aws_json)
    app, region, subnet, security_group, ami, keypair, bid_price, instance_type, aws_profile = \
        load_aws_json(aws_json, profile)
    creds_tmp_fn = 'creds_placeholder.txt'
    os.environ['VAGRANT_APPLICATION'] = app
    os.environ['VAGRANT_AWS_PROFILE'] = aws_profile
    os.environ['VAGRANT_AWS_REGION'] = region
    os.environ['VAGRANT_AWS_CREDS'] = creds_tmp_fn
    os.environ['VAGRANT_AWS_SUBNET_ID'] = subnet
    os.environ['VAGRANT_AWS_SECURITY_GROUP'] = security_group
    os.environ['VAGRANT_AWS_AMI'] = ami
    os.environ['VAGRANT_AWS_EC2_KEYPAIR'] = keypair
    os.environ['VAGRANT_AWS_EC2_INSTANCE_TYPE'] = instance_type
    os.environ['VAGRANT_AWS_EC2_BID_PRICE'] = bid_price
    slack_url = slack_webhook_url(ini_fn, section=section)
    vagrant_args = ''
    if no_destroy:
        vagrant_args += ' --no-destroy-on-error'
    if debug:
        vagrant_args += ' --debug'
    if command == 'run':
        if not no_make_creds:
            credential_fn = os.path.expanduser('~/.aws/credentials')
            if not os.path.exists(credential_fn):
                raise RuntimeError('No such credentials file "%s"' % credential_fn)
            with open(creds_tmp_fn, 'wt') as ofh:
                ofh.write('[default]\n')
                with open(credential_fn, 'rt') as fh:
                    while True:
                        ln = fh.readline()
                        if len(ln) == 0:
                            break
                        ln = ln.rstrip()
                        if ln == ('[%s]' % aws_profile):
                            tokens = fh.readline().rstrip().split('=')
                            ky, vl = tokens[0].strip(), tokens[1].strip()
                            assert ky == 'aws_access_key_id'
                            ofh.write('aws_access_key_id = %s\n' % vl)
                            tokens = fh.readline().rstrip().split('=')
                            ky, vl = tokens[0].strip(), tokens[1].strip()
                            assert ky == 'aws_secret_access_key'
                            ofh.write('aws_secret_access_key = %s\n' % vl)
        os.system('vagrant up %s 2>&1 | tee vagrant.log' % vagrant_args)
        with open(creds_tmp_fn, 'wt') as ofh:
            ofh.write('')
        attachments = []
        with open('vagrant.log', 'r') as fh:
            for ln in fh:
                if '===HAPPY' in ln:
                    st = ln[ln.find('===HAPPY') + 9:].rstrip()
                    attachments.append({'text': st, 'color': 'good'})
                elif '===SAD' in ln:
                    st = ln[ln.find('===SAD') + 7:].rstrip()
                    attachments.append({'text': st, 'color': 'danger'})
        if not skip_slack:
            name = 'no name'
            if os.path.exists('name.txt'):
                with open('name.txt', 'rt') as fh:
                    name = fh.read().strip()
            requests.put(slack_url, json={
                'username': 'webhookbot',
                'text': '%s:' % name,
                'attachments': attachments})
        if not no_destroy:
            os.system('vagrant destroy -f')
    elif command == 'ssh':
        os.system('vagrant ssh')
    elif command == 'destroy':
        os.system('vagrant destroy')
    else:
        raise ValueError('Unexpected command: "%s"' % command)


if __name__ == '__main__':
    args = docopt(__doc__)
    slack_ini = os.path.expanduser(args['--slack-ini'])
    if args['run']:
        run('run', args['--skip-slack'], slack_ini,
            args['--slack-section'], args['--aws-json'], args['--aws-profile'],
            args['--no-destroy-on-error'], args['--no-creds-file'],
            args['--debug'])
    elif args['ssh']:
        run('ssh', args['--skip-slack'], slack_ini,
            args['--slack-section'], args['--aws-json'], args['--aws-profile'],
            args['--no-destroy-on-error'], args['--no-creds-file'],
            args['--debug'])
    elif args['destroy']:
        run('destroy', args['--skip-slack'], slack_ini,
            args['--slack-section'], args['--aws-json'], args['--aws-profile'],
            args['--no-destroy-on-error'], args['--no-creds-file'],
            args['--debug'])
    elif args['exports']:
        print_exports(args['--aws-json'], args['--aws-profile'])
    else:
        raise ValueError('No such command')

