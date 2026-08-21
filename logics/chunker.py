import os
import re
import subprocess
import tempfile
import uuid
import sys
from nltk.tree import Tree
from nltk.tokenize import sent_tokenize

prereplacements = {
  "’":"'",
  " ":" ",
}

def clean(text):
  for x in prereplacements.keys():
    text = re.sub(r"\b%s\b" % x, prereplacements[x], text)
  return text


def debugPrint(*args):
  if os.environ.get("FLASK_ENV") and os.environ.get("FLASK_ENV") == "development":
    print(*args)

def chunkerserver(text):
  text = clean(text)
  response = chunkerlocal(text)
  debugPrint("chunker: ",response["result"])
  return response


def extract_trees_from_output(output_text):
  trees = []
  idx = 0
  while True:
    pos = output_text.find("(ROOT", idx)
    if pos == -1:
      break
    depth = 0
    end_pos = pos
    for i in range(pos, len(output_text)):
      if output_text[i] == '(':
        depth += 1
      elif output_text[i] == ')':
        depth -= 1
        if depth == 0:
          end_pos = i + 1
          break
    if depth == 0:
      tree_str = output_text[pos:end_pos]
      try:
        t = Tree.fromstring(tree_str)
        trees.append(str(t))
      except Exception as e:
        debugPrint("Parse tree error:", e)
    idx = max(pos + 1, end_pos)
  return trees


def chunkerlocal(text):
  sentences = sent_tokenize(text)
  current = uuid.uuid4()
  current_file = os.path.join(tempfile.gettempdir(), f"{current}.txt")
  try:
    with open(current_file, "w", encoding="utf-8") as oup:
      for i, s in enumerate(sentences):
        oup.write(s)
        if i < len(sentences) - 1:
          oup.write(os.linesep)
    
    src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser_dir = os.path.join(src_dir, "parser")
    model_jar = os.path.join(parser_dir, "stanford-parser-4.2.0-models.jar")
    if not os.path.exists(model_jar):
      import urllib.request
      print("Downloading Stanford Parser models JAR (168MB)...")
      url = "https://repo1.maven.org/maven2/edu/stanford/nlp/stanford-parser/4.2.0/stanford-parser-4.2.0-models.jar"
      urllib.request.urlretrieve(url, model_jar)

    parser_glob = os.path.join(parser_dir, "*")
    model_resource = "edu/stanford/nlp/models/lexparser/englishPCFG.caseless.ser.gz"
    cp_sep = os.pathsep
    
    stanfordcall = f'java -mx800m -cp "{parser_glob}{cp_sep}" edu.stanford.nlp.parser.lexparser.LexicalizedParser -retainTMPSubcategories -outputFormat penn {model_resource} "{current_file}"'
    
    is_windows = sys.platform.startswith('win')
    output = subprocess.check_output(stanfordcall, shell=is_windows, stderr=subprocess.STDOUT)
    out_str = str(output, encoding="utf-8", errors="replace")
    
    trees = extract_trees_from_output(out_str)
    return {"text": text, "result": "\n".join(trees)}
  except Exception as e:
    debugPrint("Stanford Parser Exception:", e)
    return {"text": text, "result": ""}
  finally:
    if os.path.exists(current_file):
      try:
        os.remove(current_file)
      except OSError:
        pass