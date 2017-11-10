import os


OK = "ok"
ERR = "nok"

DEPLOY_MODE_ST = 'ST'
DEPLOY_MODE_HA = 'HA'

AUTH_URL = "https://iam.eu-de.otc.t-systems.com:443/v3"

ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                         os.pardir))
CONF_PATH = os.path.join(ROOT_PATH, 'conf')
