import os
import json
import chardet
import requests
from bs4 import BeautifulSoup
from unidecode import unidecode

from database.loadtoDB import load_email_info_to_db, insert_or_update_email_links
from database.connectDB import create_connection_to_postgresql, close_connection

# Function to fetch all the emails
def fetch_emails(logger, access_token,  email_id, user_id):
    logger.info("Airflow - services/processEmails.py - fetch_emails() - Fetching mails from Microsoft Graph API")

    fetch_emails_url = os.getenv("FETCH_EMAILS_ENDPOINT")

    if "$top=" not in fetch_emails_url:
        if "?" in fetch_emails_url:
            fetch_emails_url += "&$top=100"
        else:
            fetch_emails_url += "?$top=100"
            
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Prefer": 'outlook.body-content-type="html"',
        "Content-Type": "application/json",
    }

    curr_link_query = """
                    SELECT next_link 
                    FROM email_links 
                    WHERE id = %s AND email = %s
                    LIMIT 1
                    """
    
    conn = create_connection_to_postgresql()
    cursor = conn.cursor()
    cursor.execute(curr_link_query, (user_id, email_id))

    curr_link = cursor.fetchone()
    logger.info(f"Airflow - services/processEmails.py - fetch_emails() - Current link from DB - {curr_link}")
    if curr_link is None:
        current_link = fetch_emails_url
        logger.info(f"Airflow - services/processEmails.py - fetch_emails() - Fetch emails URL - {current_link}")
    else:
        current_link = curr_link[0]
        logger.info(f"Airflow - services/processEmails.py - fetch_emails() - Fetch emails URL - {current_link}")

    close_connection(conn, cursor)

    all_emails = []  # List to store all emails
    next_link = None
    is_current_link_processed = False
    count = 0

    try:
        while current_link:
            logger.info(f"Airflow - services/processEmails.py - fetch_emails() - Fetching emails from link: {current_link}")

            response = requests.get(current_link, headers=headers, timeout=60)
            response.raise_for_status()

            email_data = response.json()
            emails = email_data.get("value", [])
            all_emails.extend(emails)  

            next_link = email_data.get("@odata.nextLink")
            is_current_link_processed = True  # Mark the current link as processed
            count = count + 1

            email_link_data = {
                "id": user_id,
                "email": email_id,
                "current_link": current_link,
                "next_link": next_link,
                "is_current_link_processed": is_current_link_processed
            }

            insert_or_update_email_links(logger, email_link_data)

            logger.info(f"Airflow - services/processEmails.py - fetch_emails() - Processed link: {current_link}")
            logger.info(f"Airflow - services/processEmails.py - fetch_emails() - Fetched {len(emails)} emails. Next link: {next_link}")

            # If there is no next link, break the loop
            if not next_link:
                break
            else:
                current_link = next_link

            if count == 2:
                break

    except requests.exceptions.RequestException as e:
        logger.error(f"Airflow - services/processEmails.py - fetch_emails() - Error while fetching emails: {e}")
    
    logger.info(f"Airflow - services/processEmails.py - fetch_emails() - Completed fetching all emails. Total emails: {len(all_emails)}")
    return all_emails



# Function to process email JSON contents and format them
def decode_content(content):
    return unidecode(content)

def clean_text(text):
    return text.replace('\n', ' ').replace('\r', '').strip()

def extract_text_and_links(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Replace <a> tags with their text and link inline (e.g., "Text (URL)")
    for a_tag in soup.find_all('a', href=True):
        link_text = a_tag.get_text(strip=True)
        if a_tag.get('originalsrc', None):
            href = a_tag['originalsrc']
        else:
            href = a_tag['href']
        a_tag.replace_with(f"{link_text} ({href})")

    # Extract the cleaned text
    return soup.get_text(separator='\n', strip=True)


def process_email_response(logger, emails):
    logger.info(f"Airflow - services/processEmails.py - process_email_response() - Processing mail responses")

    formatted_email_data = []

    logger.info(f"Airflow - services/processEmails.py - process_email_response() - Parsing through each mail")
    for email in emails:
        formatted_email = {}

        for key, value in email.items():
            if key == "body":
                body_content = value.get("content", "")
                cleaned_content = extract_text_and_links(body_content)

                formatted_email[key] = {
                    "contentType": value.get("contentType", "unknown"),
                    "content": clean_text(decode_content(cleaned_content))
                }

            elif isinstance(value, dict):
                # Process nested dictionaries (e.g., sender, from, toRecipients)
                formatted_email[key] = {
                    sub_key: clean_text(decode_content(str(sub_value)))
                    for sub_key, sub_value in value.items()
                }
            elif isinstance(value, list):
                # Process lists (e.g., recipients)
                formatted_email[key] = [
                    {
                        sub_key: clean_text(decode_content(str(sub_value)))
                        for sub_key, sub_value in item.items()
                    }
                    if isinstance(item, dict) else clean_text(decode_content(str(item)))
                    for item in value
                ]
            else:
                # Process other key-value pairs
                formatted_email[key] = clean_text(decode_content(str(value)))

        formatted_email_data.append(formatted_email)

    logger.info(f"Airflow - services/processEmails.py - process_email_response() - Data formatted successfully")
    return formatted_email_data


# Function to save mails to JSON file
def save_emails_to_json_file(logger, email_data, file_name):
    logger.info(f"Airflow - services/processEmails.py - save_emails_to_json_file() - Saving mails to JSON file {file_name}")
    try:
        with open(file_name, "w") as json_file:
            json.dump(email_data, json_file, indent=4)
        logger.info(f"Airflow - services/processEmails.py - save_emails_to_json_file() - Email data saved to {file_name}")
    except Exception as e:
        logger.error(f"Airflow - services/processEmails.py - save_emails_to_json_file() - Error saving email data to JSON file: {e}")


def process_emails(logger, access_token, user_email, email_id, user_id):
    logger.info(f"Airflow - services/processEmails.py - process_emails() - Processing emails")

    logger.info(f"Airflow - services/processEmails.py - process_emails() - Fetching emails with access token")
    mail_responses = fetch_emails(logger, access_token, email_id, user_id)

    logger.info(f"Airflow - services/processEmails.py - process_emails() - Processing mail responses to format contents of emails")
    formatted_mail_responses = process_email_response(logger, mail_responses)
    save_emails_to_json_file(logger, formatted_mail_responses, "mail_responses.json")

    logger.info(f"Airflow - services/processEmails.py - process_emails() - Loading mail data into PostgreSQL database")
    load_email_info_to_db(logger, formatted_mail_responses, user_email)