import requests
import datetime
from urllib.parse import urlencode
import base64
import json

class SpotifyAPI(object):
    access_token = None
    access_token_expires = datetime.datetime.now()
    access_token_did_expire = True
    client_id = None
    client_secret = None
    token_url = "https://accounts.spotify.com/api/token"
    
    def __init__(self, client_id, client_secret, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_id = client_id
        self.client_secret = client_secret

    def get_client_credentials(self):
        """
        Returns a base64 encoded string
        """
        client_id = self.client_id
        client_secret = self.client_secret
        if client_secret == None or client_id == None:
            raise Exception("You must set client_id and client_secret")
        client_creds = f"{client_id}:{client_secret}"
        client_creds_b64 = base64.b64encode(client_creds.encode())
        return client_creds_b64.decode()
    
    def get_token_headers(self):
        client_creds_b64 = self.get_client_credentials()
        return {
            "Authorization": f"Basic {client_creds_b64}"
        }
    
    def get_token_data(self):
        return {
            "grant_type": "client_credentials"
        } 
    
    def perform_auth(self):
        token_url = self.token_url
        token_data = self.get_token_data()
        token_headers = self.get_token_headers()
        r = requests.post(token_url, data=token_data, headers=token_headers)
        if r.status_code not in range(200, 299):
            raise Exception("Could not authenticate client.")
            #return False
        data = r.json()
        now = datetime.datetime.now()
        access_token = data['access_token']
        expires_in = data['expires_in'] # seconds
        expires = now + datetime.timedelta(seconds=expires_in)
        self.access_token = access_token
        self.access_token_expires = expires
        self.access_token_did_expire = expires < now
        return True
    
    def get_access_token(self):
        token = self.access_token
        expires = self.access_token_expires
        now = datetime.datetime.now()
        if expires < now:
            self.perform_auth()
            return self.get_access_token()
        elif token == None:
            self.perform_auth()
            return self.get_access_token() 
        return token

    def get_resource_header(self):
        access_token = self.get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        return headers

    def get_resource(self, lookup_id, resource_type='albums', version='v1'):
        endpoint = f"https://api.spotify.com/{version}/{resource_type}/{lookup_id}"
        headers = self.get_resource_header()
        r = requests.get(endpoint, headers=headers)
        if r.status_code not in range(200, 299):
            return {}
        return r.json()
    
    def getUserPlist(self, u_id):
        #endpoint = f"https://api.spotify.com/{u_id}/playlists"
        endpoint = f"https://api.spotify.com/v1/users/{u_id}/playlists"
        headers = self.get_resource_header()
        r = requests.get(endpoint, headers=headers)
        if r.status_code not in range(200, 299):
            return {}
        return r.json()
    
    def get_genre(self):
        # To try the genre seed 
        headers = self.get_resource_header()
        endpoint = f"https://api.spotify.com/v1/recommendations/available-genre-seeds"
        r = requests.get(endpoint, headers=headers)
        #print(r.status_code)
        if r.status_code not in range(200, 299):
            return {}
        return r.json()
    
    def recommend_track(self, artists, genres, tracks):
        #access_token = self.get_access_token()
        headers = self.get_resource_header()
        endpoint = "https://api.spotify.com/v1/recommendations"
        data = urlencode({"seed_artists": artists, "seed_genres": genres, "seed_tracks" : tracks, "limit": 10})

        lookup_url = f"{endpoint}?{data}"
        r = requests.get(lookup_url, headers=headers)
        if r.status_code not in range(200, 299):  
            return r.status_code
        return r.json()
    
    def get_album(self, _id):
        return self.get_resource(_id, resource_type='albums')
    
    def get_artist(self, _id):
        return self.get_resource(_id, resource_type='artists')
    
    def get_track(self, _id):
        return self.get_resource(_id, resource_type='tracks')
    
    def get_reccomended_songs(self, limit=20, seed_artists='', seed_tracks='', seed_genres='', max_instrumentalness=0.45, access_token1 = ''):  # reccomendations API
        #access_token = self.get_access_token()
        headers = self.get_resource_header()
        endpoint_url = "https://api.spotify.com/v1/recommendations?"
        all_recs = []
        self.limit = limit
        self.seed_artists = seed_artists
        self.seed_tracks = seed_tracks
        self.seed_genres = seed_genres
        self.max_instrumentalness = max_instrumentalness
        self.access_token = access_token1

        # API query plus some additions
        query = f'{endpoint_url}limit={limit}&max_instrumentalness={max_instrumentalness}'
        query += f'&seed_artists={seed_artists}'
        query += f'&seed_genres={seed_genres}'
        query += f'&seed_tracks={seed_tracks}'
        response = requests.get(query, headers={"Content-type": "application/json", "Authorization": f"Bearer {access_token1}"})
        json_response = response.json()

        track_url = []
        #print(json_response)
        if response:
            print("Recommended songs:")
            for i, j in enumerate(json_response['tracks']):
                #print(i, j)
                track_name = j['name']
                artist_name = j['artists'][0]['name']
                link = j['external_urls']['spotify'].split('/') #track url 
                track_id = link[-1]
                track_url.append(track_id)
                

                print(f"{i+1}) \"{j['name']}\" by {j['artists'][0]['name']}")
                reccs = [track_name, artist_name, link]
                all_recs.append(reccs)
        
        return track_url
    
    def search_art(self, query, search_type='artist'):
        headers = self.get_resource_header()
        endpoint = "https://api.spotify.com/v1/search"
        self.search_type = 'artist'
        data = urlencode({"q": query, "type": search_type.lower()})
        lookup_url = f"{endpoint}?{data}"
        
        response = requests.get(lookup_url, headers=headers)
        json_response = response.json()
        art_lists = []
    
        if response:
            for i in json_response['artists']['items']:
                art_urls = i['external_urls']
                art_lists.append(art_urls)
            id_a = art_lists[0] 
            split_id = id_a['spotify'].split("/")
            art_id = split_id[-1]
            
        return art_id
    
    def search_track(self, query, search_type='track'):
        headers = self.get_resource_header()
        endpoint = "https://api.spotify.com/v1/search"
        self.search_type = 'track'
        data = urlencode({"q": query, "type": search_type.lower()})
        lookup_url = f"{endpoint}?{data}"
        
        response = requests.get(lookup_url, headers=headers)
        json_response = response.json()
        track_listsID = []
    
        if response:
            for i in json_response['tracks']['items']:
                track_listsID.append(i['id'])
        
            target_trackID = track_listsID[0]
               
        return target_trackID
    
    def createNewPlay(self, u_id, Pname, desc, access_token1 = ''):
        endpoint = f"https://api.spotify.com/v1/users/{u_id}/playlists"
        headers = self.get_resource_header()
        self.u_id = u_id
        self.Pname = Pname
        self.desc = desc
        self.access_token = access_token1

        data = json.dumps({
            "name": Pname,
            "description": desc,
            "public": True
        })
        
        # API query plus some additions
        #query = f'{endpoint}' 
        response = requests.post(endpoint, headers={
                               "data": data ,"Content-type": "application/json", "Authorization": f"Bearer {access_token1}"})
        json_response = response.json()
        
        
        #r = requests.post(endpoint, headers=headers)
        #if r.status_code not in range(200, 299):
        #    return {r.status_code}
        
        return json_response
    
    def get_User_pro(self):
        headers = self.get_resource_header()
        endpoint = "https://api.spotify.com/v1/me"
        
        #data = urlencode({"q": query, "type": search_type.lower()})
        lookup_url = f"{endpoint}"
        
        response = requests.get(lookup_url, headers=headers)
        json_response = response.json()    
        return json_response
    
#############################################################
#Funtion for recommend custom activity class with genres
def genre_type(activity_class):
    genre = ""
    if activity_class == "Biking":
        genre = "pop, rock, hip-hop, heavy-metal"
    elif activity_class == "Eating":
        genre = "jazz, r-n-b, pop"
    elif activity_class == "Playing Instrument":
        genre = "classical, jazz, piano"
    elif activity_class == "Walking":
        genre = 'folk, country, techno'
    else:
        genre = "world-music"
    return genre

