import os, sys, time, requests, re

TELEGRAM_API_TOKEN = os.environ.get("TELEGRAM_API_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if (TELEGRAM_API_TOKEN is None):
    print("Please provide TELEGRAM_API_TOKEN in environment.")
    sys.exit(1)
if (TELEGRAM_CHAT_ID is None):
    print("Please provide TELEGRAM_CHAT_ID in environment.")
    sys.exit(1)

file_name = "/ha/home-assistant.log"
apiURL = f'https://api.telegram.org/bot{TELEGRAM_API_TOKEN}/sendMessage'

def handle_log_line(line):
    timex = re.search(r"(\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d)", line)
    if (timex):
        tstamp = timex.group(1)
        if "Serving /auth/token" in line:
            rexsult = re.search(r" to ([\d\.]+)", line)
            response = requests.post(apiURL, json={'chat_id': TELEGRAM_CHAT_ID, 'text': "HAlog ({}): successful login from {}".format(tstamp, rexsult.group(1)), 'disable_notification': True})
        if "Serving /auth/login_flow/" in line:
            rexsult = re.search(r" to ([\d\.]+)", line)
            response = requests.post(apiURL, json={'chat_id': TELEGRAM_CHAT_ID, 'text': "HAlog ({}): login attempt from {}".format(tstamp, rexsult.group(1))})
        if "Login attempt or request with invalid authentication from" in line:
            rexsult = re.search(r" from (.+)\. Requested", line)
            response = requests.post(apiURL, json={'chat_id': TELEGRAM_CHAT_ID, 'text': "HAlog ({}): failed login from {}".format(tstamp, rexsult.group(1))})

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
            handle_log_line(line)