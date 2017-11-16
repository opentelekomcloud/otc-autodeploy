import os
from threading import Thread
from prettytable import PrettyTable
from time import sleep

from src.deploy_chef_base import ChefBase
from src.deploy_base_server import deploy_server
from src.ssh import ssh_connect
from src.utils import exe_time
from src.const import SERVER_STATE_DEPLOY, SERVER_STATE_INSTALLED, ROOT_PATH


class ChefApache(ChefBase):

    def __init__(self):
        super(ChefApache, self).__init__()

        self.chef_apache = None

    def deploy_chef_apache(self):
        print("Start deploy chef apache ...")
        server_name = "apache-" + self.random
        self.chef_apache = deploy_server(server_name,
                                    "Community_Ubuntu_16.04_TSI_20170630",
                                    "c2.xlarge", self.keypair.name, None, None,
                                    self.private_sg.name,
                                    80, self.private_net.id, eip=False)

        # wait for chef-workstation
        for i in range(1200):
            if (self.chef_server_state >= SERVER_STATE_INSTALLED
                and self.chef_workstation_state >= SERVER_STATE_INSTALLED):
                break
            else:
                sleep(2)
                continue

        ssh_conn, sftp_conn = ssh_connect(
            self.chef_workstation['fip'].floating_ip_address,
            'ubuntu', None, identity_file=self.keypair_path)

        cmds = '''#!/bin/bash
echo "cookbook 'apache2'" | sudo tee -a ~/chef-repo/Berksfile
cd ~/chef-repo
sudo berks vendor
SSL_CERT_FILE='~/chef-repo/.chef/admin.pem' berks upload
sudo knife bootstrap {node_ip} -N {node_name} -x ubuntu -i ~/chef-repo/.chef/{key_pair} --sudo --run-list "recipe[chef-client],recipe[apache2]"
'''.format(node_ip=self.chef_apache['private_ip'],
           node_name=server_name,
           key_pair=self.key_name)

        sh_file = '/tmp/' + server_name + '.sh'
        with open(sh_file, 'w') as f:
            f.write(cmds)

        dst_sh_file = '/home/ubuntu/' + server_name + '.sh'
        sftp_conn.put(sh_file, dst_sh_file)
        os.remove(sh_file)

        ssh_conn.exec_command('sudo chmod +x ' + dst_sh_file)
        stdin, stdout, stderr = ssh_conn.exec_command(
            'sudo bash ' + dst_sh_file + ' > ' + server_name + 'log.log')

        for i in range(900):
            if (not stdout.channel.exit_status_ready()
                and not stdout.channel.recv_ready()):
                sleep(2)
            else:
                break
        else:
            print('Server ' + server_name + ' can not connect to '
                  'external network, install fail')

        ssh_conn.close()
        sftp_conn.close()
        print("Deploy chef apache end.")

@exe_time
def deploy():
    chef = ChefApache()
    chef.deploy_chef_net()

    t1 = Thread(target=chef.deploy_chef_server)
    t2 = Thread(target=chef.deploy_chef_workstation)
    t3 = Thread(target=chef.deploy_chef_apache)
    t1.start()
    t2.start()
    t3.start()

    t1.join()
    t2.join()
    t3.join()

    chef_server = chef.chef_server
    chef_workstation = chef.chef_workstation
    chef_apache = chef.chef_apache

    print('\r\n' * 2)
    t = PrettyTable(['Property', 'Value'])
    t.align = 'l'
    t.add_row(['vpc-name', chef.vpc.name])
    t.add_row(['vpc-cidr', str(chef.vpc.cidr)])
    t.add_row(['chef-server-name', chef_server['server'].name])
    t.add_row(['chef-server-eip', chef_server['fip'].floating_ip_address])
    t.add_row(['chef-admin-user', 'admin'])
    t.add_row(['chef-admin-passwd', chef.admin_passwd])
    t.add_row(['chef-workstation-name', chef_workstation['server'].name])
    t.add_row(['chef-workstation-eip', chef_workstation['fip'].floating_ip_address])
    t.add_row(['chef-apache-name', chef_apache['server'].name])
    t.add_row(['key-pair', chef.key_name])
    t.add_row(['key-pair-path', chef.keypair_path])
    print(t)
