import os_client_config
import os
from openstack import connection

import src.cfg as cfg
from src.const import AUTH_URL


CONF = cfg.CONF


def init_env():
    os.environ['OS_USERNAME'] = CONF.user
    os.environ['OS_USER_DOMAIN_NAME'] = CONF.user_domain
    os.environ['OS_PASSWORD'] = CONF.password
    os.environ['OS_TENANT_NAME'] = CONF.project_name
    os.environ['OS_PROJECT_NAME'] = CONF.project_name
    os.environ['OS_AUTH_URL'] = AUTH_URL
    os.environ['OS_INTERFACE'] = 'public'
    os.environ['NOVA_ENDPOINT_TYPE'] = 'publicURL'
    os.environ['OS_ENDPOINT_TYPE'] = 'publicURL'
    os.environ['CINDER_ENDPOINT_TYPE'] = 'publicURL'
    os.environ['OS_VOLUME_API_VERSION'] = '2'
    os.environ['OS_IDENTITY_API_VERSION'] = '3'
    os.environ['OS_IMAGE_API_VERSION'] = '2'


class OTCManager(object):
    def __init__(self):
        self.cloud = None
        self.user_id = None
        self.project_id = None
        self.router = None
        self.networks = []

    def create_connection(self):
        init_env()

        self.op_conn = connection.Connection(auth_url=AUTH_URL,
                                             username=CONF.user,
                                             password=CONF.password,
                                             user_domain_name=CONF.user_domain,
                                             project_name=CONF.project_name)

        self.cloud = os_client_config.make_shade(auth_url=AUTH_URL,
                                                 username=CONF.user,
                                                 password=CONF.password,
                                                 user_domain_name=CONF.user_domain,
                                                 project_name=CONF.project_name)
        self.user_id = self.cloud.keystone_session.get_user_id()
        if self.user_id:
            print ">>> Connection OK"

        self.project_id = self.cloud.keystone_session.get_project_id()

        if CONF.vpc_name:
            self.router = self.cloud.get_router(CONF.vpc_name)
            if self.router:
                self.networks = self.cloud.list_networks(
                    filters={'name':self.router.id}
                )


OTC = OTCManager()
