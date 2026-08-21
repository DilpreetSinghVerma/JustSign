import pandas as pd
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os

def hamNoSysToSigml(text):
  try:
    data = pd.read_csv("sigmlcode.csv")
    x = ET.fromstring(text)
    string=str(minidom.parseString(text).toprettyxml())
    s=string.split('<hamnosys_manual>')[1]
    s=s.split('</hamnosys_manual>')[0]
    l1=[]
    s1=s.split('<')
    result = ""
    for i in s1:
      #print(i.split('/')[0])
      l1.append(i.split('/')[0])
    for j in l1:
      for i in range(0,len(data)):
        if(data.loc[i][1]==j):
          result = result + data.loc[i][0]
    return result
  except Exception as e:
    if os.environ.get("FLASK_ENV") and os.environ.get("FLASK_ENV") == "development":
      raise e
    return ""
  