import os


OK = "ok"
ERR = "nok"

DEPLOY_MODE_ST = 'ST'
DEPLOY_MODE_HA = 'HA'

AUTH_URL = "https://iam.eu-de.otc.t-systems.com:443/v3"

ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                         os.pardir))
CONF_PATH = os.path.join(ROOT_PATH, 'conf')
SRC_PATH = os.path.join(ROOT_PATH, 'src')
SRC_TEMPLATE_PATH = os.path.join(SRC_PATH, 'template')
SSH_PATH = os.path.join(ROOT_PATH, 'ssh')
HOT_TEMPLATE_PATH = os.path.join(ROOT_PATH, 'hot_template')

# server state
SERVER_STATE_INIT = 0
SERVER_STATE_DEPLOY = 1
SERVER_STATE_INSTALLED = 2
