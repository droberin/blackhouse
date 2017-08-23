import os.path
import blackhouse.api as black_house
import logging
# import blackhouse.assistant
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

certificate_file = black_house.blackhouse_configuration_directory + '/ssl/cert.pem'
certificate_key = black_house.blackhouse_configuration_directory + '/ssl/cert.key'
if os.path.isfile(certificate_file) and os.path.isfile(certificate_key):
    logging.info("Certificates found. Trying to run in SSL mode")
    # order matters
    context = (certificate_file, certificate_key)
    black_house.app.run(debug=False, host="0.0.0.0", ssl_context=context, port=5001)
else:
    logging.info("No certificates found in SSL configuration folder. Running insecure socket mode")
    black_house.app.run(debug=False, host="0.0.0.0", port=5000)

# blackhouse.assistant.start_assistant()
