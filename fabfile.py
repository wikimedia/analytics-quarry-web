from fabric.api import sudo, env, cd, put, roles

env.roledefs = {
    'web': ['quarry-main-01.eqiad.wmflabs'],
    'db': ['quarry-main-01.eqiad.wmflabs'],
    'runner': ['quarry-runner-01.eqiad.wmflabs', 'quarry-runner-test.eqiad.wmflabs']
}
env.use_ssh_config = True

venv_dir = '/srv/venv'
code_dir = '/srv/quarry'


def sr(cmd):
    return sudo(cmd, user='quarry')


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
