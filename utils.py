import re, os, yaml, time, socket, threading
import settings
from dnslib import DNSRecord
from pythonping import ping

def check_health(client):
  while True:
    if client['domain'] in settings.domain_health.keys():
      host = client['ip']
      for _ in range(settings.HEALTH_CHECK_MAX_RETRIES):
        try:
          response = ping(host, timeout=settings.HEALTH_CHECK_TIMEOUT, count=5, interval=0.3)
          settings.domain_health[client['domain']] = response.success()

          if settings.domain_health[client['domain']]:
            break
        except:
          settings.domain_health[client['domain']] = False
    time.sleep(settings.HEALTH_CHECK_INTERVAL)

def forward_dns(data, server):
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  try:
    ip, port = server.split(':')
    sock.sendto(data, (ip, int(port)))
    response, _ = sock.recvfrom(512)
    return response
  except:
    settings.logger.error('Error forwarding DNS request')
    return None
  finally:
    sock.close()

def get_base_domain(domain):
  domain_splitted = domain.split('.')
  for i in range(len(domain_splitted)):
    base_domain = '.'.join(domain_splitted[i:])
    if base_domain in settings.EXCLUDE:
      return None

  for i in range(0, len(domain_splitted)):
    base_domain = '.'.join(domain_splitted[i:])
    if base_domain in settings.domain_health.keys():
      return base_domain.lower()

def handle_request(data, addr, sock):
  try:
    request = DNSRecord.parse(data)
    domain = str(request.q.qname).strip('.').lower()
  except:
    settings.logger.error('Error parsing DNS request')
    return

  base_domain = get_base_domain(domain)
  if base_domain:
    target_server = settings.PRIMARY_DNS if settings.domain_health[base_domain] else settings.SECONDARY_DNS
  else:
    target_server = settings.PRIMARY_DNS
  response = forward_dns(data, target_server)

  if response:
    sock.sendto(response, addr)
  else:
    settings.logger.info('No response from DNS server')

def start_server(port):
  settings.logger.info('DNS server is starting')
  try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', port))
    settings.logger.info(f'DNS server is litening on {port}')
  except:
    settings.logger.error('Error binding DNS server to port')
    return

  while True:
    data, addr = sock.recvfrom(512)
    threading.Thread(target=handle_request, args=(data, addr, sock)).start()

def args_validator(health_checks_path):
  try:
    settings.PORT = int(settings.PORT)
  except:
    return 'Port has to be an integer'

  try:
    settings.HEALTH_CHECK_INTERVAL = int(settings.HEALTH_CHECK_INTERVAL)
  except:
    return 'Health check interval has to be an integer'

  try:
    settings.HEALTH_CHECK_MAX_RETRIES = int(settings.HEALTH_CHECK_MAX_RETRIES)
  except:
    return 'Health check max retries has to be an integer'

  try:
    settings.HEALTH_CHECK_TIMEOUT = float(settings.HEALTH_CHECK_TIMEOUT)
  except:
    return 'Health check timeout has to be a float'

  dns_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+$'
  settings.PRIMARY_DNS = settings.PRIMARY_DNS if ':' in settings.PRIMARY_DNS else settings.PRIMARY_DNS + ':53'
  settings.SECONDARY_DNS = settings.SECONDARY_DNS if ':' in settings.SECONDARY_DNS else settings.SECONDARY_DNS + ':53'

  if re.match(settings.PRIMARY_DNS, dns_pattern):
    return '''Invalid primary DNS server address pattern
Allowed pattern: <ip>:<port> or <ip>'''

  if re.match(settings.SECONDARY_DNS, dns_pattern):
    return '''Invalid secondary DNS server address pattern
Allowed pattern: <ip>:<port> or <ip>'''

  if not os.path.exists(health_checks_path):
    return 'Health checks file not found'

  try:
    with open(health_checks_path, 'r') as file:
      yaml_output = yaml.safe_load(file)
      if not yaml_output:
        Exception('Empty health check YAML file')

      if 'health_checks' not in yaml_output:
        Exception('Invalid health check YAML file')

      settings.domain_health = {}
      settings.HEALTH_CHECKS = []

      for _, item in enumerate(yaml_output['health_checks']):
        if 'domain' not in item or 'ip' not in item:
          Exception('Invalid health check YAML file')
        settings.domain_health[item['domain']] = True
        if len(item) > 2:
          raise Exception('Too many fields in health check item')
      
      if 'exclude' in yaml_output and not isinstance(yaml_output['exclude'], list):
        raise Exception('Exclude field must be a list')
      
      for domain in yaml_output['exclude']:
        if not isinstance(domain, str):
          raise Exception('Exclude field must contain only strings')

      settings.HEALTH_CHECKS = yaml_output['health_checks']
      settings.EXCLUDE = yaml_output['exclude']
  except yaml.YAMLError as e:
    return 'Invalid health check YAML file'
  except Exception as e:
    return e