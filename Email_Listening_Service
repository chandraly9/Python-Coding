import imaplib
import email
import os
import logging
import time  # Import the time module
from datetime import datetime, timedelta
from email.utils import parsedate_tz, mktime_tz

# Setup logging
logging.basicConfig(filename='/Users/satish.loyapally/Downloads/emaillogfile_v2.log',  # Update with your actual log file path
                    filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

# Gmail credentials and server details
imap_host = 'imap.gmail.com'
imap_user = 'schandraly@gmail.com'  # Your Gmail address
imap_pass = 'adwytpkzzvmgybck'  # Your app password

# Function to download attachments from a message
def download_attachments(message, download_folder="/Users/satish.loyapally/Downloads"):  # Update with your actual download path
    for part in message.walk():
        if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
            continue
        filename = part.get_filename()
        if filename:
            filepath = os.path.join(download_folder, filename)
            with open(filepath, 'wb') as f:
                f.write(part.get_payload(decode=True))
            logging.info(f'Attachment {filename} saved to {filepath}')

# Connect to the Gmail server using IMAP over SSL
try:
    mail = imaplib.IMAP4_SSL(imap_host)
    mail.login(imap_user, imap_pass)
    mail.select('inbox')
    logging.info("Logged in and selected inbox successfully.")
except Exception as e:
    logging.error("Error connecting to email server: " + str(e))
    exit()

# Search for new emails with subject "Invoice"
while True:
    try:
        # Search for emails with subject "Invoice" received since the last run
        since_date = (datetime.now() - timedelta(minutes=1)).strftime("%d-%b-%Y")
        result, data = mail.uid('search', None, f'(SINCE {since_date})', 'HEADER Subject "Invoice"')
        if result == 'OK':
            for num in data[0].split():
                result, data = mail.uid('fetch', num, '(RFC822)')
                if result == 'OK':
                    email_message = email.message_from_bytes(data[0][1])
                    download_attachments(email_message)
                else:
                    logging.error("Failed to fetch email.")
        else:
            logging.error("Failed to search emails.")
    except Exception as e:
        logging.error("An error occurred: " + str(e))
    
    time.sleep(60)  # Check every 1 minute
