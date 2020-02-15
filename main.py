# -*- coding: utf-8 -*-
import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

scopes = ["https://www.googleapis.com/auth/youtube.readonly"]


# Disable OAuthlib's HTTPS verification when running locally.
# *DO NOT* leave this option enabled in production.
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

api_service_name = "youtube"
api_version = "v3"
client_secrets_file = "client_secret_file.json"

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
while 'nextPageToken' in response:
    for item in response["items"]:
        video_id = item["id"]
        youtube_url = "https://www.youtube.com/watch?v={}".format(item["id"])
        print(item)

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