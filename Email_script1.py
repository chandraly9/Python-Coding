import imaplib
import email
import logging
import time
from datetime import datetime, timedelta
from email.utils import parsedate_tz, mktime_tz
import oci  # Ensure you've installed the OCI Python SDK

# Setup logging
logging.basicConfig(filename='/path/to/your/logfile.log',  # Update with your actual log file path
                    filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

# Gmail credentials and server details
imap_host = 'imap.gmail.com'  # Gmail's IMAP server
imap_user = 'your_email@gmail.com'  # Your Gmail address
imap_pass = 'your-app-password'  # Your app password

# OCI Config setup
config = oci.config.from_file("~/.oci/config")  # Default location for config file, update if needed
object_storage = oci.object_storage.ObjectStorageClient(config)
namespace = object_storage.get_namespace().data

# Specify your bucket name
bucket_name = 'Your_Bucket_Name'

# Track the last processed email time
last_processed_time = datetime.now(tz=datetime.timezone.utc) - timedelta(minutes=1)  # Start from 1 minute ago

def upload_to_oci_object_storage(object_storage, namespace, bucket_name, object_name, file_data):
    try:
        object_storage.put_object(namespace, bucket_name, object_name, file_data)
        logging.info(f'Uploaded {object_name} to OCI Object Storage in bucket {bucket_name}')
    except Exception as e:
        logging.error(f'Failed to upload {object_name}. Error: {e}')

def download_attachments(msg):
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
            continue

        file_name = part.get_filename()
        if file_name:
            file_data = part.get_payload(decode=True)
            upload_to_oci_object_storage(object_storage, namespace, bucket_name, file_name, file_data)

def check_for_invoices():
    global last_processed_time
    try:
        since_date = last_processed_time.strftime("%d-%b-%Y")
        mail.recent()  # Refresh the mailbox
        _, all_emails = mail.search(None, f'(SINCE "{since_date}")', 'HEADER Subject "Invoice"')
        for e_id in all_emails[0].split():
            email_time = get_internal_date(e_id)
            if email_time > last_processed_time:
                _, msg_data = mail.fetch(e_id, '(RFC822)')
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        download_attachments(msg)
                        last_processed_time = max(last_processed_time, email_time)
    except Exception as e:
        logging.error("Error checking for invoices: " + str(e))

# Connect to the Gmail server using IMAP over SSL
try:
    mail = imaplib.IMAP4_SSL(imap_host)
    mail.login(imap_user, imap_pass)
    mail.select('inbox')  # Select the inbox folder
    logging.info("Logged in and selected inbox successfully.")
except Exception as e:
    logging.error("Error connecting to email server: " + str(e))
    exit()

# Check for new invoices at regular intervals
while True:
    logging.info("Checking for new invoices...")
    check_for_invoices()
    time.sleep(60)  # Check every 1 minute
