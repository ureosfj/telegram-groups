from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError, UserAlreadyParticipantError
from telethon.tl.functions.messages import AddChatUserRequest
import sys
import csv
import traceback
import time
import config

class Scraper():
    def __init__(self):
        #Enter Your 7 Digit Telegram API ID.
        self.api_id =  config.api_id
        #Enter Yor 32 Character API Hash
        self.api_hash = config.api_hash   
        #Enter Your Mobile Number With Country Code.
        self.phone = config.phone   
        self.client = TelegramClient(self.phone, self.api_id, self.api_hash)
        self.groups=[]

    def connect(self):
        #connecting to telegram and checking if you are already authorized. 
        #Otherwise send an OTP code request and ask user to enter the code 
        #they received on their telegram account.
        #After logging in, a .session file will be created. This is a database file which makes your session persistent.
        
        self.client.connect()
        if not self.client.is_user_authorized():
            self.client.send_code_request(self.phone)
            self.client.sign_in(self.phone, input('Enter verification code you received on telegram: '))
           
    def getGroups(self):
        
        chats = []
        last_date = None
        chunk_size = 200
        result = self.client(GetDialogsRequest(
                    offset_date=last_date,
                    offset_id=0,
                    offset_peer=InputPeerEmpty(),
                    limit=chunk_size,
                    hash = 0
                ))
        chats.extend(result.chats)
        
        # create a list of groups
        for chat in chats:
            try:
                if chat.participants_count > 1:
                    self.groups.append(chat)
                else:
                    pass
            except:
                pass





        #choose which group you want to scrape  members:
        for i,g in enumerate(self.groups):
            print(str(i) + '- ' + g.title)
            
     
    def saveFile(self):
        # with this method you will get group all members to csv file that you choosed group.
        
        g_index = input("Please! Enter a Number: ")
        target_group=self.groups[int(g_index)]

        print('Fetching Members...')
        all_participants = []
        all_participants = self.client.get_participants(target_group, aggressive=True)

        print('Saving In file...')
        with open(target_group.title+".csv","w",encoding='UTF-8') as f:#Enter your file name.
            self.csvfile = target_group.title+".csv"
            writer = csv.writer(f,delimiter=",",lineterminator="\n")
            writer.writerow(['username','user id', 'access hash','name','group', 'group id'])
            for user in all_participants:
                if user.username: username= user.username
                else: username= ""

                if user.first_name: first_name= user.first_name
                else: first_name= ""

                if user.last_name: last_name= user.last_name
                else: last_name= ""

                name= (first_name + ' ' + last_name).strip()
                writer.writerow([username,user.id,user.access_hash,name,target_group.title, target_group.id])
        print('Members scraped successfully.......')

    def addUserToGroup(self):
        input_file = self.csvfile
        users = []
        with open(input_file, encoding='UTF-8') as f:
            rows = csv.reader(f,delimiter=",",lineterminator="\n")
            next(rows, None)
            for row in rows:
                user = {}
                user['username'] = row[0]
                try:
                    user['id'] = int(row[1])
                    user['access_hash'] = int(row[2])
                except IndexError:
                    print ('users without id or access_hash')
                users.append(user)

        chats = []
        last_date = None
        chunk_size = 10
        groups=[]

        result = self.client(GetDialogsRequest(
                    offset_date=last_date,
                    offset_id=0,
                    offset_peer=InputPeerEmpty(),
                    limit=chunk_size,
                    hash = 0
                ))
        chats.extend(result.chats)

        for chat in chats:
            try:
                if chat.participants_count >= 1:
                    groups.append(chat)
            except:
                continue

        print('Choose a group to add members:')
        i=0
        for group in groups:
            print(str(i) + '- ' + group.title)
            i+=1

        g_index = input("Enter a Number: ")
        target_group=groups[int(g_index)]
        print('Target Group: ' + groups[int(g_index)].title)


        error_count = 0

        for user in users:
            try:
                print ("Adding {}".format(user['username']))
                self.client(AddChatUserRequest(
                        target_group.id,
                        user['id'],
                        fwd_limit=10  # Allow the user to see the 10 last messages
                    ))
                time.sleep(10)
            except PeerFloodError:
                print("Getting Flood Error from telegram. Script is stopping now. Please try again after some time.")
            except UserPrivacyRestrictedError:
                print("The user's privacy settings do not allow you to do this. Skipping.")
            except UserAlreadyParticipantError:
                print("User is already added to group. Skipping.")
            except:
                traceback.print_exc()
                print("Unexpected Error")
                error_count += 1
                if error_count > 10:
                    sys.exit('too many errors')
                continue

if __name__ == '__main__':
    telegram = Scraper()
    telegram.connect()
    telegram.getGroups()
    telegram.saveFile()
    telegram.addUserToGroup()
    print('Complete: Members added successfully...')