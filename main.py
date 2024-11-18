import socket
import threading
import requests
import time
from dnslib import DNSRecord, DNSHeader, RR, QTYPE, A

PRIMARY_DNS = '127.0.0.1:54'
SECONDARY_DNS = '127.0.0.1:55'
HEALTH_CHECK_INTERVAL = 10

HEALTH_CHECKS = {
  'example.kl': 'http://10.70.1.2'
}

domain_health = {
  'example.kl': True
}

def check_health(domain):
  global domain_health

  while True:
    if domain in HEALTH_CHECKS:
      url = HEALTH_CHECKS[domain]
      try:
        response = requests.get(url)
        domain_health[domain] = response.status_code == 200
      except:
        domain_health[domain] = False
    time.sleep(HEALTH_CHECK_INTERVAL)

def forward_dns(data, server):
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  try:
    ip, port = server.split(':')
    sock.sendto(data, (ip, int(port)))
    response, _ = sock.recvfrom(512)
    return response
  except:
    print('Error forwarding DNS request')
    return None
  finally:
    sock.close()

def get_base_domain(domain):
  for base_domain in HEALTH_CHECKS:
    if domain.endswith(base_domain):
      return base_domain
  return None

def handle_request(data, addr, sock):
  global domain_health

  try:
    request = DNSRecord.parse(data)
    domain = str(request.q.qname).strip('.')
  except:
    print('Error parsing DNS request')
    return

  base_domain = get_base_domain(domain)
  target_server = PRIMARY_DNS if domain_health[base_domain] else SECONDARY_DNS
  response = forward_dns(data, target_server)

  if response:
    sock.sendto(response, addr)
  else:
    print('No response from DNS server')

def start_server():
  print('Starting DNS server on port 53')
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.bind(('0.0.0.0', 53))

  while True:
    data, addr = sock.recvfrom(512)
    threading.Thread(target=handle_request, args=(data, addr, sock)).start()

if __name__ == '__main__':
  for domain in HEALTH_CHECKS:
    threading.Thread(target=check_health, args=(domain,), daemon=True).start()

  try:
    start_server()
  except KeyboardInterrupt:
    print('Shutting down DNS server')