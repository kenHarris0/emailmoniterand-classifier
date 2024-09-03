import os
import base64
import time
import json
from googleapiclient import errors
from gmail_auth import authenticate_gmail

categories = {
    'tech_reports': ['tech', 'report', 'analysis', 'technical', 'specifications', 'evaluation'],
    'financial_docs': ['finance', 'statement', 'audit', 'invoice', 'financial', 'budget', 'expense', 'receipt'],
    'research_papers': ['research', 'paper', 'study', 'thesis', 'dissertation', 'experiment', 'journal'],
    'legal_documents': ['contract', 'agreement', 'legal', 'law', 'policy', 'terms', 'conditions'],
    'marketing_materials': ['marketing', 'campaign', 'brochure', 'advertisement', 'promo', 'promotion', 'flyer'],
    'human_resources': ['resume', 'cv', 'application', 'interview', 'hiring', 'employee', 'job'],
    'healthcare_documents': ['medical', 'health', 'prescription', 'report', 'diagnosis', 'treatment', 'patient'],
    'education_materials': ['assignment', 'course', 'syllabus', 'lecture', 'notes', 'education', 'training', 'tutorial'],
    'business_documents': ['business', 'plan', 'proposal', 'strategy', 'report', 'meeting', 'minutes'],
    'project_documents': ['project', 'plan', 'proposal', 'timeline', 'report', 'status', 'deliverables', 'milestones']
}


def list_messages_matching_query(service, user_id, query=''):
    try:
        response = service.users().messages().list(userId=user_id, q=query).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])
        return messages
    except errors.HttpError as error:
        print(f'An error occurred: {error}')
        return []

def classify_document(text):
    
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in text.lower():
                return category
    return 'other'  
#mixtrel

def classify_and_store_attachment(service, user_id, msg_id, store_dir):
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id).execute()
        for part in message['payload']['parts']:
            if part['filename'] and part['filename'].endswith('.pdf'):
                if 'data' in part['body']:
                    data = part['body']['data']
                else:
                    att_id = part['body']['attachmentId']
                    att = service.users().messages().attachments().get(userId=user_id, messageId=msg_id, id=att_id).execute()
                    data = att['data']
                file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
                
                ################ Ensure the directory exists ######################
                filename = part['filename']
                path = os.path.join(store_dir, filename)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                
                with open(path, 'wb') as f:
                    f.write(file_data)
                print(f"Attachment {filename} saved to {path}")

              
                text_content = extract_text_from_pdf(path)
                classification = classify_document(text_content)

                print(f"File {filename} classified as: {classification}")

    except errors.HttpError as error:
        print(f'An error occurred: {error}')

def extract_text_from_pdf(pdf_path):
   
    import fitz
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def monitor_inbox(service, store_dir):
    while True:
        messages = list_messages_matching_query(service, 'me', 'has:attachment')
        if messages:
            for msg in messages:
                classify_and_store_attachment(service, 'me', msg['id'], store_dir)
        time.sleep(60) 

if __name__ == '__main__':
    service = authenticate_gmail()
    store_dir = './pdf_attachments'
    os.makedirs(store_dir, exist_ok=True)
    monitor_inbox(service, store_dir)
