import threading, argparse, logging, sys, settings
from utils import check_health, args_validator, start_server

if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  settings.logger = logging.getLogger('dns-proxy')

  parser = argparse.ArgumentParser()
  parser.add_argument('--primary', help='Primary DNS server address', default='127.0.0.1:54')
  parser.add_argument('--secondary', help='Secondary DNS server address', default='127.0.0.1:55')
  parser.add_argument('--interval', help='Health check interval', default=10)
  parser.add_argument('--retries', help='Health check max retries', default=3)
  parser.add_argument('--port', help='DNS server port', default=53)
  parser.add_argument('--timeout', help='Health check timeout', default=0.3)
  parser.add_argument('--health-checks-path', help='Health checks', default='/etc/dns-proxy/health-check.yml')
  args = parser.parse_args()

  settings.PRIMARY_DNS = args.primary
  settings.SECONDARY_DNS = args.secondary
  settings.HEALTH_CHECK_INTERVAL = args.interval
  settings.HEALTH_CHECK_MAX_RETRIES = args.retries
  settings.HEALTH_CHECK_TIMEOUT = args.timeout
  settings.PORT = args.port

  error = args_validator(args.health_checks_path)

  if error:
    settings.logger.error(error)
    sys.exit(1)

  for domain in settings.HEALTH_CHECKS:
    threading.Thread(target=check_health, args=(domain,), daemon=True).start()

  try:
    start_server(settings.PORT)
  except KeyboardInterrupt:
    settings.logger.info('Shutting down DNS server')