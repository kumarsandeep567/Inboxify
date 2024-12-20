from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator

import os
from dotenv import load_dotenv
from services.logger import start_logger
from auth.accessToken import get_token_response, format_token_response
from database.setupTables import create_tables_in_db
from database.loadtoDB import load_users_tokendata_to_db, fetch_new_job, update_job_timestamp
from services.processEmails import process_emails
from services.processEmailAttachments import process_emails_with_attachments
from services.extractAttachments import extract_contents_from_attachments
from services.processEmailFolders import get_email_folders

# Initialize logger
logger = start_logger()

load_dotenv()

def get_and_format_token(**context):
    """Get and format authentication token"""
    
    try:
        received_token_dict = None
        tokens_present = False

        # Check if dag_run was passed to our Airflow logic
        if context.get("dag_run", None):
            logger.info("Task: get_and_format_token - Attempting to fetch tokens from context")
            
            # Safety check: The '.conf' value can be missing
            try:
                received_token_dict = context['dag_run'].conf if context['dag_run'].conf else None
            
            except Exception as e:
                logger.error("Task: get_and_format_token - Context '.conf' is missing (See exception below)")
                logger.error(e)

        # If the above logic successfully fetched non-null values
        if received_token_dict:

            # Sometimes, context['dag_run'].conf may be available, but does not 
            # contain the data we are looking for

            try:
                if received_token_dict.get("access_token", None):
                    tokens_present = True
            
            except Exception as e:
                logger.error("Task: get_and_format_token - Token dictionary is non-null, but still an exception occured (See exception below)")
                logger.error(e)

        # If we actually found the data we are looking for
        if tokens_present:
            token_response = {
                "message" : received_token_dict
            }
            
            logger.info(f"RECEIVED DATA {context['dag_run'].conf}")

        else:
            logger.info("Task: get_and_format_token - Fetching endpoint from environment variable")
            
            endpoint = os.getenv("ENDPOINT")

            if not endpoint:
                raise ValueError("Endpoint environment variable seems to be missing")
            
            logger.info("Task: get_and_format_token - Fetching refresh tokens from database")
            refresh_token = fetch_new_job(logger)

            if refresh_token is None:
                raise ValueError("No refresh tokens found from the database")
        
            # Get token response
            token_response = get_token_response(logger, endpoint, refresh_token)
            logger.info(f"Task: get_and_format_token - Token Response received")
        
        # Format token response
        formatted_token = format_token_response(logger, token_response)
        logger.info("Task: get_and_format_token - Token Response formatted")
        
        # Store formatted token in XCom for downstream tasks
        context['task_instance'].xcom_push(key='formatted_token', value=formatted_token)
        return formatted_token

    except Exception as e:
        context['task_instance'].xcom_push(key='formatted_token', value=None)
        logger.error(f"Task: get_and_format_token - Error in get_and_format_token: {e}")
        raise

def setup_database(**context):
    """Setup database tables if not already created"""
    
    try:
        logger.info("Task: setup_database - Starting database setup")
        
        # Get the task instance
        task_instance = context['task_instance']
        
        # Try to get the DB_SETUP state from XCom
        db_setup = task_instance.xcom_pull(key='DB_SETUP', include_prior_dates=True)
        
        # If DB_SETUP is None or False, we need to create tables
        if not db_setup:
            logger.info("Task: setup_database - Database not setup yet. Creating tables...")
            
            # Create tables
            create_tables_in_db(logger)
            
            # Set DB_SETUP to True in XCom
            task_instance.xcom_push(key='DB_SETUP', value=True)
            logger.info("Task: setup_database - Database tables created successfully and DB_SETUP set to True")
            
        else:
            logger.info("Task: setup_database - Database tables already exist, skipping table creation")

    except Exception as e:
        logger.error(f"Task: setup_database - Error in setup_database: {e}")
        context['task_instance'].xcom_push(key='DB_SETUP', value=False)
        raise

def process_user_token(**context):
    """Process user token and load to database"""
    
    try:
        logger.info("Task: process_user_token - Processing user token")
        
        # Get formatted token from previous task
        formatted_token = context['task_instance'].xcom_pull(task_ids='get_token_task', key='formatted_token')

        if formatted_token is None:
            raise ValueError("formatted_token contains None instead of a dictionary in process_user_token")
        
        # Load user token data to database
        user_email = load_users_tokendata_to_db(logger, formatted_token)
        logger.info("Task: process_user_token - User token data loaded to database")
        
        # Store user email in XCom for downstream tasks
        context['task_instance'].xcom_push(key='user_email', value=user_email)
        return user_email
    
    except Exception as e:
        logger.error(f"Task: process_user_token - Error in process_user_token: {e}")
        context['task_instance'].xcom_push(key='user_email', value=None)
        raise


def process_email_folders(**context):
    """Process email folders and save to database"""
    try:
        logger.info("Task: process_email_folders - Processing email folders")
        
        # Get the task instance
        task_instance = context['task_instance']
        
        # Try to get the FOLDERS_PROCESSED state from XCom
        folders_processed = task_instance.xcom_pull(key='FOLDERS_PROCESSED', include_prior_dates=True)
        
        if not folders_processed:
            # Get access token from previous task
            formatted_token = context['task_instance'].xcom_pull(task_ids='get_token_task', key='formatted_token')

            if formatted_token is None:
                raise ValueError("formatted_token contains None instead of a dictionary in process_email_folders")

            # Process email folders
            get_email_folders(logger, formatted_token['access_token'])
            logger.info("Task: process_email_folders - Email folders processed successfully")
            
            # Set FOLDERS_PROCESSED to True in XCom
            task_instance.xcom_push(key='FOLDERS_PROCESSED', value=True)
            logger.info("Task: process_email_folders - FOLDERS_PROCESSED set to True")
        else:
            logger.info("Task: process_email_folders - Email folders already processed, skipping folder creation")
    
    except Exception as e:
        logger.error(f"Task: process_email_folders - Error in process_email_folders: {e}")
        # Make sure to set FOLDERS_PROCESSED to False if there's an error
        context['task_instance'].xcom_push(key='FOLDERS_PROCESSED', value=False)
        raise


