import json
import operator
import os
import requests
from fabric.api import sudo, env, cd, put, roles

env.roledefs = {
    'web': ['quarry-main-01.eqiad.wmflabs'],
    'db': ['quarry-main-01.eqiad.wmflabs'],
    'runner': [
        'quarry-runner-01.eqiad.wmflabs',
        'quarry-runner-02.eqiad.wmflabs'
    ]
}
env.use_ssh_config = True

venv_dir = '/srv/venv'
code_dir = '/srv/quarry'


def sr(cmd):
    return sudo(cmd, user='quarry')


def generate_dbname_mapping():
    specials = [
        ["centralauth_p", "CentralAuth"],
        ["meta_p", "Meta (information about databases)"],
        ["heartbeat_p", "Heartbeat (replication lag info)"]
    ]
    family_map = {
        'wiki': 'Wikipedia',  # hysterical raisins
        'wikiquote': 'Wikiquote',
        'wikinews': 'Wikinews',
        'wiktionary': 'Wiktionary',
        'wikivoyage': 'Wikivoyage',
        'wikiversity': 'Wikiversity',
        'wikisource': 'Wikisource',
        'wikibooks': 'Wikibooks'
    }
    banned_dbs = ['labswiki', 'labtestwiki']  # https://phabricator.wikimedia.org/T89548
    r = requests.get("https://meta.wikimedia.org/w/api.php?action=sitematrix&format=json&" +
                     "smstate=all%7Cclosed%7Cfishbowl")
    wikis = []
    for key, value in r.json()['sitematrix'].items():
        if key == 'specials':
            for special in value:
                wikis.append((special['dbname'] + "_p", special['sitename']))
        elif key != 'count':
            langname = value['localname']
            for site in value['site']:
                if site['dbname'] not in banned_dbs:
                    wikis.append((site['dbname'] + "_p", langname + ' ' + family_map[site['code']]))

    wikis.sort(key=operator.itemgetter(1))
    with open(os.path.join(os.path.dirname(__file__), 'quarry/web/dbs.json'), 'w') as f:
        json.dump(specials + wikis, f)


@roles('web', 'runner')
def update_git():
    with cd(code_dir):
        sr('git fetch origin')
        sr('git reset --hard origin/master')


@roles('web')
def restart_uwsgi():
    sudo('service uwsgi restart')


@roles('runner')
def restart_celery():
    sudo('service celeryd restart')


@roles('web', 'runner')
def update_config(config_file):
    put(config_file, '/srv/quarry/quarry/config.yaml', use_sudo=True)
    sudo('chown quarry:www-data /srv/quarry/quarry/config.yaml')


@roles('db')
def run_sql(sql_file):
    put(sql_file, '/tmp/%s' % sql_file)
    sr('mysql -u root -p < "/tmp/%s"' % sql_file)
