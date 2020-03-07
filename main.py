# -*- coding: utf-8 -*-
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import youtube_dl
import json
import requests
from spotify_auth import spotify_user_id, OATH_TOKEN

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

def get_youtube_api_client():
    scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "client_secret_file.json"
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
    credentials = flow.run_console()
    youtube = googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)
    return youtube

def make_request_post(query, request_body, token):
    return requests.post(
                query,
                data=request_body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer {}".format(token)
                }
            ).json()

def get_tracks(response, ydl, songs):
    for item in response["items"]:
        try:
            with ydl:
                video = ydl.extract_info("https://www.youtube.com/watch?v={}".format(item["snippet"]["resourceId"]["videoId"]), download=False)

            if video['artist'] is not None and video['track'] is not None:
                query = "https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track".format(
                    video['track'],
                    video['artist']
                )
                response_json = requests.get(
                    query,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": "Bearer {}".format(OATH_TOKEN)
                    }
                ).json()
                if len(response_json['tracks']['items']) > 0:
                    print('------------------------------------------------------')
                    songs.append(response_json['tracks']['items'][0]['uri'])
        except:
            print('error')
    return songs

def create_spotify_playlist(name):
    request_body = json.dumps({"name": name})
    query = "https://api.spotify.com/v1/users/{}/playlists".format(spotify_user_id)
    response_json = make_request_post(query, request_body, OATH_TOKEN)
    return response_json['id']


spotify_playlist_id = create_spotify_playlist("Youtube Liked Videos")
liked_songs_uris = []

youtube = get_youtube_api_client()
ydl = youtube_dl.YoutubeDL({})

# Get liked videos from YouTube
response = youtube.videos().list(
    part="snippet,contentDetails,statistics",
    myRating="like",
    maxResults=50
).execute()
get_tracks(response, ydl, liked_songs_uris)
while 'nextPageToken' in response:
    response = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        myRating="like",
        maxResults=50,
        pageToken=response['nextPageToken']
    ).execute()
    get_tracks(response, ydl, liked_songs_uris)

# Add songs from liked videos to Spotify playlist
query = "https://api.spotify.com/v1/playlists/{}/tracks".format(spotify_playlist_id)
request_body = json.dumps({"uris": liked_songs_uris})
response_json = make_request_post(query, request_body, OATH_TOKEN)

# Get YouTube Playlists
response = youtube.playlists().list(
    part="snippet",
    mine=True,
    maxResults=50
).execute()
youtube_playlists = []
for i in response['items']:
    youtube_playlists.append({
        'id': i['id'],
        'title': i['snippet']['title'],
        'songs': []
    })

# Get tracks in playlists and create spotify playlists
for k, p in enumerate(youtube_playlists):
    songs = []
    response = youtube.playlistItems().list(
        part="snippet",
        playlistId=p['id'],
        maxResults="50"
    ).execute()
    print(response)
    save_re = response
    youtube_playlists[k]['songs'] = get_tracks(response, ydl, songs)

    while 'nextPageToken' in response:
        response = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            myRating="like",
            maxResults=50,
            pageToken=response['nextPageToken']
        ).execute()
        youtube_playlists[k]['songs'] = get_tracks(response, ydl, songs)

    if len(songs) > 0:
        spotify_playlist_id = create_spotify_playlist(p.title)
        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(spotify_playlist_id)
        request_body = json.dumps({"uris": songs})
        response_json = make_request_post(query, request_body, OATH_TOKEN)