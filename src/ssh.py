import paramiko


class OTCSSH(object):

    def __init__(self, ip, user, passwd, identity_file):
        self.ip = ip
        self.user = user
        self.passwd = passwd
        self.ifile = identity_file
        self.client = None

        try:
            self.client = self.__connect(ip, user, passwd, identity_file)
        except Exception as e:
            print(e.message)

    def __connect(self, ip, user, passwd, identity_file):
        print('ssh connect %s@%s -i %s' % (user, ip, identity_file))
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, port=22, username=user, password=passwd,
                    key_filename=identity_file)
        return ssh

    def execute(self, cmds):
        if not self.client:
            print('  ERROR: ', self.ip, 'have not connected')
            return

        print('Exec '),
        for cmd in cmds:
            stdin, stdout, stderr = self.client.exec_command(cmd)
            print(cmd + " on " + self.ip)
            output = stdout.readlines()
            print(' output: '),
            if not output:
                print('ok')

            for info in output:
                print(info)

            err = stderr.readlines()
            print(' error: '),
            if not err:
                print('-')

            for info in err:
                print(info)
