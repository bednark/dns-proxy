# DNS Proxy with Health Checks

This Python-based DNS Proxy server dynamically routes DNS queries to primary or secondary DNS servers based on the health status of target domains. The health of domains is monitored using ICMP ping requests. The tool supports configuration through command-line arguments and YAML files.

## Features
- Routes DNS queries to primary or secondary servers based on domain health.
- Continuously monitors the health of configured domains using ping.
- Configurable through command-line arguments.
- Health check domains and their IPs are defined in a YAML configuration file.
- Multithreaded design for handling DNS requests and domain health checks concurrently.

---

## Prerequisites
- Python 3.7 or higher
- Libraries:
  - `pythonping`
  - `PyYAML`
  - `dnslib`

Install the required dependencies using:

```bash
pip install -r requirements.txt
```

---

## Configuration

### Command-Line Arguments

The application accepts the following arguments:

| Argument | Default Value | Description |
| -------- | ------------- | ----------- |
| --primary | 127.0.0.1:54 | Address of the primary DNS server in **ip:port** or **ip** format. |
| --secondary |	127.0.0.1:55 | 	Address of the secondary DNS server in **ip:port** or **ip** format. |
| --port | 53 | Port for the DNS proxy to listen on. |
| --interval | 10 | Interval (in seconds) between health checks. |
| --retries |	3 | Maximum retries for health checks before marking a domain down. |
| --timeout | 0.3 | Timeout (in seconds) for individual ping requests. |
| --health-checks-path | /etc/dns-proxy/health-check.yml | Path to the YAML file defining domains for health checks.

---

### Health Check YAML File
The YAML file specifies the domains and their corresponding IP addresses for health checks.

Example:
```yaml
health_checks:
  - domain: example.com
    ip: 192.168.1.1
  - domain: sub.example.com
    ip: 192.168.1.2
```

---

## Usage
1. **Run the Application**
```bash
python dns_proxy.py --primary 8.8.8.8:53 --secondary 8.8.4.4:53 --interval 15 --port 5353 --timeout 0.5 --health-checks-path ./health-check.yml
```

2. **Example Logs**
When the application runs, it outputs log to the console or system journal (if run as a daemon). Example:

```
INFO - Starting DNS server on port 53
```

---

## Troubleshooting
1. **Empty or invalid YAML file:**
Ensure the YAML file is properly formatted and includes health_checks with domain and ip.

2. **Ping not working:**
Check ICMP permissions for the DNS Proxy server.

3. **DNS resolution issues:**
Verify the primary and secondary DNS server configurations.

---

## Contribution
Feel free to report issues or submit pull requests to improve this tool.