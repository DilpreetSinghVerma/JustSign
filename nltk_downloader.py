import nltk

packages = None
try:
  with open("nltk.txt") as inpf:
    packages = [x.strip() for x in inpf.readlines()]
except Exception as ex:
  print("nltk.txt file not found, skipping installation.")
else:
  if packages:
    for x in packages:
      print(f"Installing {x}")
      nltk.download(x)