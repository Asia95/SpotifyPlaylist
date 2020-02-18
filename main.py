# -*- coding: utf-8 -*-
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import youtube_dl
import json
import requests
from spotify_auth import spotify_user_id, OATH_TOKEN

scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

# Disable OAuthlib's HTTPS verification when running locally.
# *DO NOT* leave this option enabled in production.
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

api_service_name = "youtube"
api_version = "v3"
client_secrets_file = "client_secret_file.json"

# Create Spotify Playlist
request_body = json.dumps({"name": "Youtube Liked Videos"})
query = "https://api.spotify.com/v1/users/{}/playlists".format(spotify_user_id)
response = requests.post(
    query,
    data=request_body,
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(OATH_TOKEN)
    }
)
response_json = response.json()
spotify_playlist_id = response_json['id']

# Get credentials and create an API client
flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
    client_secrets_file, scopes)
credentials = flow.run_console()
youtube = googleapiclient.discovery.build(
    api_service_name, api_version, credentials=credentials)

request = youtube.videos().list(
    part="snippet,contentDetails,statistics",
    myRating="like",
    maxResults=50
)

response = request.execute()
ydl = youtube_dl.YoutubeDL({})
while 'nextPageToken' in response:
    for item in response["items"]:
        with ydl:
            video = ydl.extract_info("https://www.youtube.com/watch?v={}".format(item["id"]), download=False)

        if video['artist'] is not None and video['track'] is not None:
            print('{} - {}'.format(video['artist'], video['track']))
            query = "https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track".format(
                video['track'],
                video['artist']
            )
            response = requests.get(
                query,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer {}".format(OATH_TOKEN)
                }
            )
            response_json = response.json()
            if len(response_json['tracks']['items']) > 0:
                print(response_json['tracks']['items'][0]['uri'])
                query = "https://api.spotify.com/v1/playlists/{}/tracks".format(spotify_playlist_id)
                request_body = json.dumps({"uris": response_json['tracks']['items'][0]['uri']})
                response = requests.post(
                    query,
                    data=request_body,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": "Bearer {}".format(OATH_TOKEN)
                    }
                )
                response_json = response.json()
                print(response_json)

    request = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        myRating="like",
        maxResults=50,
        pageToken=response['nextPageToken']
    )

    response = request.execute()



print(response)

#if __name__ == "__main__":
#    main()