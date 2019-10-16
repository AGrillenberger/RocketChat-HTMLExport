# -*- coding: utf-8 -*-

import json
import os
import requests
import shutil
import getpass
from requests import sessions
from pprint import pprint
from rocketchat_API.rocketchat import RocketChat
import datetime
import re
import sys
import subprocess
from hashlib import md5
import time

if "RC_SERVER" in os.environ:
    server = os.environ["RC_SERVER"]
else:
    server = input("RocketChat server (full address, e. g. https://my.chat.server): ")


if "RC_USER" in os.environ:
    user = os.environ["RC_USER"]
else:
    user = input("username: ")

if "RC_PW" in os.environ:
    password = os.environ["RC_PW"]
else:
    password = getpass.getpass("password: ")


with sessions.Session() as session:
    rocket = RocketChat(user, password, server_url=server, session=session)

index = ""

def main():
    askDelete = False
    try:
        os.mkdir("out")
    except FileExistsError:
        askDelete = True

    while askDelete:
        answer = input("'out' directory already exists - delete contents [y/n]? ")
        if answer == "y":
            try:
                shutil.rmtree("out/", ignore_errors=True)
                os.mkdir("out")
            except Error:
                pass
            break
        elif answer == "n":
            break

    getChannels()
    getPrivChannels()
    getIMs()

    f = open("out/index.html", "w+", encoding="utf-8")
    f.write("<html><head><meta charset='utf-8'><title>RocketChat-Export</title><link rel='stylesheet' type='text/css' href='style.css' media='screen' /></head><body><div class='main'><h1>RocketChat-Export</h1><ul>" + index + "</ul></div></body></html>")
    f.close()

    shutil.copyfile("res/style.css", "out/style.css")

    print("")
    print("### FINISHED ###")
    print("The export files are stored in ./out --> " + os.getcwd() + "/out/index.html")

    url = "file://" + os.getcwd() + "/out/index.html"

    if sys.platform=='win32':
        os.startfile(url)
    elif sys.platform=='darwin':
        subprocess.Popen(['open', url])
    else:
        try:
            subprocess.Popen(['xdg-open', url])
        except OSError:
            pass

def getChannels():
    ch = rocket.channels_list_joined().json()

    for it in ch["channels"]:
        print("Channel " + it["name"])
        toHTML(it["_id"], "Kanal " + it["name"], getHistForChannel(it["_id"]))

def getHistForChannel(chan):
    res = []

    hist = rocket.channels_history(chan,count=1000000000).json()
    if not hist["success"]:
        if hist["error"].startswith("Error, too many requests"):
            m = re.search('([0-9]+) seconds', hist["error"])
            print("...waiting for " + m.group(0) + " seconds because of rate limits...")
            time.sleep(30)
            print("...continuing...")
            return getHistForPrivChannel(chan)
        else:
            print("...failed: " + hist["error"])
        return res

    for m in hist["messages"]:
        msg = {
            "author": m["u"]["username"],
            "msg": m["msg"],
            "ts": datetime.datetime.strptime(m["ts"], '%Y-%m-%dT%H:%M:%S.%fZ').strftime("%d.%m.%Y %H:%M:%S")
        }

        if "attachments" in m and m["attachments"] != None and len(m["attachments"]) > 0:
            if "image_url" in m["attachments"][0]:
                msg["img"] = downloadFile(m["attachments"][0]["image_url"])
            elif "title_link" in m["attachments"][0]:
                msg["file"] = downloadFile(m["attachments"][0]["title_link"])

        res.append(msg)

    return res

def getPrivChannels():
    ch = rocket.groups_list().json()

    for it in ch["groups"]:
        print("Group " + it["name"])
        toHTML(it["_id"], "Privater Kanal " + it["name"], getHistForPrivChannel(it["_id"]))

def getHistForPrivChannel(chan):
    res = []

    hist = rocket.groups_history(chan,count=1000000000).json()
    if not hist["success"]:
        if hist["error"].startswith("Error, too many requests"):
            m = re.search('([0-9]+) seconds', hist["error"])
            print("...waiting for " + m.group(0) + " seconds because of rate limits...")
            time.sleep(30)
            print("...continuing...")
            return getHistForPrivChannel(chan)
        else:
            print("...failed: " + hist["error"])
        return res

    for m in hist["messages"]:
        msg = {
            "author": m["u"]["username"],
            "msg": m["msg"],
            "ts": datetime.datetime.strptime(m["ts"], '%Y-%m-%dT%H:%M:%S.%fZ').strftime("%d.%m.%Y %H:%M:%S")
        }

        if "attachments" in m and m["attachments"] != None and len(m["attachments"]) > 0:
            if "image_url" in m["attachments"]:
                msg["img"] = downloadFile(m["attachments"][0]["image_url"])
            elif "title_link" in m["attachments"][0]:
                msg["file"] = downloadFile(m["attachments"][0]["title_link"])

        res.append(msg)

    return res

