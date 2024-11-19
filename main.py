import socket
import threading
import time
import argparse
import re
import os
import logging
import yaml
import sys
from dnslib import DNSRecord
from pythonping import ping

def check_health(client):
  global domain_health

  while True:
    if domain in HEALTH_CHECKS:
      host = client['ip']
      for _ in range(HEALTH_CHECK_MAX_RETRIES):
        try:
          response = ping(host, timeout=HEALTH_CHECK_TIMEOUT, count=5)
          domain_health[client['domain']] = response.success()
        except:
          domain_health[client['domain']] =False
    time.sleep(HEALTH_CHECK_INTERVAL)

def forward_dns(data, server):
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  try:
    ip, port = server.split(':')
    sock.sendto(data, (ip, int(port)))
    response, _ = sock.recvfrom(512)
    return response
  except:
    logger.error('Error forwarding DNS request')
    return None
  finally:
    sock.close()

def get_base_domain(domain):
  for base_domain in HEALTH_CHECKS.keys():
    if domain.endswith(base_domain):
      return base_domain
  return None

def handle_request(data, addr, sock):
  global domain_health

  try:
    request = DNSRecord.parse(data)
    domain = str(request.q.qname).strip('.')
  except:
    logger.error('Error parsing DNS request')
    return

  base_domain = get_base_domain(domain)
  if base_domain:
    target_server = PRIMARY_DNS if domain_health[base_domain] else SECONDARY_DNS
  else:
    target_server = PRIMARY_DNS
  response = forward_dns(data, target_server)

  if response:
    sock.sendto(response, addr)
  else:
    logger.info('No response from DNS server')

def start_server(port):
  logger.info(f'Starting DNS server on port {port}')
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.bind(('0.0.0.0', port))

  while True:
    data, addr = sock.recvfrom(512)
    threading.Thread(target=handle_request, args=(data, addr, sock)).start()

def args_validator():
  try:
    global PORT
    PORT = int(args.port)
  except:
    return 'Port has to be an integer'

  try:
    global HEALTH_CHECK_INTERVAL
    HEALTH_CHECK_INTERVAL = int(args.interval)
  except:
    return 'Health check interval has to be an integer'

  try:
    global HEALTH_CHECK_MAX_RETRIES
    HEALTH_CHECK_MAX_RETRIES = int(args.retries)
  except:
    return 'Health check max retries has to be an integer'

  try:
    global HEALTH_CHECK_TIMEOUT
    HEALTH_CHECK_TIMEOUT = float(args.timeout)
  except:
    return 'Health check timeout has to be a float'
  
  dns_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+$'
  global PRIMARY_DNS
  global SECONDARY_DNS
  PRIMARY_DNS = args.primary if ':' not in args.primary else args.primary + ':53'
  SECONDARY_DNS = args.secondary if ':' not in args.secondary else args.secondary + ':53'

  if re.match(PRIMARY_DNS, dns_pattern):
    return '''Invalid primary DNS server address pattern
Allowed pattern: <ip>:<port> or <ip>'''

  if re.match(SECONDARY_DNS, dns_pattern):
    return '''Invalid secondary DNS server address pattern
Allowed pattern: <ip>:<port> or <ip>'''

  health_check_path = args.health_checks_path
  if not os.path.exists(health_check_path):
    return 'Health checks file not found'
  
  try:
    with open(health_check_path, 'r') as file:
      yaml_output = yaml.safe_load(file)
      if not yaml_output:
        Exception('Empty health check YAML file')

      if 'health_checks' not in yaml_output:
        Exception('Invalid health check YAML file')

      global domain_health
      domain_health = {}

      for _, item in enumerate(yaml_output['health_checks']):
        if 'domain' not in item or 'host' not in item:
          Exception('Invalid health check YAML file')
        domain_health[item['domain']] = True
      
      global HEALTH_CHECKS
      HEALTH_CHECKS= yaml_output['health_checks']
  except yaml.YAMLError as e:
    return 'Invalid health check YAML file'
  except Exception as e:
    return 'Error reading health check YAML file'

if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO)
  logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  logger = logging.getLogger(' dns-proxy')

  parser = argparse.ArgumentParser()
  parser.add_argument('--primary', help='Primary DNS server address', default='127.0.0.1:54')
  parser.add_argument('--secondary', help='Secondary DNS server address', default='127.0.0.1:55')
  parser.add_argument('--interval', help='Health check interval', default=10)
  parser.add_argument('--retries', help='Health check max retries', default=3)
  parser.add_argument('--port', help='DNS server port', default=53)
  parser.add_argument('--timeout', help='Health check timeout', default=0.3)
  parser.add_argument('--health-checks-path', help='Health checks', default='/etc/dns-proxy/health-check.yml')
  args = parser.parse_args()

  error = args_validator()

  if error:
    logger.error(error)
    sys.exit(1)

  for domain in HEALTH_CHECKS:
    threading.Thread(target=check_health, args=(domain,), daemon=True).start()

  try:
    start_server(PORT)
  except KeyboardInterrupt:
    logger.info('Shutting down DNS server')