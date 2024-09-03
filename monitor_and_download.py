import os
import base64
import time
from googleapiclient import errors
from gmail_auth import authenticate_gmail

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

def save_attachment(service, user_id, msg_id, store_dir):
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
                
                # ###################### Ensure the directory exists ####################################
                filename = part['filename']
                path = os.path.join(store_dir, filename)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                
                with open(path, 'wb') as f:
                    f.write(file_data)
                print(f"Attachment {filename} saved to {path}")
    except errors.HttpError as error:
        print(f'An error occurred: {error}')

def monitor_inbox(service, store_dir):
    while True:
        messages = list_messages_matching_query(service, 'me', 'has:attachment')
        if messages:
            for msg in messages:
                save_attachment(service, 'me', msg['id'], store_dir)
        time.sleep(60)  

if __name__ == '__main__':
    service = authenticate_gmail()
    store_dir = './pdf_attachments'
    os.makedirs(store_dir, exist_ok=True)
    monitor_inbox(service, store_dir)
