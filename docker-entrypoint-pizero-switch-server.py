import os
import blackhouse.switch as black_house
from blackhouse.flat_configuration import BlackhouseConfiguration
import logging
# import blackhouse.assistant
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

cfg = BlackhouseConfiguration()

# If no value is set for BH_SERVICE_TYPE set it to PUSH
os.environ['BH_SERVICE_TYPE'] = os.getenv('BH_SERVICE_TYPE', 'push')

if not os.path.isdir(cfg.config_structure['blackhouse_configuration_directory']):
    os.mkdir(cfg.config_structure['blackhouse_configuration_directory'])
certificate_file = cfg.config_structure['blackhouse_configuration_directory'] + '/ssl/cert.pem'
certificate_key = cfg.config_structure['blackhouse_configuration_directory'] + '/ssl/cert.key'
if os.path.isfile(certificate_file) and os.path.isfile(certificate_key):
    logging.info("Certificates found. Trying to run in SSL mode")
    # order matters
    context = (certificate_file, certificate_key)
    black_house.app.run(debug=False, host="0.0.0.0", ssl_context=context, port=5003)
else:
    logging.info("No certificates found in SSL configuration folder. Running insecure socket mode")
    black_house.app.run(debug=False, host="0.0.0.0", port=5002)

# blackhouse.assistant.start_assistant()
