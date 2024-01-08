import imaplib
import email
import logging
import time
from datetime import datetime, timedelta
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

# This dictionary will hold the UIDs and the last processed timestamps of emails
processed_emails = {}

def get_internal_date(email_data):
    try:
        email_message = email.message_from_bytes(email_data[0][1])
        date_tuple = email.utils.parsedate_tz(email_message['Date'])
        return datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
    except Exception as e:
        logging.error(f"Error parsing internal date: {e}")
        return None

def upload_to_oci_object_storage(object_storage, namespace, bucket_name, object_name, file_data):
    try:
        object_storage.put_object(namespace, bucket_name, object_name, file_data)
        logging.info(f'Uploaded {object_name} to OCI Object Storage in bucket {bucket_name}')
    except Exception as e:
        logging.error(f'Failed to upload {object_name}. Error: {e}')

def download_attachments(msg, email_uid, email_internal_date):
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
            continue

        file_name = part.get_filename()
        if file_name:
            # Check if the email is new or has a newer date than the last processed one
            if email_uid not in processed_emails or email_internal_date > processed_emails[email_uid]:
                file_data = part.get_payload(decode=True)
                upload_to_oci_object_storage(object_storage, namespace, bucket_name, file_name, file_data)
                processed_emails[email_uid] = email_internal_date  # Update the last processed date for this email UID

def check_for_invoices():
    try:
        since_date = (datetime.now() - timedelta(minutes=1)).strftime("%d-%b-%Y")
        result, data = mail.uid('search', None, f'(SINCE {since_date})', 'HEADER Subject "Invoice"')
        if result == 'OK':
            for num in data[0].split():
                email_uid = num.decode()
                result, data = mail.uid('fetch', num, '(RFC822)')
                if result == 'OK':
                    email_internal_date = get_internal_date(data)
                    if email_internal_date:
                        download_attachments(email.message_from_bytes(data[0][1]), email_uid, email_internal_date)
                else:
                    logging.error("Failed to fetch email.")
        else:
            logging.error("Failed to search emails.")
    except Exception as e:
        logging.error("An error occurred: " + str(e))

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
