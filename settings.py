import logging

def init():
  global PRIMARY_DNS
  global SECONDARY_DNS
  global HEALTH_CHECKS
  global EXCLUDE
  global HEALTH_CHECK_INTERVAL
  global HEALTH_CHECK_MAX_RETRIES
  global HEALTH_CHECK_TIMEOUT
  global PORT
  global domain_health
  global logger