import json
import os
import requests
import shutil
import getpass
from requests import sessions
from pprint import pprint
from rocketchat_API.rocketchat import RocketChat
import datetime

server = input("RocketChat server (full address, e. g. https://my.chat.server): ")
user = input("username: ")
password = getpass.getpass("password: ")


with sessions.Session() as session:
    rocket = RocketChat(user, password, server_url=server, session=session)

index = ""

def main():
    try: 
        os.mkdir("out")
    except FileExistsError as error: 
        pass    
    
    getChannels()
    getPrivChannels()
    getIMs()

    f = open("out/index.html", "w+")
    f.write("<html><head><meta charset='utf-8'><title>RocketChat-Export</title><link rel='stylesheet' type='text/css' href='style.css' media='screen' /></head><body><div class='main'><h1>RocketChat-Export</h1><ul>" + index + "</ul></div></body></html>")
    f.close()

    shutil.copyfile("style.css", "out/style.css")

def getChannels():
    ch = rocket.channels_list_joined().json()

    for it in ch["channels"]:
        print("Channel " + it["name"])
        toHTML(it["_id"], "Kanal " + it["name"], getHistForChannel(it["_id"]))

def getHistForChannel(chan):
    res = []
    
    for m in rocket.channels_history(chan,count=1000000000).json()["messages"]:
        msg = {
            "author": m["u"]["username"],
            "msg": m["msg"],
            "ts": datetime.datetime.strptime(m["ts"], '%Y-%m-%dT%H:%M:%S.%fZ').strftime("%d.%m.%Y %H:%M:%S")
        }

        if "attachments" in m and m["attachments"] != None and len(m["attachments"]) > 0:
            if "image_url" in m["attachments"][0]:
                msg["img"] = m["attachments"][0]["image_url"]
                downloadFile(m["attachments"][0]["image_url"])
            elif "title_link" in m["attachments"][0]:
                msg["file"] = m["attachments"][0]["title_link"]
                downloadFile(m["attachments"][0]["title_link"])

        res.append(msg)

    return res

def getPrivChannels():
    ch = rocket.groups_list().json()

    for it in ch["groups"]:
        print("Group " + it["name"])
        toHTML(it["_id"], "Privater Kanal " + it["name"], getHistForPrivChannel(it["_id"]))

def getHistForPrivChannel(chan):
    res = []
    
    for m in rocket.groups_history(chan,count=1000000000).json()["messages"]:
        msg = {
            "author": m["u"]["username"],
            "msg": m["msg"],
            "ts": datetime.datetime.strptime(m["ts"], '%Y-%m-%dT%H:%M:%S.%fZ').strftime("%d.%m.%Y %H:%M:%S")
        }

        if "attachments" in m and m["attachments"] != None and len(m["attachments"]) > 0:
            if "image_url" in m["attachments"]:
                msg["img"] = m["attachments"][0]["image_url"]
                downloadFile(m["attachments"][0]["image_url"])
            elif "title_link" in m["attachments"][0]:
                msg["file"] = m["attachments"][0]["title_link"]
                downloadFile(m["attachments"][0]["title_link"])

        res.append(msg)
    
    return res

def getIMs():
    ch = rocket.im_list().json()

    for it in ch["ims"]:
        print("PrivMsg " + it["usernames"][0] + " / " + it["usernames"][1])
        toHTML(it["_id"], "Privatnachrichten " + it["usernames"][0] + " &lrarr; " + it["usernames"][1], getHistForIM(it["_id"]))

def getHistForIM(chan):
    res = []
    
    for m in rocket.im_history(chan,count=1000000000).json()["messages"]:
        msg = {
            "author": m["u"]["username"],
            "msg": m["msg"],
            "ts": datetime.datetime.strptime(m["ts"], '%Y-%m-%dT%H:%M:%S.%fZ').strftime("%d.%m.%Y %H:%M:%S")
        }

        if "attachments" in m and m["attachments"] != None and len(m["attachments"]) > 0:
            if "image_url" in m["attachments"]:
                msg["img"] = m["attachments"][0]["image_url"]
                downloadFile(m["attachments"][0]["image_url"])
            elif "title_link" in m["attachments"][0]:
                msg["file"] = m["attachments"][0]["title_link"]
                downloadFile(m["attachments"][0]["title_link"])

        res.append(msg)
    
    return res

def downloadFile(uri):
    #urllib.request.urlretrieve(server + uri, 'out/file.png')
    #print(rocket.headers["X-Auth-Token"])

    r = requests.get(server + uri, headers=rocket.headers)

    split = uri.split("/")

    try: 
        os.mkdir("out/" + split[1])
    except FileExistsError: 
        pass

    try: 
        os.mkdir("out/" + split[1] + "/" + split[2])
    except FileExistsError: 
        pass

    with open("out/" + split[1] + "/" + split[2] + "/" + split[3], "wb") as f:
        f.write(r.content)
    pass

def toHTML(id, title, msgs):
    html = "<html><head><meta charset='utf-8'><title>" + title + "</title><link rel='stylesheet' type='text/css' href='style.css' media='screen' /></head><body><div class='main'>"
    html += "<h1>" + title + "</h1>"
    html += "<p><a href='index.html'>&larr; zur&uuml;ck</a></p>"
    for m in reversed(msgs):
        html += "<div class='msg'><p><span class='from'>" + m["author"] + "</span> <span class='ts'>(" +  m["ts"] + ")</span></p><p class='content'>" + m["msg"]
        if "img" in m:
            html += "<img src='" + m["img"][1:] + "' />"
        if "file" in m:
            html += "<a href='" + m["file"][1:] + "'>" + m["file"][1:] + "</a>"
        html += "</p></div>"
    
    html += "</div></body></html>"

    f = open("out/chat_" + id + ".html", "w+")
    f.write(html)
    f.close()

    global index
    index += "<li><a href='chat_" + id + ".html'>" + title + "</a></li>"


main()