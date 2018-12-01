from fabric.api import local, settings, abort, run, cd
from fabric.decorators import task
from fabric.operations import get, sudo, put
from fabric.state import env
import os

from script_templates import *


env.user = 'iptv'
env.hosts = ['213.159.56.188:22']

# service parameters see script_templates.py service_basic variable
env.iptv_service_name = 'iptv.service'
env.iptv_service_desc = 'IPTV proxy service'
env.iptv_service_user = 'root'

# directory at which we store scripts for iptv service installation
env.iptv_script_dir = '/opt/iptv/'
# name of the iptv script we want to install
env.iptv_cmd_name = 'iptv-run.sh'  # the script that starts our iptv program

# SERVICE AND TIMER NAMES MUST MATCH!
env.iptvepg_service_name = 'make-epg.service'
env.iptvepg_timer_name = 'make-epg.timer'
env.iptvepg_service_path = os.path.join('.', env.iptvepg_service_name)
env.iptvepg_timer_path = os.path.join('.', env.iptvepg_timer_name)
env.iptvepg_script_name = 'make-epg.sh'
env.iptvepg_script_owner = 'iptv'

env.web_grab_url = 'http://www.webgrabplus.com/sites/default/files/download/SW/V2.1.0/WebGrabPlus_V2.1_install.tar.gz'
GIT_REPO_URL = 'git@github.com:Povilas1/Skynet-IPTV-With-EPG.git'
env.epg_base_dir = '/opt/iptv-epg'  # arbitrary directory in which your store files
env.wg_dir = os.path.join(env.epg_base_dir, 'wgpp')
env.repo_dir = os.path.join(env.epg_base_dir, 'epg-repo')
env.iptvepg_script_path = os.path.join(env.repo_dir, 'tools')


# DO NOT CHANGE THIS UNLESS YOU KNOW WHAT YOU ARE DOING!
env.system_script_dir = '/usr/bin/'  # systemd can only call scripts from here
env.systemd_service_dir = '/etc/systemd/system/'  # path to *.service files

# Code management

def commit():
    local("git add -p && git commit")


def amend():
    local("git add -p && git commit --amend")


def push():
    local("git push origin dev")


def commit_master(do_deploy=True):
    """Does commit to dev and merges DEV -> MASTER"""
    local("git pull origin master")
    commit()
    local("git checkout master")
    local("git pull origin master")
    local("git merge dev")
    local("git push origin master")
    if do_deploy:
        deploy()
        deploy_config()


def commit_local():
    commit()
    push()


def connection_test():
    run('whoami')


# Reusable functions

def install_script_stored_on_local(local_dir, local_script_name, remote_dir, remote_script_name, mode=751, owner='root'):

    put(local_path=os.path.join(local_dir, local_script_name),
        remote_path=remote_dir,
        use_sudo=True)

    install_script_stored_on_remote(remote_dir, remote_script_name, mode, owner)


def install_script_stored_on_remote(script_dir, script_name, mode=775, owner='root'):
    """Installs script to '/usr/bin' stored on a remote machine.
    :param script_dir: folder which contains your script you want to install
    :param script_name: the actual file name you want to install to '/usr/bin/'
    :param mode: a unix permission sum 771 == -rwxrwxr-x
    """
    full_path = os.path.join(script_dir, script_name)

    with cd(script_dir):
        sudo("chmod {} {}".format(mode, script_name))
        sudo("chown {} {}".format(owner, script_name))
        sudo("ln -sf {} {}".format(full_path, env.system_script_dir))


def put_service_from_local_file(local_path):
    """Takes your localy stored *.server file and uploads it to server"""
    put(local_path=local_path, remote_path=env.systemd_service_dir, use_sudo=True)


def put_timer_from_local_file(local_path):
    """Takes your localy stored *.timer file and uploads it to server"""
    put(local_path=local_path, remote_path=env.systemd_service_dir, use_sudo=True)


def install_basic_service_from_templates(service_description, user, script_name, filename):
    """makes a simple service, see: script_templates.py -> service_basic"""
    script_path = os.path.join(env.system_script_dir, script_name)
    service = service_basic.format(
        service_description=service_description,
        user=user,
        script_path=script_path,
    )
    put_python_string(service, env.systemd_service_dir, filename, 'root')


