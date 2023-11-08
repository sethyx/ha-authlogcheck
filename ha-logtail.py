import os, sys, time, requests, re, ipaddress

IP2LOC_API_TOKEN = os.environ.get("IP2LOC_API_TOKEN")
TELEGRAM_API_TOKEN = os.environ.get("TELEGRAM_API_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
NETWORK_WHITELIST = os.environ.get("NETWORK_WHITELIST")
PUBLIC_IP_API = "https://api.ipify.org?format=json"

if (IP2LOC_API_TOKEN is None):
    print("Please provide IP2LOC_API_TOKEN in environment.")
    sys.exit(1)
if (TELEGRAM_API_TOKEN is None):
    print("Please provide TELEGRAM_API_TOKEN in environment.")
    sys.exit(1)
if (TELEGRAM_CHAT_ID is None):
    print("Please provide TELEGRAM_CHAT_ID in environment.")
    sys.exit(1)
if (NETWORK_WHITELIST is None):
    print("Please provide NETWORK_WHITELIST in environment.")
    sys.exit(1)

file_name = "/ha/home-assistant.log"
telegramAPI = f'https://api.telegram.org/bot{TELEGRAM_API_TOKEN}/sendMessage'

def handle_log_line(line):
    timex = re.search(r"(\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d)", line)
    if (timex):
        tstamp = timex.group(1)
        if "Serving /auth/token" in line:
            rexsult = re.search(r" to ([\w\.:]+)", line)
            ip = rexsult.group(1)
            if not valid_ip(ip):
                return
            if check_if_lan_ip(ip):
                # LAN IP and logged in, no action needed
                print("Successful login from LAN IP: {}".format(ip))
                log_and_send_message("success", False, tstamp, ip)
            else:
                if check_if_own_public_ip(ip):
                    log_and_send_message("success", False, tstamp, ip)
                else:
                    ip2locdata = lookup_external_ip(ip)
                    log_and_send_message("success", True, tstamp, ip, ip2locdata)
                        
        if "Serving /auth/login_flow/" in line:
            rexsult = re.search(r" to ([\w\.:]+)", line)
            ip = rexsult.group(1)
            if not valid_ip(ip):
                return
            if not check_if_lan_ip(ip) and not check_if_own_public_ip(ip):
                ip2locdata = lookup_external_ip(ip)
                log_and_send_message("attempt", True, tstamp, ip, ip2locdata)
            else:
                log_and_send_message("attempt", False, tstamp, ip)
                
        if "Login attempt" in line:
            rexsult = re.search(r" from .+\(([\.:\w]+)\)\. Requested", line)
            ip = rexsult.group(1)
            if not valid_ip(ip):
                return
            if check_if_lan_ip(ip):
                log_and_send_message("failed", True, tstamp, ip)

            else:
                if check_if_own_public_ip(ip):
                    log_and_send_message("failed", True, tstamp, ip)
                else:
                    ip2locdata = lookup_external_ip(ip)
                    log_and_send_message("failed", True, tstamp, ip, ip2locdata)


def log_and_send_message(ltype, send_telegram, tstamp, ip, ip2locdata=None):
    if (ip2locdata):
        msg = "HA ({}): login {} from external IP: {}, {}, {}".format(tstamp, ltype, ip, ip2locdata.get('country'), ip2locdata.get('as'))
    else:
        msg = "HA ({}): login {} from IP: {}".format(tstamp, ltype, ip)

    print(msg)
    if send_telegram:
        try:
            response = requests.post(telegramAPI, json={'chat_id': TELEGRAM_CHAT_ID, 'text': msg})
        except Exception as e:
            print("Failed to send Telegram message: {}".format(str(e)))

               
def valid_ip(ip):
    try:
        ipaddress.ip_address(ip)
        print("{} is a valid IP".format(ip))
        return True
    except ValueError as e:
        print("{} is not an IP".format(ip))
    return False

def lookup_external_ip(ip):
    payload = {'key': '4A3431F20C9106E063FC01763918BD63', 'ip': ip, 'format': 'json'}
    try:
        api_result = requests.get('https://api.ip2location.io/', params=payload)
        data = api_result.json()
        return {'country': data.get('country_name'), 'isp': data.get('isp'), }
    except Exception as e:
        print("Error during ip2loc: {}".format(str(e)))
        return None

def check_if_lan_ip(ip):
    return ipaddress.ip_address(ip) in ipaddress.ip_network(NETWORK_WHITELIST)

def check_if_own_public_ip(ip):
    try:
        response = requests.get(PUBLIC_IP_API)
        public_ip = response.json().get('ip')
        if public_ip == ip:
            return True
    except Exception as e:
        print("Error checking public IP: {}".format(str(e)))
    return False

print("Starting up logtailer")

seek_end = True
while True:  # handle moved/truncated files by allowing to reopen
    with open(file_name) as f:
        if seek_end:  # reopened files must not seek end
            f.seek(0, 2)
        while True:  # line reading loop
            line = f.readline()
            if not line:
                try:
                    if f.tell() > os.path.getsize(file_name):
                        # rotation occurred (copytruncate/create)
                        f.close()
                        seek_end = False
                        break
                except FileNotFoundError:
                    # rotation occurred but new file still not created
                    pass  # wait 1 second and retry
                time.sleep(1)
            try:
                handle_log_line(line)
            except Exception as e:
                print("Exception while handling line: {}".format(str(e)))