def getIMs():
    ch = rocket.im_list().json()

    for it in ch["ims"]:
        print("PrivMsg " + it["usernames"][0] + " / " + it["usernames"][1])
        toHTML(it["_id"], "Privatnachrichten " + it["usernames"][0] + " &lrarr; " + it["usernames"][1], getHistForIM(it["_id"]))

def getHistForIM(chan):
    res = []

    hist = rocket.im_history(chan,count=1000000000).json()
    if not hist["success"]:
        if hist["error"].startswith("Error, too many requests"):
            m = re.search('([0-9]+) seconds', hist["error"])
            print("...waiting for " + m.group(0) + " seconds because of rate limits...")
            time.sleep(30)
            print("...continuing...")
            return getHistForPrivChannel(chan)
        else:
            print("...failed: " + hist["error"])
        return res

    for m in hist["messages"]:
        msg = {
            "author": m["u"]["username"],
            "msg": m["msg"],
            "ts": datetime.datetime.strptime(m["ts"], '%Y-%m-%dT%H:%M:%S.%fZ').strftime("%d.%m.%Y %H:%M:%S")
        }

        if "attachments" in m and m["attachments"] != None and len(m["attachments"]) > 0:
            if "image_url" in m["attachments"]:
                msg["img"] = downloadFile(m["attachments"][0]["image_url"])
            elif "title_link" in m["attachments"][0]:
                msg["file"] = downloadFile(m["attachments"][0]["title_link"])

        res.append(msg)

    return res

def downloadFile(uri):
    r = requests.get(server + uri, headers=rocket.headers)
    split = re.sub("[^A-Za-z0-9_\-\.\/]+", "", uri)
    split = re.sub("\/\/", "/", split).split("/")

    path = "out/"
    for i in range(1, 2):
        path = path + split[i] + "/"
        try:
            os.mkdir(path)
        except FileExistsError:
            pass

    path2 = ""
    for i in range(2, len(split) - 1):
        path2 = path2 + split[i]
    path = path + md5(path2.encode("utf-8")).hexdigest() + "/"
    try:
        os.mkdir(path)
    except FileExistsError:
        pass

    fn = split[len(split) - 1]
    fp = path + md5(fn[:-4].encode("utf-8")).hexdigest() + fn[-4:]
    with open(fp, "wb") as f:
        f.write(r.content)
    pass

    return fp[4:]

def toHTML(id, title, msgs):
    html = "<html><head><meta charset='utf-8'><title>" + title + "</title><link rel='stylesheet' type='text/css' href='style.css' media='screen' /></head><body><div class='main'>"
    html += "<h1>" + title + "</h1>"
    html += "<p><a href='index.html'>&larr; zur&uuml;ck</a></p>"
    for m in reversed(msgs):
        html += "<div class='msg'><p><span class='from'>" + m["author"] + "</span> <span class='ts'>(" +  m["ts"] + ")</span></p><p class='content'>" + m["msg"]
        if "img" in m:
            html += "<a href='" + re.sub("[^A-Za-z0-9_\-\.\/]+", "", m["img"]) + "'><img src='" + re.sub("[^A-Za-z0-9_\-\.\/]+", "", m["img"]) + "' /></a>"
        if "file" in m:
            if m["file"][-3:] == "jpg" or m["file"][-3:] == "png":
                html += "<a href='" + re.sub("[^A-Za-z0-9_\-\.\/]+", "", m["file"]) + "'><img src='" + re.sub("[^A-Za-z0-9_\-\.\/]+", "", m["file"]) + "' /></a>"
            else:
                html += "<a href='" + re.sub("[^A-Za-z0-9_\-\.\/]+", "", m["file"]) + "'>" + re.sub("[^A-Za-z0-9_\-\.\/]+", "", m["file"]) + "</a>"
        html += "</p></div>"

    html += "<p><a href='index.html'>&larr; zur&uuml;ck</a></p>"
    html += "</div></body></html>"

    f = open("out/chat_" + id + ".html", "w+", encoding="utf-8")
    f.write(html)
    f.close()

    global index
    index += "<li><a href='chat_" + id + ".html'>" + title + "</a></li>"


main()
