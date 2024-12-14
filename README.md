# Outlook Assistant

## Overview
The Outlook Email Management Assistant enables users to efficiently manage their inboxes by leveraging OpenAI, Retrieval-Augmented Generation (RAG), natural language processing, and automation to streamline email management. It focuses on simplifying email management with features like query-based email interaction, email summarization, categorization, automatic responses to emails, real-time translation, and audio transcription for accessibility. By automating these tasks, this tool will help users save time, improve productivity, reduce email overload, and ensure they never miss crucial communications, all while enhancing accessibility for users with different needs.

## Links

### Application Links
Streamlit: http://3.129.73.242:8501

FastAPI: http://3.129.73.242:5000/docs

### Documentation
Codelabs Link: https://codelabs-preview.appspot.com/?file_id=19F-oNrpfrvN73wmcrOozv6A72wKVv1PLru9mqvLXvps#0


## Attestation and Team Contribution
**WE ATTEST THAT WE HAVEN’T USED ANY OTHER STUDENTS’ WORK IN OUR ASSIGNMENT AND ABIDE BY THE POLICIES LISTED IN THE STUDENT HANDBOOK**

Name | NUID | Contribution% | Work_Contributed
--- | --- | --- | --- |
Sandeep Suresh Kumar | 002841297 | 33% | Endpoints for Microsoft SignIn, Triggering Airflow, Vector Embeddings for mail contents, mail attachment contents, Endpoint for Chatbot, Prompt Agent, Langgraph Implementation to handle multiple agents, CI/CD, Email Categorization
Deepthi Nasika       | 002474582 | 33% | Token responses, Fetching mails with Microsoft Graph API, Processing mail contents, attachment contents into database, Setup Airflow, Endpoints for Mails with folder, RAG agent, Auto Response Agent, Streamlit for connecting with Fastapi endpoints
Gomathy Selvamuthiah | 002410534 | 33% | Processing Mail Attachments, Endpoints for fetching and loading mails, Summarization agent, Streamlit Pages for Mailbox UI, Chatbot Interface, Audio to Text and Text to Audio Translation, Refreshing Mails, Search functionality
Ramy Solanki         | 002816593 | 33% |  Prompt Correction Functionality, JWT tokens, 

## Workflow

## Airflow
The Airflow pipeline streamlines the process of managing email data by automating tasks such as fetching emails, processing attachments, extracting content, and organizing data for efficient retrieval and analysis.
1. Fetches emails using the Microsoft Graph API, authorized with an access token received from the FastAPI application. Extracted email contents are loaded into the Amazon RDS (PostgreSQL) database, following the defined database schema.
2. Receives access token responses from FastAPI, formats the token response, and stores user details along with token information in Amazon RDS.
3. Identifies emails with attachments and sends requests to fetch the attachment files. Downloads the attachments to Amazon S3, organized for scalable storage and accessibility.
4. Extract content from email attachments using tools like PyMuPDF. Stores the extracted content locally for further processing, including creating vector embeddings.
5. Generates vector embeddings for email contents and extracted attachment contents using OpenAI Embeddings.. Stores the embeddings in the Milvus Vector Database for efficient semantic search and retrieval.
6. Uses the on-device Microsoft Phi-3 128k-instruct LLM model to categorize emails intelligently. Stores the categorized information of each email in Amazon RDS for easy filtering and prioritization.


## FastAPI
Acts as the backend service to integrate Milvus, Mulit-agentic architecture with Langgraph, and the Streamlit user interface. The endpoints are:
1. SignIn - Microsoft Authentication
2. AccessToken - Getting access token to make calls to Microsoft Graph API
3. 

## LangGraph (Agents):
Prompt Correction Agent: This agent takes the user’s prompt and passes it through a Large Language Model (LLM), which then rewrites the prompt to improve clarity and specificity for better results. To simplify the process, human approval for the regenerated prompt is skipped.

Retrieval Augmented Generation (RAG) Agent: Instead of relying solely on semantic search, this agent utilizes similarity search for more precise context retrieval, enhancing the relevance of the results generated by the system. Attachments from emails are also taken into consideration when finding similarities.

Summarization Agent: This agent analyzes the content of an entire email thread including attachment data and generates concise, accurate summaries. It extracts key points and relevant information, enabling users to quickly understand the message without reading the entire email thread, improving efficiency, and reducing information overload.

Response Agent: This agent processes the user’s response, generates a well-structured email, identifies the appropriate recipients, and automatically sends the email on behalf of the user.

## Streamlit
The Streamlit application provides an intuitive and interactive interface for users to explore their categorized mail, generate summaries for threads of mail, have a chatbot interaction with their mailbox, and also automate responses through it. It also provides a speech-to-text and text-to-speech feature for people with accessibility issues.

## Architecture Diagrams

### 1. Airflow Pipeline

