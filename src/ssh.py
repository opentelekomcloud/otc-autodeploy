import paramiko
from time import sleep
from paramiko.ssh_exception import NoValidConnectionsError


def ssh_connect(ip, user, passwd, identity_file):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    for i in range(300):
        try:
            print('connect to %s:%s use %s' % (ip, 22, identity_file))
            ssh.connect(ip, port=22, username=user, password=passwd,
                        key_filename=identity_file)
            transport = ssh.get_transport()
            transport.send_ignore()
            sftp = paramiko.SFTPClient.from_transport(transport)
            return ssh, sftp
        except (EOFError, NoValidConnectionsError) as e:
            sleep(2)
            continue
    else:
        return None
