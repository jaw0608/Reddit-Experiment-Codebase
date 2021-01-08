# -*- coding: utf-8 -*-

# Sample Python code for youtube.thumbnails.set
# NOTES:
# 1. This sample code uploads a file and can't be executed via this interface.
#    To test this code, you must run it locally using your own API credentials.
#    See: https://developers.google.com/explorer-help/guides/code_samples#python
# 2. This example makes a simple upload request. We recommend that you consider
#    using resumable uploads instead, particularly if you are transferring large
#    files or there's a high likelihood of a network interruption or other
#    transmission failure. To learn more about resumable uploads, see:
#    https://developers.google.com/api-client-library/python/guide/media_upload

import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import sys
from subprocess import call
import json

from googleapiclient.http import MediaFileUpload
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import argparser, run_flow
#from apiclient.http import MediaFileUpload

scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]

def main(url):
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "../upload/client_secrets.json"
    thumb = "../../tmp/images/title.png"
    if os.path.exists("../../tmp/images/thumbnail.jpg"):
        thumb = "../../tmp/images/thumbnail.jpg"


    # Get credentials and create an API client
    flow = flow_from_clientsecrets(
        client_secrets_file, scope=scopes)
    storage = Storage('../upload/thumb.json')
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        args = argparser.parse_args()
        credentials = run_flow(flow,storage,args)

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)

    request = youtube.thumbnails().set(
        videoId=url,

        # TODO: For this request to work, you must replace "YOUR_FILE"
        #       with a pointer to the actual file you are uploading.
        media_body=MediaFileUpload(thumb)
    )
    response = request.execute()
    storage.put(credentials)
    #print(response)

if __name__ == "__main__":
    argparser.add_argument("-v", required=True, help="Video id")
    argparser.add_argument("-p", required=False, help="Playlist id")
    args = sys.argv[1:]
    if(len(args)==0):
        sys.exit(-1)
    url = args[0]
    playlist = "None"
    if len(args)>1:
        playlist = args[1]
        playlist = playlist[3:]
    url = url[3:]
    main(url)
    if playlist!="None":
        ret = call(['python3','../upload/playlist.py',"{}".format(url), "{}".format(playlist)])
        print("Return from playlist:",ret)
        if ret==-1:
            sys.exit(-1)
    sys.exit(0)