![Architecture Diagram](https://github.com/BigDataIA-Fall2024-TeamB6/FinalProject/blob/main/diagrams/airflowpipeline.png)

### 2. Core Application
![Architecture Diagram](https://github.com/BigDataIA-Fall2024-TeamB6/FinalProject/blob/main/diagrams/Corepipeline.png)

## Technologies
[![Python](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-000000?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Airflow](https://img.shields.io/badge/Airflow-17B3A8?style=for-the-badge&logo=apacheairflow&logoColor=white)](https://airflow.apache.org/)
[![PyMuPDF](https://img.shields.io/badge/PyMuPDF-333333?style=for-the-badge&logo=python&logoColor=white)](https://pymupdf.readthedocs.io/en/latest/)
[![Amazon RDS](https://img.shields.io/badge/Amazon%20RDS-527FFF?style=for-the-badge&logo=amazonaws&logoColor=white)](https://aws.amazon.com/rds/)
[![Amazon S3](https://img.shields.io/badge/Amazon%20S3-569A31?style=for-the-badge&logo=amazonaws&logoColor=white)](https://aws.amazon.com/s3/)
[![LangChain](https://img.shields.io/badge/LangChain-FF9900?style=for-the-badge&logo=chainlink&logoColor=white)](https://langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-5C2D91?style=for-the-badge&logo=microsoft&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![Boto3](https://img.shields.io/badge/Boto3-569A31?style=for-the-badge&logo=amazonaws&logoColor=white)](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
[![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.crummy.com/software/BeautifulSoup/)
[![Microsoft Graph API](https://img.shields.io/badge/Microsoft%20Graph%20API-0078D4?style=for-the-badge&logo=microsoft&logoColor=white)](https://learn.microsoft.com/en-us/graph/)
[![Microsoft Azure](https://img.shields.io/badge/Microsoft%20Azure-0089D6?style=for-the-badge&logo=microsoftazure&logoColor=white)](https://azure.microsoft.com/)
[![Microsoft Phi-3](https://img.shields.io/badge/Microsoft%20Phi--3-005A9C?style=for-the-badge&logo=microsoft&logoColor=white)](https://www.microsoft.com/)
[![Ollama](https://img.shields.io/badge/Ollama-FF3366?style=for-the-badge&logo=llama&logoColor=white)](https://ollama.ai/)
[![SQL](https://img.shields.io/badge/SQL-4479A1?style=for-the-badge&logo=postgresql&logoColor=white)](https://en.wikipedia.org/wiki/SQL)


## Prerequisites

Software Installations required for the project
1. Python Environment
   A Python environment allows you to create isolated spaces for your Python projects, managing dependencies and versions separately
2. Packages
```bash
pip install -r requirements.txt
```
3. Apache Airflow - Orchestrates the data pipeline, enabling automated workflows for data processing and integration
4. Docker - provides a containerized environment to ensure consistent deployment and scalability of the application
6. Amazon RDS (PostgreSQL) - Manages relational data storage and retrieval with high availability and scalability
8. Milvus Vector Database - Stores and retrieves high-dimensional vector embeddings for efficient similarity searches
9. Amazon S3 - Serves as a scalable storage solution for raw files and processed data in the pipeline
10. Microsoft Graph API - Facilitates seamless interaction with Microsoft 365 services for email management and data access
11. Streamlit - A web application framework used to create a user-friendly interface.

## Project Structure
```
project_root/
│
├── airflow/                      
│   └── dags/
│       ├── auth/
│       │   └── accessToken.py
│       ├── database/
│       │   ├── connectDB.py
│       │   ├── loadtoDB.py
│       │   └── setupTables.py
│       ├── services/            
│       │   ├── extractAttachments.py
│       │   ├── extractFileContents.py
│       │   ├── labeling.py
│       │   ├── logger.py
│       │   ├── processEmailAttachments.py
│       │   ├── processEmailFolders.py
│       │   ├── processEmails.py
│       │   └── vectors.py
│       ├── .env.example
│       ├── airflowpipeline.py
│       └── .gitignore
│
├── diagrams/                   
│
├── fastapi/                    
│   ├── agents/                 
│   │   ├── controller.py
│   │   ├── init.py
│   │   ├── prompt_agent.py
│   │   ├── rag_agent.py
│   │   ├── response_agent.py
│   │   ├── state.py
│   │   ├── summary_agent.py
│   │   └── summary_attachments.py
│   ├── auth/                    
│   │   ├── authenticate.py
│   │   └── init.py
│   ├── database/               
│   │   ├── authstorage.py
│   │   ├── connection.py
│   │   ├── init.py
│   │   └── jobs.py
│   ├── routes/                 
│   │   ├── auth.py
│   │   ├── extras.py
│   │   └── init.py
│   ├── utils/                 
│   │   ├── init.py
│   │   ├── logs.py
│   │   ├── services.py
│   │   └── variables.py
│   ├── .env.example
│   ├── app.py
│   ├── dummy.py
│   └── requirements.txt
│
├── streamlit/                 
│   ├── .env.example
│   ├── .gitignore
│   ├── app.py                 
│   ├── email_service.py       
│   ├── mailbox.py            
│   ├── signin.py             
│   ├── style.css            
│   ├── README.md
│   └── requirements.txt
│
├── Dockerfile                
├── docker-compose.yml       
├── env                     
├── requirements.txt       
└── .gitignore

```


