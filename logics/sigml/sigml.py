import csv
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os

def hamNoSysToSigml(text):
  try:
    src_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_path = os.path.join(src_dir, "sigmlcode.csv")
    data = []
    if os.path.exists(csv_path):
      with open(csv_path, encoding="utf-8") as f:
        reader = csv.reader(f)
        data = list(reader)
    
    x = ET.fromstring(text)
    string=str(minidom.parseString(text).toprettyxml())
    s=string.split('<hamnosys_manual>')[1]
    s=s.split('</hamnosys_manual>')[0]
    l1=[]
    s1=s.split('<')
    result = ""
    for i in s1:
      l1.append(i.split('/')[0])
    for j in l1:
      for row in data:
        if len(row) > 1 and row[1] == j:
          result = result + row[0]
    return result
  except Exception as e:
    if os.environ.get("FLASK_ENV") and os.environ.get("FLASK_ENV") == "development":
      raise e
    return ""

  