def process_email_data(**context):
    """Process email data"""
    
    try:
        logger.info("Task: process_email_data - Processing emails")
        
        # Get necessary data from previous tasks
        formatted_token = context['task_instance'].xcom_pull(task_ids='get_token_task', key='formatted_token')
        user_email = context['task_instance'].xcom_pull(task_ids='process_token_task', key='user_email')

        # Using the checking condition "if formatted_token and user_email"
        # will make it difficult to identify which value was None
        # To simplify, keep them separate
        
        if formatted_token is None:
            raise ValueError("formatted_token contains None instead of a dictionary in process_email_data")
        
        if user_email is None:
            raise ValueError("user_email contains None instead of a string in process_email_data")
        
        # Process emails
        process_emails(
            logger,
            formatted_token['access_token'],
            user_email,
            formatted_token['email'],
            formatted_token['id']
        )
        logger.info("Task: process_email_data - Emails processed successfully")
    
    except Exception as e:
        logger.error(f"Task: process_email_data - Error in process_email_data: {e}")
        raise

def process_attachments(**context):
    """Process email attachments"""
    
    try:
        logger.info("Task: process_attachments - Processing email attachments")
        
        # Get necessary data from previous tasks
        formatted_token = context['task_instance'].xcom_pull(task_ids='get_token_task', key='formatted_token')

        if formatted_token is None:
            raise ValueError("formatted_token contains None instead of a dictionary in process_attachments")

        s3_bucket_name = os.getenv("S3_BUCKET_NAME")
        
        # Process email attachments
        process_emails_with_attachments(
            logger,
            formatted_token['access_token'],
            s3_bucket_name
        )
        logger.info("Task: process_attachments - Email attachments processed successfully")
    
    except Exception as e:
        logger.error(f"Task: process_attachments - Error in process_attachments: {e}")
        raise

def extract_attachment_contents(**context):
    """Extract contents from email attachments"""
    
    try:
        logger.info("Task: extract_attachment_contents - Extracting contents from attachments")
        
        extract_contents_from_attachments(logger)
        logger.info("Task: extract_attachment_contents - Attachment contents extracted successfully")
    
    except Exception as e:
        logger.error(f"Task: extract_attachment_contents - Error in extract_attachment_contents: {e}")
        raise

def update_job(**context):
    """ Update the job's updated_at time in the database """

    try:
        logger.info("Task: update_job - Updating job's updated_at timestamp")
        
        # Get necessary data from previous tasks
        formatted_token = context['task_instance'].xcom_pull(task_ids='get_token_task', key='formatted_token')

        if formatted_token is None:
            raise ValueError("formatted_token contains None instead of a dictionary in update_job")
        
        update_status = update_job_timestamp(logger, formatted_token['email'])
        if not update_status:
            raise ValueError(f"Failed to update status for email {formatted_token['email']} in the queued_jobs table")
        
    except Exception as e:
        logger.error(f"Task: update_job - Error in update_job: {e}")
        raise


# Default arguments for our DAG
default_args = {
    'owner'            : 'airflow',
    'depends_on_past'  : False,
    'email_on_failure' : True,
    'email_on_retry'   : False,
    'retries'          : 1,
    'retry_delay'      : timedelta(minutes=5),
    'start_date'       : datetime(2024, 1, 1),
}

# Create the DAG
with DAG(
    'outlook_pipeline',
    default_args      = default_args,
    description       = 'Pipeline to process emails and their attachments',
    schedule_interval = timedelta(hours=1),
    catchup           = False,
    tags              = ['email', 'processing']
) as dag:

    # Define tasks
    setup_db_task = PythonOperator(
        task_id='setup_db_task',
        python_callable=setup_database,
        provide_context=True,
        dag=dag,
    )

    get_token_task = PythonOperator(
        task_id='get_token_task',
        python_callable=get_and_format_token,
        provide_context=True,
        dag=dag,
    )

    process_token_task = PythonOperator(
        task_id='process_token_task',
        python_callable=process_user_token,
        provide_context=True,
        dag=dag,
    )

    process_folders_task = PythonOperator(
        task_id='process_folders_task',
        python_callable=process_email_folders,
        provide_context=True,
        trigger_rule='all_success',
        dag=dag,
    )

    process_emails_task = PythonOperator(
        task_id='process_emails_task',
        python_callable=process_email_data,
        provide_context=True,
        dag=dag,
    )

    process_attachments_task = PythonOperator(
        task_id='process_attachments_task',
        python_callable=process_attachments,
        provide_context=True,
        dag=dag,
    )

    extract_contents_task = PythonOperator(
        task_id='extract_contents_task',
        python_callable=extract_attachment_contents,
        provide_context=True,
        dag=dag,
    )

    update_job_task = PythonOperator(
        task_id='update_job_task',
        python_callable=update_job,
        provide_context=True,
        dag=dag,
    )

    # Task dependencies
    setup_db_task >> get_token_task >> process_token_task >> process_folders_task >> process_emails_task >> process_attachments_task >> extract_contents_task >> update_job_task