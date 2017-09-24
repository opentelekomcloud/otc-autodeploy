import os_client_config

import src.cfg as cfg
from src.const import AUTH_URL


CONF = cfg.CONF


class OTCManager(object):
    def __init__(self):
        self.cloud = None
        self.user_id = None
        self.project_id = None
        self.router = None
        self.networks = []

    def create_connection(self):
        self.cloud = os_client_config.make_shade(auth_url=AUTH_URL,
                                                 username=CONF.user,
                                                 password=CONF.password,
                                                 user_domain_name=CONF.user_domain,
                                                 project_name=CONF.project_name)
        self.user_id = self.cloud.keystone_session.get_user_id()
        if self.user_id:
            print "Connection to cloud success..."

        self.project_id = self.cloud.keystone_session.get_project_id()
        self.router = self.cloud.get_router(CONF.vpc_name)
        if self.router:
            self.networks = self.cloud.list_networks(
                filters={'name':self.router.id}
            )

OTC = OTCManager()
