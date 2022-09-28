# -*- coding: utf-8 -*-

from __future__ import print_function

import os.path, threading

from src.cnbody import clean_body
from src.logs import log
from src.constants import *

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
    ]

def main(npt):
    global count, count2
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)

        #Will only search for unreads, can be changed in constrants
        if npt is None:
            results = service.users().messages().list(userId='me', maxResults=max_result,q=query).execute()
        elif npt == -1:
            return
        else:
            results = service.users().messages().list(userId='me', maxResults=max_result,pageToken=npt,q=query).execute()
        
        log("npt: {}".format(results.get('nextPageToken')))
        
        """creates a thread for each batch(next page token)
        max result by default is set to 100, higher number = less threads, max is 500"""
        try:
            npt = results.get('nextPageToken')
            if npt is not None:
                t1 = threading.Thread(target=main, args=[npt])
                t1.start()
                t1.join()
                #pass
        except Exception as e:
            log(str(e))
            npt = -1

        #Get meta records
        labels = results.get('messages', [])
        if not labels:
            log('No items found.')
            return
        log('items:')
        subject = None
        sender = None

        log("{} items found.".format(len(labels)))
        
        for label in labels:
            
            #Record counts
            count2 += 1

            #Get full record for each meta record
            message = service.users().messages().get(userId="me",id=label['id'],format='full',metadataHeaders=None).execute()

            status = None
            set_archive = 0

            """DEPRECATED by query
            if 'UNREAD' in message['labelIds']:
                status = 'UNREAD'
            else:
                status = 'READ'            
            if status == 'UNREAD':"""
            
            try:
                #snippet = message['snippet'].strip()

                #TODO needs to be optimized, buggy also; will skip emails if error for manual archiving
                #Gets raw body of message
                try:
                    body = message['payload']['parts'][-1]['body']['data']
                except Exception as e:
                    if 'data' in str(e) or str(e) == 'data':
                        #log('data')
                        body = message['payload']['parts'][-1]['parts'][-1]['parts'][-1]['body']['data']
                        log("body: {}".format(body[:5]))
                    elif 'parts' in str(e) or str(e) == 'parts':
                        #log('parts')
                        body = message['payload']['body']['data']
                        #log(message,silent = 1)
                    else:
                        log(str(e),'body')
                        #log(message,silent = 1)
                        return
                    if body is None:
                        return
                
                for i in range (len(message['payload']['headers'])):
                    #subject
                    if message['payload']['headers'][i]['name'] == 'Subject':
                        subject = message['payload']['headers'][i]['value'].strip()
                    
                    """DEPRECATED gets encoding type
                    if message['payload']['headers'][i]['name'] == 'Content-Transfer-Encoding':
                        encoding = message['payload']['headers'][i]['value'].strip()"""

                    #sender
                    if message['payload']['headers'][i]['name'] == 'From':
                        sender = message['payload']['headers'][i]['value'].strip()

                #Whitelist Check
                for i in whitelist_email:
                    if i in sender.casefold():
                        set_archive = 1
                        log("Sender {} found!".format(i))
                        break
                if set_archive == 0:
                    if body is not None:
                        body = clean_body(body)
                    for i in whitelist_key:
                        if i in str(body).casefold() or i in subject.casefold():
                            set_archive = 1
                            log("Key {} found!".format(i))
                            break
                    if set_archive == 0:
                        service.users().threads().modify(
                            userId="me",
                            id=label['id'],
                            body={
                                'removeLabelIds':['UNREAD','INBOX']
                            }).execute()
                        log("Archiving {}\n{}".format(sender,subject))
                        #print(status,'\n',sender,'\n',snippet,'\n',subject,'\n')

                        #Counts archived
                        count += 1
            except Exception as e:
                #log(message,json_data = 1)
                #log(str(e),' - loop')
                pass
        log("{} items has been archived.\n{} total scanned".format(count,count2))
            #main()

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        log(f'An error occurred: {error}')

if __name__ == '__main__':
    main(npt)