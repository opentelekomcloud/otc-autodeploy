# import os_client_config
from openstack import connection

import cfg
from const import AUTH_URL


CONF = cfg.CONF


class OTCConn(object):
    def __init__(self):
        self.conn = None

    def create_connection(self):
#         self.conn = os_client_config.make_shade(auth_url=AUTH_URL,
#                                                 username=CONF.user,
#                                                 password=CONF.password,
#                                                 user_domain_name=CONF.user_domain,
#                                                 project_name=CONF.project_name)


        self.conn = connection.Connection(auth_url=AUTH_URL,
                                          project_name=CONF.project_name,
                                          project_id=CONF.project_id,
                                          username=CONF.user,
                                          password=CONF.password,
                                          user_domain_name=CONF.user_domain
                                          )
        self.conn.session.get_endpoint(service_type='compute')

OTC=OTCConn()
