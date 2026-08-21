from flask import Response
import re
import os
import mimetypes

from logics.announcements.listAnnouncements import staticAnnouncements,airportStaticAnnouncements
from logics.isldictionary import getCategories,getElements

def get_sign_files_dir():
  base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
  local_sign_dir = os.path.join(base_dir, "SignFiles")
  if os.path.exists(local_sign_dir):
    return local_sign_dir
  parent_sign_dir = os.path.abspath(os.path.join(base_dir, "..", "SignFiles"))
  if os.path.exists(parent_sign_dir):
    return parent_sign_dir
  return local_sign_dir

def sigmlProvider(text):
  text = text.replace("\n"," ")
  text = re.sub(r"[^a-zA-Z0-9 ]","",text.lower()).strip()
  text = re.sub(r"\s+"," ",text.lower()).strip()
  print("recieved Text for sigml: ",text)
  words = text.split(" ")
  resultSigml = []
  sign_dir = get_sign_files_dir()
  
  if os.path.exists(sign_dir):
    dir_files = [x.lower() for x in os.listdir(sign_dir)]
  else:
    dir_files = []

  for word in words:
    if word == "i" and os.path.exists(os.path.join(sign_dir, "i-proper.sigml")):
      with open(os.path.join(sign_dir, "i-proper.sigml"), encoding="utf-8", errors="ignore") as inpf:
        resultSigml.append(inpf.read().replace("$PROD",word))
    elif f"{word}.sigml" in dir_files:
      with open(os.path.join(sign_dir, f"{word}.sigml"), encoding="utf-8", errors="ignore") as inpf:
        resultSigml.append(inpf.read().replace("gloss=\"\"","gloss=\"$PROD\"").replace("$PROD",word))
    else:
      for char in word:
        if f"{char}.sigml" in dir_files:
          with open(os.path.join(sign_dir, f"{char}.sigml"), encoding="utf-8", errors="ignore") as inpf:
            resultSigml.append(inpf.read().replace("$PROD",word))
  resultSigml = [re.sub(r"<sigml>|</sigml>","",x) for x in resultSigml]
  result = "".join(resultSigml)
  result = f"<sigml>{result}</sigml>"
  return result
  # return send_from_directory("../SignFiles","quiet.sigml",mimetype="text/plain",attachment_filename=f"{str(uuid.uuid4().hex)}.sigml")

def dictionaryProvider(text):
  test = re.findall(r"category:.+\-element:.+",text)
  if test:
    data = text.split("-")
    words = [x.split(":")[1] for x in data]
    category = words[0]
    element = words[1]
    if category in getCategories() and element in getElements(category):
      with open(os.path.join("../DictionarySigns",category,f"{element}.sigml")) as inpf:
        return inpf.read().replace("$PROD",element)
  return sigmlProvider(text)

def dictionaryVideoProvider(text):
  test = re.findall(r"category:.+\-element:.+",text)
  if test:
    data = text.split("-")
    words = [x.split(":")[1] for x in data]
    category = words[0]
    element = words[1]
    if category in getCategories() and element in getElements(category):
      if os.path.exists(os.path.join("../DictionaryMovies",category,f"{element}.mp4")):
        with open(os.path.join("../DictionaryMovies",category,f"{element}.mp4"),'rb') as inpf:
          data = inpf.read()
          response = Response(data,200,mimetype=mimetypes.guess_type(os.path.join("../DictionaryMovies",category,f"{element}.mp4"))[0],direct_passthrough=True)
          return response
      else:
        with open(os.path.join("../DictionaryMovies","not-available.mp4"),'rb') as inpf:
          data = inpf.read()
          response = Response(data,200,mimetype=mimetypes.guess_type(os.path.join("../DictionaryMovies","not-available.mp4"))[0],direct_passthrough=True)
          return response
  with open(os.path.join("../DictionaryMovies","not-available.mp4"),'rb') as inpf:
    data = inpf.read()
    response = Response(data,200,mimetype=mimetypes.guess_type(os.path.join("../DictionaryMovies","not-available.mp4"))[0],direct_passthrough=True)
    return response

def railwayProvider(text):
  resultSigml = []
  static_announcements = staticAnnouncements()
  railway_special = os.listdir(os.path.join("../RailwayFiles","special"))
  if static_announcements.get(text,None):
    result = ""
    for r in railway_special:
      if static_announcements.get(text).lower() in r.lower():
        result = r
        break
    if result:
      with open(os.path.join("../RailwayFiles","special",result)) as inpf:
        resultSigml.append(inpf.read())
  else:
    test = re.findall(r"announcement_type:.+\-announcement_platform:\d+\-announcement_hour:\d+\-announcement_minute:\d+",text)
    if test:
      data = text.split("-")
      words = [x.split(":")[1] for x in data]
      for word in words:
        if f"{word}.sigml" in os.listdir("../RailwayFiles"):
          with open(os.path.join("../RailwayFiles",f"{word}.sigml")) as inpf:
            resultSigml.append(inpf.read())
        else:
          for char in word:
            if f"{char}.sigml" in [x.lower() for x in os.listdir("../SignFiles")]:
              with open(os.path.join("../SignFiles",f"{char}.sigml")) as inpf:
                resultSigml.append(inpf.read().replace("$PROD",word))
    else:
      return sigmlProvider(text)
  resultSigml = [re.sub(r"<sigml>|</sigml>","",x) for x in resultSigml]
  result = "".join(resultSigml)
  result = f"<sigml>{result}</sigml>"
  return result

def airportProvider(text):
  static_announcements = airportStaticAnnouncements()
  if static_announcements.get(text,None):
    return sigmlProvider(static_announcements[text])
  else:
    return sigmlProvider(text)