def install_timed_service_from_files(service_name, timer_name, service_path, timer_path, do_start_service=False, boot_on_start=False, monitor=True):
    """Install a service plus timer using services stored on local disk"""
    put_service_from_local_file(service_path)
    put_timer_from_local_file(timer_path)
    if boot_on_start:
        enable_service(service_name)
    enable_timer(timer_name)
    if do_start_service:
        start_service(service_name)
    start_timer(timer_name)
    if monitor:
        service_status(service_name)
        timer_status(timer_name)


def install_timed_service_from_pystr():
    # TODO: Implement me use install_timed_service_from_files
    pass


def enable_service(service_name):
    sudo("systemctl enable {}".format(service_name))


def enable_timer(timer_name):
    sudo("systemctl enable {}".format(timer_name))


def start_service(service_name):
    sudo("systemctl start {}".format(service_name))


def start_timer(service_name):
    sudo("systemctl start {}".format(service_name))


def service_status(service_name):
    # this does not require sudo permission
    run('systemctl status {}'.format(service_name))


def service_log(service_name):
    sudo('journalctl -f -u {}'.format(service_name))


def timer_status(timer_name):
    # no sudo needed
    run('systemctl status {}'.format(timer_name))
    run('systemctl list-timers --all')


def put_python_string(data_string, path, filename, owner,  mode=644):
    """Dumps Python str to file on a server. Helps with script_templates.py"""
    with cd(path):
        sudo('echo "{}" > {}'.format(data_string, filename))
        sudo('chown {} {}'.format(owner, filename))
        sudo('chmod {} {}'.format(mode, filename))
        sudo('cat {}'.format(filename))


def user_confirms(message):
    # raw_input returns the empty string for "enter"
    yes = {'yes', 'y', 'ye', ''}
    no = {'no', 'n'}

    choice = raw_input(message).lower()
    if choice in yes:
        return True
    elif choice in no:
        return False
    else:
        print("Please respond with 'yes' or 'no'")

########################## PROJECT SPECIFIC METHODS ###########################


def deploy():
    with cd('{}'.format(env.repo_dir)):
        run('git pull origin master')


def generate_epg():
    pass


def deploy_config():
    """Deploys config edits to WG++ generator"""
    run('cp {}/tools/WebGrab++.config.xml {}'.format(env.repo_dir, env.wg_dir))


def install_iptv_epg_script_and_service():
    # TODO implement me
    # make symlink to /usr/bin/ from /opt/iptv-epg/epg-repo/tools/make-epg.sh
    install_script_stored_on_remote(
        script_dir=env.iptvepg_script_path,
        script_name=env.iptvepg_script_name,
        mode=775,
        owner='iptv:iptv')

    install_timed_service_from_files(
        service_name=env.iptvepg_service_name,
        timer_name=env.iptvepg_timer_name,
        service_path=env.iptvepg_service_path,
        timer_path=env.iptvepg_timer_path,
    )


def iptv_log():
    service_log(env.iptv_service_name)


def download_epg(local_path='/tmp'):
    """copies epg from the generator machine."""
    remote_path = "{}/guide.xml".format(env.wg_dir)
    get(remote_path=remote_path, local_path=local_path, use_sudo=True)


@task
def install_iptv_proxy_full():
    """Takes the script we want to start and adds it to /usr/bin, then makes service"""
    # TODO: needs a file for starting as service
    """
    iptv-run.sh
    
    #!/bin/bash
    /opt/iptv/iptv2rtsp-proxy -f -s 192.168.1.112 -l 5555
    """
    install_script_stored_on_remote(env.iptv_script_dir, env.iptv_cmd_name)
    # creates service file at /etc/systemd/system/
    install_basic_service_from_templates(env.iptv_service_desc, env.iptv_service_user, env.iptv_cmd_name, env.iptv_service_name, )
    start_service(env.iptv_service_name)
    enable_service(env.iptv_service_name)


@task
def install_epg():
    sudo("apt-get install -y mono-complete")

    sudo('mkdir -p {}'.format(env.epg_base_dir))
    sudo('chown -R {0}:{0} {1}'.format(env.user, env.epg_base_dir))

    with cd(env.epg_base_dir):
        run('wget {}'.format(env.web_grab_url))
        run('tar -zxvf *.tar.gz')
        run('mv .wg++ wgpp')
        run('rm *.tar.gz')
        run('bash ' + os.path.join(env.wg_dir, 'install.sh'))
        run('git clone {} epg-repo'.format(GIT_REPO_URL))
        run('ln -s {}/WebGrab++.config.xml {}/WebGrab++.config.xml'.format(env.iptvepg_script_path, env.wg_dir))


@task
def epg_install_full():
    install_epg()
    install_iptv_epg_script_and_service()





