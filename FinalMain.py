import requests
import base64
import json
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import urllib.parse
from urllib.parse import urlencode
import time

client_id = '1906ff01f5ee4766aa640a9fbb4e6207' # client_id
client_secret = '627fb88c2eac4d288795e96b180603a4' # client_secret 

class GetAuthCode:
    def __init__(self, c_id, c_secret): # passing in cliend_id and client_secret
        # Selenium Inititalization
        chromedriver_path = 'C:/PROGRAMMING/VSCode/Practice/chromedriver.exe'
        self.driver = selenium.webdriver.Chrome(chromedriver_path)

        # Spotify API Credentials        
        self.client_id = c_id
        self.client_secret = c_secret
        self.redirect_uri = 'https://google.com/'
        
        self.spot_login_username = None
        self.spot_login_pass = None

        self.auth_code_url = None
        self.auth_code_data = None
        self.auth_url = None
        self.auth_response = None
        self.code = None
        self.auth_response_url = None

        # Spotify Login Credentials
    def GetSpotCredentials(self):
        self.spot_login_username = input('Enter your spotify username/email id: ')
        self.spot_login_pass = input('Enter your spotify password: ')   

        # Sending Request For Authorization Code
    def Request_Auth_code(self):
        self.GetSpotCredentials()
        self.auth_code_url = 'https://accounts.spotify.com/authorize'
        self.auth_code_data = urllib.parse.urlencode({
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': 'playlist-modify-public user-library-read',
            'show_dialog': 'false'
        })
        self.auth_url = f"{self.auth_code_url}?{self.auth_code_data}"
        self.auth_response = requests.get(self.auth_url)
        
        # Getting The Auth Code From redirect_uri
    def Get_Auth_Code(self):
        self.Request_Auth_code()
        self.driver.get(self.auth_response.url)
        time.sleep(3)
        self.driver.find_element_by_xpath('/html/body/div[1]/div[2]/div/form/div[1]/div/input').send_keys(self.spot_login_username)
        self.driver.find_element_by_xpath('/html/body/div[1]/div[2]/div/form/div[2]/div/input').send_keys(self.spot_login_pass + Keys.ENTER)
        time.sleep(3)

        # Extracting The Auth Code From The Redirect_Uri
        parsed_url = urllib.parse.splitquery(self.driver.current_url) # creates a tuple of all query parameters

        for element in parsed_url:
            element = str(element)
            self.code = element[5:]
        return self.code
        
        
class GetToken(GetAuthCode):
    def __init__(self, c_id, c_secret):
        super().__init__(c_id, c_secret)
        self.codee = None
        self.client_creds = f"{self.client_id}:{self.client_secret}"
        self.client_creds_b64 = base64.b64encode(self.client_creds.encode())
        self.token_req_url = 'https://accounts.spotify.com/api/token'
        self.token_req_body = None
        self.headers = None

    def Request_Token(self):
        self.codee = self.Get_Auth_Code()
        self.token_req_body = urllib.parse.urlencode({
            'grant_type': 'authorization_code',
            'code': self.codee,
            'redirect_uri': self.redirect_uri
        })  
        self.headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f"Basic {self.client_creds_b64.decode()}"
        }
        self.token_req = requests.post(self.token_req_url, params=self.token_req_body ,headers=self.headers)
        
        if self.token_req.status_code in range(200, 299):
            return self.token_req.json()['access_token']
        else:
            print('Token Request Unsuccessful')
            exit(1)

# Create Playlist

class CreatePlaylist(GetToken):
    def __init__(self, c_id, c_secret):
        super().__init__(c_id, c_secret)
        self.pl_url1 = None
        self.pl_url2 = None
        self.user_id = None
        self.user_id_url = None
        self.flag = 0
        self.created_playlist_id = None
        self.access_token = self.Request_Token()
        self.pl_name = input('Enter playlist name: ')

        # fetching user id using selenium
        self.user_id_url = 'https://accounts.spotify.com/en/login/?continue=https:%2F%2Fwww.spotify.com%2Fapi%2Fgrowth%2Fl2l-redirect&_locale=en-IN'
        self.driver.get(self.user_id_url)
        time.sleep(3)
        self.driver.execute_script("window.scrollTo(0, 400)")
        time.sleep(2)
        self.user_id = self.driver.find_element_by_xpath('/html/body/div[1]/div[4]/div/div[2]/div[3]/div[2]/div/article[1]/section/table/tbody/tr[1]/td[2]')
        
        #joining pl_url by formatting user id into it
        self.pl_url1 = 'https://api.spotify.com/v1/users/'
        self.pl_url2 = '/playlists'
        self.user_id = self.user_id.text
        self.pl_url = f"{self.pl_url1}{self.user_id}{self.pl_url2}"
        
        self.headers = {
            'Authorization': f"Bearer {self.access_token}",
            'Content-Type': 'application/json',
        }
        self.json = {
            'name': self.pl_name
        }
        self.pl_response = None

    def SendCreatePlaylistRequest(self):
        if self.flag == 0:
            self.pl_response = requests.post(self.pl_url, headers=self.headers, json=self.json)
            self.created_playlist_id = self.pl_response.json()['id']
            # print(self.created_playlist_id)        
            if self.pl_response.status_code in range(200, 299):
                self.flag = 1
                return self.created_playlist_id
            else:
                print('Playlist Creation Failed')
                exit(1)
        if self.flag == 1:
            return self.access_token

CPL = CreatePlaylist(client_id, client_secret)
created_playlist_id = CPL.SendCreatePlaylistRequest()
access_token = CPL.SendCreatePlaylistRequest()

# Get Saved Tracks
st_list = []
st_url = 'https://api.spotify.com/v1/me/tracks'
offv = 0
# Getting total
st_query = urlencode({
        'limit': 50,
        'offset': offv
    })
st_headers = {
    'Authorization': f"Bearer {access_token}"
}
st_real_url = f"{st_url}?{st_query}"
st_response =  requests.get(st_real_url, headers=st_headers)
total = st_response.json()['total']

# getting saved tracks and adding them till no more saved tracks available
while offv < total:                                                 
    st_query = urlencode({
        'limit': 50,
        'offset': offv
    })
    st_headers = {
        'Authorization': f"Bearer {access_token}"
    }
    st_real_url = f"{st_url}?{st_query}"
    st_response =  requests.get(st_real_url, headers=st_headers)
    for track_id in st_response.json()['items']:
        st_list.append(track_id['track']['uri'])

    # Adding Item To Playlist
    gt_url1 = 'https://api.spotify.com/v1/playlists/'
    gt_url2 = '/tracks'
    created_playlist_id = created_playlist_id
    gt_url = f"{gt_url1}{created_playlist_id}{gt_url2}"
    gt_headers = {
        'Authorization': f"Bearer {access_token}",
        'Content-Type': 'application/json'
    }
    gt_json = {
        'uris': st_list
    }
    gt_response = requests.post(gt_url, headers=gt_headers, json=gt_json)
    final_response_variable = 0
    if gt_response.status_code in range(200, 299):
        final_response_variable = 1
    offv += 50
    st_list.clear()

# final message
if final_response_variable == 1:
        print('All songs from liked songs successfully added to playlist!')
