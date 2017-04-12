import logging
import pickle
import signal
import smtplib
import sys
import time
from email.mime.text import MIMEText

import facebook

def connectSMTP():
    s = smtplib.SMTP('<smtp-server>', 587)
    s.ehlo()
    if s.has_extn('STARTTLS'):
        s.starttls()
        s.ehlo()
    s.login('<username>', '<password>')
    logger.debug("SMTP Connected!")
    return s

def genHTML(msg, id_):
    event_id, post_id = id_.split("_")
    message = "<br>".join(msg.split("\n"))
    link = "https://www.facebook.com/events/{0}/{1}".format(event_id, post_id)
    html = "<html><head></head><body>" + message + "<br><a href='" + link + "'>Goto Post</a></body></html>"
    return html

def sendEmail(html):
    server = connectSMTP()
    recipients = ["<email-address>"]
    content = MIMEText(html, 'html')
    content['Subject'] = "<email-subject>"
    content['From'] = "<email-address>"
    content['Bcc'] = ", ".join(recipients)
    server.send_message(content)
    server.quit()

def handler(signum, frame):
    logger.info("Terminated!")
    with open("read_id.data", "wb") as out_file:
        logger.debug("Store read_id.")
        pickle.dump(read_id, out_file)
    sys.exit(0)

logging.basicConfig(format="%(levelname)s: %(message)s")
logger = logging.getLogger("<logger name>")
logger.setLevel(logging.DEBUG)

EVENT_ID = "<event-id>"
KEYWORDS = ["keyword"]

try:
    logger.debug("Load read_id.data.")
    with open("read_id.data", "rb") as in_file:
        read_id = pickle.load(in_file)
except FileNotFoundError:
    logger.debug("Create read_id.data.")
    read_id = set()

graph = facebook.GraphAPI(access_token='<access-token>', version='<api-version>')
signal.signal(signal.SIGINT, handler)

while True:
    try:
        req = EVENT_ID + "/feed"
        posts = graph.get_object(id=req)
    except facebook.GraphAPIError as e:
        logger.error("Graph API error: {}".format(e.result))
        continue

    for post in posts['data']:
        msg = post['message']
        id_ = post['id']
        if id_ in read_id:
            continue
        for keyword in KEYWORDS:
            if keyword in msg.lower():
                logger.info(msg + "\n" + "*" * 30)
                html = genHTML(msg, id_)
                sendEmail(html)
                read_id.add(id_)
                break
    print(".", end="")
    sys.stdout.flush()
    time.sleep(1)
