import imaplib
import email
import logging
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import oci  # Ensure you've installed the OCI Python SDK

# Setup logging
logging.basicConfig(filename='C:\\Users\\Satish Loyapally\\Desktop\\Invoice_AI\\OCI\\emaillogfile_v3.log',
                    filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

# Gmail credentials and server details
imap_host = 'imap.gmail.com'
imap_user = 'schandraly@gmail.com'
imap_pass = 'adwytpkzzvmgybck'

# OCI Config setup
config = oci.config.from_file("C:\\Users\\Satish Loyapally\\.oci\\config")
object_storage = oci.object_storage.ObjectStorageClient(config)
namespace = object_storage.get_namespace().data

# Specify your bucket name
bucket_name = 'Test_bucket'

# Track the last processed email time
last_processed_time = datetime.now(tz=timezone.utc) - timedelta(minutes=1)

def get_internal_date(email_id):
    try:
        result, data = mail.fetch(email_id, '(INTERNALDATE)')
        if result == 'OK':
            internal_date_raw = data[0].decode()
            internal_date_str = internal_date_raw.split('"')[1]  # Extract the date string
            return parsedate_to_datetime(internal_date_str)
        else:
            logging.error(f"Failed to fetch internal date for email {email_id}: {data}")
            return None
    except Exception as e:
        logging.error(f"Error parsing internal date for email {email_id}: {e}")
        return None

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
            if email_time and email_time > last_processed_time:
                _, msg_data = mail.fetch(e_id, '(RFC822)')
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        download_attachments(msg)
                        last_processed_time = max(last_processed_time, email_time)
    except Exception as e:
        logging.error("Error checking for invoices: " + str(e))

try:
    mail = imaplib.IMAP4_SSL(imap_host)
    mail.login(imap_user, imap_pass)
    mail.select('inbox')
    logging.info("Logged in and selected inbox successfully.")
except Exception as e:
    logging.error("Error connecting to email server: " + str(e))
    exit()

while True:
    logging.info("Checking for new invoices...")
    check_for_invoices()
    time.sleep(60)  # Check every 1 minute
