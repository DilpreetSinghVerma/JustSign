import re
import os

def getCategories():
  return sorted(sorted(os.listdir("DictionarySigns")),key=len)
  # return sorted([x.replace("_"," ").title() for x in os.listdir("DictionarySigns")])

def getElements(category):
  if category in getCategories():
    return sorted(sorted([x[:x.index(".sigml")] for x in os.listdir(os.path.join("DictionarySigns",category)) if x.endswith(".sigml")]),key=len)
  else:
    return []
  # return sorted([x.replace("_"," ").title() for x in os.listdir("DictionarySigns")])

def searchElements(word):
  categories = getCategories()
  result = []
  for category in categories:
    elements = getElements(category)
    for element in elements:
      if word.lower() in element:
        result.append((category,element))
  return sorted(sorted(result,key=lambda x: x[1]),key=lambda x: len(x[1]))