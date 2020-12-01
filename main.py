# Downloader for ubicast media servers

import sys
import re
import requests
import json
import ffmpeg
from bs4 import BeautifulSoup

def choice(options, prompt):
    i = 1
    for option in options:
        print(f"{option} : {i}")
        i = i + 1
    
    choices = [str(c) for c in range(1, len(options)+1)]
    
    while True:
        output = input(prompt)
        if output in choices:
            output = int(output) - 1
            output = options[output]
            return output
        else:
            print("Bad option. Options: " + ", ".join(options))

if len(sys.argv) == 1:
    print(f"Usage:\
        {sys.argv[0]} <link>")
    exit()

with open("config.json") as config_file:
    config = json.load(config_file)
    api_key = config["api_key"]
    cookie = config.get("cookie", "")
    ubicast_server = config["ubicast_server"]

urls = sys.argv[1:]

def oid_from_permalink(url):
    oid = re.sub('.*permalink', "", url).strip("/")
    return oid

def oid_from_videolink(url):
    cookies = {'mssessionid': cookie}
    
    webpage = requests.get(url, cookies=cookies, verify=False)
    soup = BeautifulSoup(webpage.content, "html.parser")
    meta_tag = soup.find("meta", property="og:url")
    permalink = meta_tag["content"]
    return oid_from_permalink(permalink)

def get_oid(url):
    if "permalink" in url:
        return oid_from_permalink(url)
    else:
        if (len(cookie) == 0):
            print("The requested URL is not a permalink. To download this video, you need to provide a cookie in config.json.")
            exit(1)
        return oid_from_videolink(url)

def download(url):
    oid = get_oid(url)
    
    params = {
        "api_key": api_key,
        "oid": oid,
        "html5": "mp4_mp3_m3u8"
    }

    res = requests.get(f"{ubicast_server}/api/v2/medias/modes/",
                       params=params, verify=False)
    dict_vid = json.loads(res.content)
    streams = dict_vid["names"]
    choosed_stream = choice(streams, "Choose a stream:")
    url_vid = dict_vid[choosed_stream]["resource"]["url"]
    url_audio = dict_vid["audio"]["tracks"][0]["url"]

    params.pop("html5")
    res = requests.get(f"{ubicast_server}/api/v2/medias/get/",
                       params=params, verify=False)
    info_vid = json.loads(res.content)
    title = info_vid["info"]["title"]

    audio = ffmpeg.input(url_audio)
    video = ffmpeg.input(url_vid)
    stream = ffmpeg.output(audio, video, title+".mkv", codec="copy")
    ffmpeg.run(stream)


for url in urls:
    try:
        download(url)
    except:
        print("There was an error. Ensure your api key and/or cookie are valid.")
        exit(1)
    