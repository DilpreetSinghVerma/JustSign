import os
import re
from nltk.tree import Tree, ParentedTree
from pattern.en import conjugate, lemma, lexeme,PRESENT,PAST,FUTURE
from logics.chunker import chunkerserver

def debugPrint(*args):
  if os.environ.get("FLASK_ENV") and os.environ.get("FLASK_ENV") == "development":
    print(*args)


def getSentenceType(text,debug=False):
  try:
    tree = Tree.fromstring(chunkerserver(text)["result"])
    sbar = [" ".join(x.leaves()).strip() for x in tree.subtrees() if x.label() == "SBAR"]
    if sbar:
      cc = [" ".join(x.leaves()).strip() for x in tree.subtrees() if x.label() == "CC"]
      if cc:
        return " - ".join([text, "Compound Sentence"])
      frag = [" ".join(x.leaves()).strip() for x in tree.subtrees() if x.label() == "FRAG"]
      if frag:
        return " - ".join([text, "Complex Sentence Fragment"])
      return " - ".join([text, "Complex Sentence"])

    s = [" ".join(x.leaves()).strip() for x in tree.subtrees() if x.label() == "S"]
    if s and len(s) > 1:
      return " - ".join([text, "Compound Sentence"])

    return " - ".join([text, "Simple Sentence"])

  except Exception as e:
    debugPrint(e)
    if os.environ.get("FLASK_ENV") and os.environ.get("FLASK_ENV") == "development":
      raise e
    return " - ".join([text, "Invalid Sentence"])