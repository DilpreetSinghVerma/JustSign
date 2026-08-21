import os
import re
from nltk.tag import pos_tag
from nltk.tree import Tree, ParentedTree
from pattern.en import conjugate, lemma, lexeme,PRESENT,PAST,FUTURE
from logics.chunker import chunkerserver
from logics.sentencereplacements import getSentenceReplacements

prereplacements = {
  "even though":"although",
  "’":"'",
  "‘":"'",
  " ":" ",
  "“":"\"",
  "”":"\"",
}

replacements = {
  " n't":"n't",
  "can not":"cannot",
  "even though":"although",
  "young":"young age",
  "old":"old age",
  "Dying, he was":"He died in",
  "Without being not":"Not",
  "age age":"age",
}

nouns = ["NN", "NNS", "NNP", "NNPS", "NP"]
pronouns = ["PR", "PRP", "PRP$", "WP", "WP$"]
verbs = ["VB", "VBP", "VBZ", "VBG", "VBN", "VBD"]
punctuations = ["SYM", "LS", ".", "!", "?", ",", ":", "(", ")", "\"", "#", "$"]
possesivedeterminers = {"i":"my","you":"your","he":"his","she":"her","it":"its","we":"our","they":"their","one":"one's"}
possesivepronouns = {"i":"mine","you":"yours","he":"his","she":"hers","it":"its","we":"ours","they":"theirs","one":"one's"}
objects = {"i":"me","you":"you","he":"him","she":"her","it":"it","we":"us","they":"them","one":"one"}
negations = {"am":"ain't", "are":"aren't", "can":"can't", "could":"couldn't", "dare":"daren't", "did":"didn't", "does":"doesn't", "do":"don't", "had":"hadn't", "has":"hasn't", "have":"haven't", "is":"isn't", "may":"mayn't", "might":"mightn't", "must":"mustn't", "need":"needn't", "ought":"oughtn't", "shall":"shan't", "should":"shouldn't", "was":"wasn't", "were":"weren't", "will":"won't", "would":"wouldn't",}

contractions = {"ain't":"am not","daren't":"dare not","mayn't":"may not","shan't":"shall not","isn't":"is not","aren't":"are not","wasn't":"was not","weren't":"were not","haven't":"have not","hasn't":"has not","hadn't":"had not","won't":"will not","wouldn't":"would not","don't":"do not","doesn't":"does not","didn't":"did not","can't":"can not","couldn't":"could not","shouldn't":"should not","mightn't":"might not","mustn't":"must not","would've":"would have","should've":"should have","could've":"could have","might've":"might have","must've":"must have","i'm":"i am","you're":"you are","he's":"he is","she's":"she is","it's":"it is","'tis it":"is","we're":"we are","they're":"they are","that's":"that is","who's":"who is","what's":"what is","what're":"what are","where's":"where is","when's":"when is","why's":"why is","how's":"how is","i'll":"i will","you'll":"you will","he'll":"he will","she'll":"she will","it'll":"it will","we'll":"we will","they'll":"they will","that'll":"that will","who'll":"who will","what'll":"what will","where'll":"where will","when'll":"when will","why'll":"why will","how'll":"how will","i'd":"i would","you'd":"you would","he'd":"he would","she'd":"she would","it'd":"it would","we'd":"we would","they'd":"they would","that'd":"that would","who'd":"who would","what'd":"what would","where'd":"where would","when'd":"when would","why'd":"why would","how'd":"how would","i've":"i have","you've":"you have","we've":"we have","they've":"they have","ma'am":"madam","'twas":"it was","she\'d\'ve":"she would have","\'tisn\'t":"it is not","there's":"there is",}

rule1 = ["since","as","when","anytime"]
rule2 = ["am", "is", "are", "was", "were", "has", "have", "had"]
rule2a = ["am", "is", "are", "was", "were"]
rule2b = ["has", "have", "had"]
rule5a = ["dawn", "dusk", "morning", "mid-morning", "midmorning", "noon", "afternoon", "evening", "night", "mid-night", "midnight"]
rule5b = ["winter", "spring", "summer", "autumn"]
rule7 = list([f"{x} not" for x in negations.keys()])
rule7.extend(negations.values())
rule11a = ["am","is","are","was","were"]
rule11b = ["has","have","had"]

ignoreingify = ["he","she","they","them","that","the","you","him","his","her","me","my","i","lied","would","should","could","in","it","tea","rang"]
lemmacorpus = {"paid":"pay","laid":"lay",}
ingifycorpus = {"sings":"singing","love":"loving","turned":"turning"}
def ingify(word):
  debugPrint("ingify:",word)
  pos = pos_tag([word,])[0]
  if word in ignoreingify:
    return word
  if word in lemmacorpus.keys():
    word = lemmacorpus[word]
  if word in ingifycorpus.keys():
    return ingifycorpus[word]
  if pos[1] not in verbs:
    return word
  word1Lex = [x for x in lexeme(word) if x.endswith("ing")]
  word1final = word1Lex[0] if word1Lex else word
  return word1final

def generateResponse(text,rule,debug):
  response = text.capitalize()
  response = response.replace(" i "," I ")
  response = re.sub(r" ([^\w\d])",r"\1",response)
  response = re.sub(r" +"," ",response)
  debugPrint("before replacement:",response)
  for x in replacements.keys():
    # response = response.replace(x,replacements[x])
    response = re.sub(r"\b%s\b" % x, replacements[x], response)
  for x in negations:
    response = re.sub(r"\b%s not\b" % negations[x], negations[x], response)
  debugPrint("after replacement:",response)
  if os.environ.get("FLASK_ENV") and os.environ.get("FLASK_ENV") == "development" and debug:
    return (response + " - " + rule,True)
  return (response,True)

def debugPrint(*args):
  if os.environ.get("FLASK_ENV") and os.environ.get("FLASK_ENV") == "development":
    print(*args)

def rule1convert(trees,subject1,verbphrase1,verb1,subject2,punc):
  debugPrint("rule1")
  verb1final = ingify(verb1)
  part1 = verbphrase1.replace(verb1,verb1final)
  # part2 = " ".join(trees[1].leaves()).strip().replace(subject2,subject1)
  if (subject1 in objects.keys() or subject2 in objects.keys()) and subject1 != subject2:
    subject1, subject2 = subject2, subject1
    # part1 = f"{objects.get(subject2,subject2)} {part1}"
  part2 = re.sub(r"\b%s\b" % subject2, subject1, " ".join(trees[1].leaves()).strip())
  part2 = part2.replace(" "+punc,"") if punc else part2
  if subject1 not in objects.keys() and subject2 not in objects.keys() and subject1 != subject2:
    part1 = f"{subject1} {part1}"
    part2 = re.sub(r"\b%s\b" % subject1, subject2, part2)
  return ", ".join([part1, part2 + punc]).strip()

def rule2convert(trees,subject1,verbphrase1,verb1,subject2,punc):
  debugPrint("rule2")
  verb1final = ingify(verb1)
  part1 = " ".join([subject1, verbphrase1.replace(verb1,verb1final)]).strip()
  part2 = " ".join(trees[1].leaves()).strip()
  part2 = part2.replace(" "+punc,"") if punc else part2
  return ", ".join([part1, part2 + punc]).strip()

def rule3convert(trees,subject1,verbphrase1,verb1,subject2,punc):
  debugPrint("rule3")
  verb1final = ingify(verb1)
  part1 = "because of " + " ".join([subject1, verbphrase1.replace(verb1,verb1final)]).strip()
  part2 = " ".join(trees[1].leaves()).strip()
  part2 = part2.replace(" "+punc,"") if punc else part2
  return ", ".join([part1, part2 + punc]).strip()

def rule4convert(tree,whnp,words,punc):
  debugPrint("rule4")
  if len(whnp.split(" ")) > 1:
    whnp2 = whnp.split(" ")[-1]
    words[words.index(whnp2) + 1] = ingify(words[words.index(whnp2) + 1])
    part1 = " ".join(words[:words.index(whnp2) - 1])
    part2 = " ".join(words[words.index(whnp2):])
  else:
    whnp2 = whnp
    debugPrint(pos_tag(words[words.index(whnp2) + 1:]))
    nn = ""
    vbg = ""
    for w,t in pos_tag(words[:words.index(whnp2)]):
      if t == "NN":
        nn = w
        break
    for w,t in pos_tag(words[words.index(whnp2) + 1:]):
      if t == "VBG":
        vbg = w
        break
    if nn and vbg and vbg.endswith("ing"):
      part1 = " ".join(words[:words.index(nn)]) + " " + vbg
      part2 = " ".join(words[words.index(vbg) + 1:])
      part2 = part2.replace(punc,"") if punc else part2
      part2 = f"{part2} {nn}"
    else:
      testword = words[words.index(whnp2) + 1]
      offset = 1
      if testword == "would":
        words[words.index(whnp2) + 1] = "to"
      elif testword in ["do","does","can","could","should","would","must","did"]:
        offset = 2
        if words[words.index(whnp2) + 2] == "not":
          words[words.index(whnp2) + 3] = ingify(words[words.index(whnp2) + 3])
        else:
          words[words.index(whnp2) + 2] = ingify(words[words.index(whnp2) + 2])
      else:
        words[words.index(whnp2) + 1] = ingify(words[words.index(whnp2) + 1])
      part1 = " ".join(words[:words.index(whnp2)])
      part2 = " ".join(words[words.index(whnp2) + offset:])
  part2 = part2.replace(" "+punc,"") if punc else part2
  for end in ["are","is","were"]:
    if part2.endswith(f" {end}"):
      part2 = part2.replace(f" {end}","")
      break
  return " ".join([part1, part2 + punc]).strip()

def rule5convert(trees,namednoun,subject1,cardinal,punc):
  debugPrint("rule5")
  if namednoun:
    if namednoun in rule5a:
      prefix = "at "
    elif namednoun in rule5b:
      prefix = "in "
  elif cardinal:
    prefix = "at the age of "
  else:
    prefix = ""
  part1 = trees[0].leaves()
  if subject1 != namednoun:
    part1 = prefix + subject1.strip()
  else:
    part1 = prefix + " ".join(part1[part1.index(namednoun if namednoun else cardinal):]).strip()
  part2 = " ".join(trees[1].leaves()).strip()
  part2 = part2.replace(" "+punc,"") if punc else part2
  return ", ".join([part1, part2 + punc]).strip()

def rule6convert(trees,verbgerund,punc,prp,verbbase,verbphrase1):
  debugPrint("rule6/12")
  if prp:
    prefix = "at the time of "
  else:
    prefix = "at the time of "
    verbphrase1final = re.sub(r"\b%s\b" % verbbase, ingify(verbbase), verbphrase1)
  part1 = trees[0].leaves()
  part1 = prefix + " ".join(part1[part1.index("when") + 1:]).strip()
  part1 = part1.replace(" "+punc,"") if punc else part1
  if prp:
    debugPrint("rule6verbs",verbbase,verbphrase1)
    part1 = part1.replace(f" {prp} {verbbase} ",f" {objects.get(prp,prp)} ")
  else:
    part1 = part1.replace(verbphrase1,verbphrase1final)

  if len(verbphrase1.split(" ")) > 1 and prp:
    verbphrase1 = " ".join([ingify(x) for x in verbphrase1.split(" ")])
    part1 = prefix + f" {possesivedeterminers.get(prp,prp)} {verbphrase1} "
  part2 = " ".join(trees[1].leaves()).strip()
  part2 = part2.replace(" "+punc,"") if punc else part2
  return ", ".join([part1, part2 + punc]).strip()

def rule21convert(trees,verbgerund,punc):
  debugPrint("rule21")
  prefix = "at the time "
  part1 = trees[0].leaves()
  part1 = prefix + " ".join(part1[part1.index("when") + 1:]).strip()
  part2 = " ".join(trees[1].leaves()).strip()
  part2 = part2.replace(" "+punc,"") if punc else part2
  return ", ".join([part1, part2 + punc]).strip()

def rule7convert(trees,subject1,subject2,verbphrase1,verbbase,punc):
  debugPrint("rule7")
  prefix = "without "
  part1 = prefix + re.sub(r".*%s" % verbbase, ingify(verbbase),verbphrase1).strip()
  part2 = " ".join(trees[1].leaves()).strip()
  if subject1 and subject2 and subject2 in objects.keys():
    part2 = re.sub(r"\b%s\b" % subject2, subject1, part2)
  part2 = part2.replace(" "+punc,"") if punc else part2
  return ", ".join([part1, part2 + punc]).strip()

def rule8convert(trees,subject1,subject2,verbphrase1,verbbase,punc):
  debugPrint("rule8")
  prefix = "by "
  part1 = prefix + re.sub(r".*%s" % verbbase, ingify(verbbase),verbphrase1).strip()
  part2 = " ".join(trees[1].leaves()).strip()
  # if subject1 and subject2 and subject2 in objects.keys():
  #   part2 = re.sub(r"\b%s\b" % subject2, subject1, part2)
  part2 = part2.replace(" "+punc,"") if punc else part2
  return ", ".join([part1, part2 + punc]).strip()

def rule9convert(text,modal,words,punc):
  debugPrint("rule9")
  return re.sub(r"so that.*%s" % modal,"to ",text)

def rule10convert(text,modal,words,punc):
  debugPrint("rule10")
  negation = "n\'t" if "n't" in text else "not"
  return re.sub(r"\bso(.*)that.*%s\b" % negation,r"too\1to",text)

def rule11convert(trees,subject1,verbphrase1,verb1,subject2,punc):
  debugPrint("rule11")
  
  prefix = "in spite of"
  if verb1 in rule11a or verb1 in rule11b:
    verb1final = "being" if verb1 in rule11a else "having"
  else:
    verb1final = ingify(verb1)
  subject1final = objects.get(subject1,subject1)

  words = trees[0].leaves()
  part1 = [prefix, subject1final, verb1final]
  part1.extend(words[words.index(verb1) + 1:])

  part1 = " ".join(part1).strip().strip(punc)
  part2 = " ".join(trees[1].leaves()).strip()
  for w in ["yet",]:
    part2 = re.sub(r"\b%s\b" % w, "", part2)
  part2 = part2.replace(" "+punc,"") if punc else part2
  return ", ".join([part1, part2 + punc]).strip()

def rule12convert(trees,subject1,verbphrase1,verb1,subject2,punc):
  debugPrint("rule12")
  
  if verb1 in rule11a or verb1 in rule11b:
    verb1final = "being" if verb1 in rule11a else "having"
  else:
    verb1final = verb1

  words = trees[0].leaves()
  if words[words.index(verb1) + 1] == "not":
    part1 = [subject1, verb1]
  else:
    part1 = [subject1, verb1final]
  part1.extend(words[words.index(verb1) + 1:])

  part1 = " ".join(part1).strip().strip(punc)
  part2 = " ".join(trees[1].leaves()).strip()
  # part2 = re.sub(r"\b%s\b" % subject2, subject1, part2)
  part2 = part2.replace(" "+punc,"") if punc else part2
  return ", ".join([part1, part2 + punc]).strip()

def rule13convert(trees,subject1,verbphrase1,verb1,subject2,punc):
  debugPrint("rule13")
  
  prefix = "at the time of"
  if verb1 in rule11a or verb1 in rule11b:
    verb1final = "being" if verb1 in rule11a else "having"
  else:
    verb1final = ingify(verb1)
  subject1final = possesivedeterminers.get(subject1,subject1)

  words = trees[0].leaves()
  part1 = [prefix, subject1final, verb1final]
  part1.extend(words[words.index(verb1) + 1:])

  part1 = " ".join(part1).strip().strip(punc)
  part2 = " ".join(trees[1].leaves()).strip()
  # part2 = re.sub(r"\b%s\b" % subject2, subject1, part2)
  part2 = part2.replace(" "+punc,"") if punc else part2
  return " ".join([part2, part1 + punc]).strip()

def rule14convert(trees,subject1,verbphrase1,verb1,subject2,punc):
  debugPrint("rule14")
  
  prefix = "anywhere"
  if verb1 in rule11a or verb1 in rule11b:
    verb1final = "being" if verb1 in rule11a else "having"
  elif verb1 in ["find"]:
    verb1final = verb1 
  else:
    verb1final = ingify(verb1)

  words = trees[0].leaves()
  part1 = [prefix, subject1, verb1final if words[words.index(verb1) + 1:] else verb1]
  part1.extend(words[words.index(verb1) + 1:])

  part1 = " ".join(part1).strip().strip(punc)
  part2 = " ".join(trees[1].leaves()).strip()
  # part2 = re.sub(r"\b%s\b" % subject2, subject1, part2)
  part2 = part2.replace(" "+punc,"") if punc else part2
  return " ".join([part2, part1 + punc]).strip()


def rule15convert(trees,words,subject1,verbphrase1,verb1,subject2,punc):
  debugPrint("rule15")
  changed = False
  for i,w in enumerate(words[0]):
    words[0][i] = negations.get(w,w)
    if negations.get(w,None):
      changed = True
  if not changed and "not" in words[1]:
    words[1] = [x for x in words[1] if x != "not"]    
  
  part1 = " ".join(words[1]).strip().strip(punc)
  part2 = re.sub(r"\bunless\b","if"," ".join(words[0]).strip())
  part2 = part2.replace(" "+punc,"") if punc else part2
  return ", ".join([part1, part2 + punc]).strip()


def rule16convert(trees,words,subject1,verbphrase1,verb1,subject2,punc):
  debugPrint("rule16")
  part1 = " ".join(words[1]).strip().strip(punc)
  part2 = re.sub(r"\bas if\b","like"," ".join(words[0]).strip())
  part2 = part2.replace(" "+punc,"") if punc else part2
  return " ".join([part1, part2 + punc]).strip()
  
def rule17convert(tree,whnp,words,punc):
  debugPrint("rule17")
  return re.sub(r"\bhow many\b","number of"," ".join(words).strip())

def rule18convert(tree,whnp,words,punc):
  debugPrint("rule18")
  return re.sub(r"\bin which \b|\b in which\b",""," ".join(words).strip())


def ruleSelector(rulename):
  rules = {
    "rule1": rule1convert,
    "rule2": rule2convert,
    "rule3": rule3convert,
    "rule4": rule4convert,
    "rule5": rule5convert,
    "rule6": rule6convert,
    "rule7": rule7convert,
    "rule8": rule8convert,
    "rule9": rule9convert,
    "rule10": rule10convert,
    "rule11": rule11convert,
    "rule12": rule12convert,
    "rule13": rule13convert,
    "rule14": rule14convert,
    "rule15": rule15convert,
    "rule16": rule16convert,
    "rule17": rule17convert,
    "rule18": rule18convert,
    "rule21": rule21convert,
  }
  return rules.get(rulename, lambda *args: None)


def complexToSimple(text,debug=False):
  debugPrint("Running Complex to Simple Module")
  try:
    sentreplacements = getSentenceReplacements() 
    for sent in sentreplacements:
      if re.sub(r"[^a-zA-Z0-9 ]","",text.lower()).strip() == re.sub(r"[^a-zA-Z0-9 ]","",sent["sent"].lower()).strip():
        return (sent["repl"].capitalize(),True)

    for c in contractions.keys():
      text = re.sub(r"\b%s\b" % c, contractions[c],text.lower())
    result = [x.strip() for x in text.lower().split(",")]
    for w in ["even though","wherever","although","though","unless","because","when","after","as if","if"]:
      if len(result) == 1 and w in text.lower() and not text.lower().startswith(w):
        text = re.sub(r"\b%s\b" % w,f",{w}",text.lower())
        result = [x.strip() for x in text.lower().split(",")]
    for i in range(len(result)):
      for x in prereplacements.keys():
        # result[i] = result[i].replace(x,prereplacements[x])
        result[i] = re.sub(r"\b%s\b" % x, prereplacements[x], result[i])
    rule = None
    response = None
    if(len(result) == 2):
      trees = [Tree.fromstring(chunkerserver(x)["result"]) for x in result]
      words = [list(x.flatten()) for x in trees]

      if len([x for x in words[1] if x in rule1]) > 0:
        trees[0], trees[1] = trees[1], trees[0]
        words[0], words[1] = words[1], words[0]

      tree1 = trees[0]
      tree2 = trees[1]
      punc = [" ".join(x.leaves()).strip() for x in tree2.subtrees() if x.label() in punctuations]
      punc = [" ".join(x.leaves()).strip() for x in tree1.subtrees() if x.label() in punctuations] if not punc else punc
      punc = punc[-1] if punc else ""

      verbphrase1 = [" ".join(x.leaves()).strip() for x in tree1.subtrees() if x.label() == "VP"]
      verbphrase2 = [" ".join(x.leaves()).strip() for x in tree2.subtrees() if x.label() == "VP"]

      subject1 = [" ".join(x.leaves()).strip() for x in tree1.subtrees() if x.label() == "NP"]
      subject1 = subject1[0] if subject1 else subject1
      verb1 = [" ".join(x.leaves()).strip() for x in tree1.subtrees() if x.label() in verbs]
      verb1 = verb1[0] if verb1 else ""
      verb2 = [" ".join(x.leaves()).strip() for x in tree2.subtrees() if x.label() in verbs]
      verb2 = verb2[0] if verb2 else ""
      subject2 = [" ".join(x.leaves()).strip() for x in tree2.subtrees() if x.label() in nouns or x.label() in pronouns]
      subject2 = subject2[0] if subject2 else ""


      verbbase = [" ".join(x.leaves()).strip() for x in tree1.subtrees() if x.label() in verbs]
      if words[0][0] == "if":
        debugPrint("verb7phrase",verbphrase1)
        debugPrint("verb7base",verbbase)
        if verbphrase1:
          changed = False
          # for r in rule7:
          #   if changed:
          #     break
          #   if verbphrase1[0].startswith(r) and len(verbphrase1) > 1:
          #     verbphrase1 = verbphrase1[1]
          #     changed = True
          #     if verbbase:
          #       if len(verbbase) > 1:
          #         verbbase = verbbase[1]
          #       elif len(verbphrase1.split(" ")) == 1:
          #         verbbase = verbphrase1
          #       else:
          #         verbbase = verbbase[0]
          #     else:
          #       verbbase = ""
          if not changed:
            verbphrase1 = verbphrase1[0]
            verbbase = verbbase[0] if verbbase else ""
        else:
          verbphrase1 = ""
          verbbase = verbbase[0] if verbbase else ""
        if "not" in words[0]:
          rule = "rule7"
        else:
          rule = "rule8"

      debugPrint("verb7phrase-p2",verbphrase1)
      debugPrint("verb7base-p2",verbbase)
      if not response:
        response = ruleSelector(rule)(trees,subject1,subject2,verbphrase1,verbbase,punc)

      if response:
        return generateResponse(response,rule,debug)


      if words[1][0] == "if":
        verbbase = [" ".join(x.leaves()).strip() for x in tree2.subtrees() if x.label() in verbs]
        trees[0], trees[1] = trees[1], trees[0]
        words[0], words[1] = words[1], words[0]
        debugPrint("verb7phrase",verbphrase2)
        debugPrint("verb7base",verbbase)
        if verbphrase2:
          changed = False
          # for r in rule7:
          #   if changed:
          #     break
          #   if verbphrase2[0].startswith(r) and len(verbphrase2) > 1:
          #     verbphrase2 = verbphrase2[1]
          #     changed = True
          #     if verbbase:
          #       if len(verbbase) > 1:
          #         verbbase = verbbase[1]
          #       elif len(verbphrase2.split(" ")) == 1:
          #         verbbase = verbphrase2
          #       else:
          #         verbbase = verbbase[0]
          #     else:
          #       verbbase = ""
          if not changed:
            verbphrase2 = verbphrase2[0]
            verbbase = verbbase[0] if verbbase else ""
        else:
          verbphrase2 = ""
          verbbase = verbbase[0] if verbbase else ""
        if "not" in words[0]:
          rule = "rule7"
        else:
          rule = "rule8"
      
      debugPrint("verb7phrase-p2",verbphrase2)
      debugPrint("verb7base-p2",verbbase)
      if not response:
        response = ruleSelector(rule)(trees,subject1,subject2,verbphrase2,verbbase,punc)

      if response:
        return generateResponse(response,rule,debug)

      verbphrase1 = verbphrase1[0] if verbphrase1 else ""
      verbphrase2 = verbphrase2[0] if verbphrase2 else ""
      verbbase = verbbase[0] if verbbase else ""




      subject1 = [" ".join(x.leaves()).strip() for x in tree1.subtrees() if x.label() == "NP"]
      subject1 = subject1[0] if subject1 else subject1
      namednoun = [" ".join(x.leaves()).strip() for x in tree1.subtrees() if x.label() == "NN"]
      namednoun = namednoun[0] if namednoun else ""
      cardinal = [" ".join(x.leaves()).strip() for x in tree1.subtrees() if x.label() == "CD"]
      cardinal = cardinal[0] if cardinal else ""

      # if x in rule1 and (subject1 == subject2 or len([x for x in tree1.subtrees() if x.label() in pronouns]) ):
      if words[0][0] == "when" and (namednoun in rule5a or namednoun in rule5b or cardinal) and rule is None:
        rule = "rule5"

      if not response:
        response = ruleSelector(rule)(trees,namednoun,subject1,cardinal,punc)

      if response:
        return generateResponse(response,rule,debug)

      verbgerund = [" ".join(x.leaves()).strip() for x in tree1.subtrees() if x.label() == "VBG"]
      verbgerund = verbgerund[0] if verbgerund else ""

      prp = [" ".join(x.leaves()).strip() for x in tree1.subtrees() if x.label() == "PRP"]
      prp = prp[0] if prp else ""

      if words[0][0] == "when" and rule is None:
        rule = "rule6"

      if not response:
        response = ruleSelector(rule)(trees,verbgerund,punc,prp,verbbase,verbphrase1)

      if response:
        return generateResponse(response,rule,debug)

      subject1 = [" ".join(x.leaves()).strip() for x in tree1.subtrees() if x.label() == "NP"]
      subject1 = subject1[0] if subject1 else subject1
      verb1 = [" ".join(x.leaves()).strip() for x in tree1.subtrees() if x.label() in verbs]
      verb1 = verb1[0] if verb1 else ""
      verb2 = [" ".join(x.leaves()).strip() for x in tree2.subtrees() if x.label() in verbs]
      verb2 = verb2[0] if verb2 else ""
      subject2 = [" ".join(x.leaves()).strip() for x in tree2.subtrees() if x.label() in nouns or x.label() in pronouns]
      subject2 = subject2[0] if subject2 else ""

      debugPrint("namednoun: ",namednoun)
      debugPrint("cardinal: ",cardinal)
      debugPrint("verbgerund: ",verbgerund)
      debugPrint("verbbase: ",verbbase)
      debugPrint("subject1: ",subject1)
      debugPrint("verbphrase1: ",verbphrase1)
      debugPrint("verbphrase2: ",verbphrase2)
      debugPrint("verb1: ",verb1)
      debugPrint("verb2: ",verb2)
      debugPrint("subject2: ",subject2)
      debugPrint("punc: ",punc)
      debugPrint("tree0",list(trees[0].flatten()))
      debugPrint("tree1",list(trees[1].flatten()))



      if words[1][0] in ["yet"] and subject1 and verb1 and verbphrase1 and rule is None:
        rule = "rule11"

      if not response:
        response = ruleSelector(rule)(trees,subject1,verbphrase1,verb1,subject2,punc)

      if response:
        return generateResponse(response,rule,debug)

      if words[0][0] in ["though", "although"] and subject1 and rule is None:
        rule = "rule11"

      if not response:
        response = ruleSelector(rule)(trees,subject1,verbphrase1,verb1,subject2,punc)

      if response:
        return generateResponse(response,rule,debug)

      if words[1][0] in ["though", "although"] and subject2 and rule is None:
        rule = "rule11"
        trees[0], trees[1] = trees[1], trees[0]
        words[0], words[1] = words[1], words[0]

      if not response:
        response = ruleSelector(rule)(trees,subject2,verbphrase2,verb2,subject1,punc)

      if response:
        return generateResponse(response,rule,debug)



      if words[0][0] in ["because","whenever","wherever"] and subject1 and rule is None:
        if words[0][0] == "because":
          rule = "rule12"
        elif words[0][0] == "whenever":
          rule = "rule13"
        elif words[0][0] == "wherever":
          rule = "rule14"

      if not response:
        response = ruleSelector(rule)(trees,subject1,verbphrase1,verb1,subject2,punc)

      if response:
        return generateResponse(response,rule,debug)

      if words[1][0] in ["because","whenever","wherever"] and subject2 and rule is None:
        if words[1][0] == "because":
          rule = "rule12"
        elif words[1][0] == "whenever":
          rule = "rule13"
        elif words[1][0] == "wherever":
          rule = "rule14"

        trees[0], trees[1] = trees[1], trees[0]
        words[0], words[1] = words[1], words[0]

      if not response:
        response = ruleSelector(rule)(trees,subject2,verbphrase2,verb2,subject1,punc)

      if response:
        return generateResponse(response,rule,debug)



      if words[0][0] in ["unless"] and subject1 and rule is None:
        rule = "rule15"

      if not response:
        response = ruleSelector(rule)(trees,words,subject1,verbphrase1,verb1,subject2,punc)

      if response:
        return generateResponse(response,rule,debug)

      if words[1][0] in ["unless"] and subject2 and rule is None:
        rule = "rule15"
        trees[0], trees[1] = trees[1], trees[0]
        words[0], words[1] = words[1], words[0]

      if not response:
        response = ruleSelector(rule)(trees,words,subject2,verbphrase2,verb2,subject1,punc)

      if response:
        return generateResponse(response,rule,debug)



      if words[0][0] == "as" and words[0][1] == "if" and rule is None:
        rule = "rule16"

      if not response:
        response = ruleSelector(rule)(trees,words,subject1,verbphrase1,verb1,subject2,punc)

      if response:
        return generateResponse(response,rule,debug)

      if words[1][0] == "as" and words[1][1] == "if" and rule is None:
        rule = "rule16"
        trees[0], trees[1] = trees[1], trees[0]
        words[0], words[1] = words[1], words[0]

      if not response:
        response = ruleSelector(rule)(trees,words,subject2,verbphrase2,verb2,subject1,punc)

      if response:
        return generateResponse(response,rule,debug)

      if words[0][0] in rule1 and rule is None:
        if verb1 in rule2 and len(subject1) > 1:
          if subject1 == subject2:
            rule = "rule3"
          else:
            rule = "rule2"
        if rule is None:
          rule = "rule1"
      
      subject1 = subject1.capitalize() if subject1 == "i" or subject1 == "i'll" else subject1
      subject2 = subject2.capitalize() if subject2 == "i" or subject2 == "i'll" else subject2

      if not response:
        response = ruleSelector(rule)(trees,subject1,verbphrase1,verb1,subject2,punc)
      
      if response:
        return generateResponse(response,rule,debug)



      if words[0][0] in ["after"] and subject1 and verb1 and rule is None:
        rule = "rule1"

      if not response:
        response = ruleSelector(rule)(trees,subject1,verbphrase1,verb1,subject2,punc)

      if response:
        return generateResponse(response,rule,debug)

      if words[1][0] in ["after"] and subject2 and verb2 and rule is None:
        rule = "rule1"
        trees[0], trees[1] = trees[1], trees[0]
        words[0], words[1] = words[1], words[0]

      if not response:
        response = ruleSelector(rule)(trees,subject2,verbphrase2,verb2,subject1,punc)

      if response:
        return generateResponse(response,rule,debug)




      return (text.capitalize(),False)
    elif(len(result) == 1):
      tree = [Tree.fromstring(chunkerserver(x)["result"]) for x in result][0]
      words = list(tree.flatten())
      punc = [" ".join(x.leaves()).strip() for x in tree.subtrees() if x.label() in punctuations]
      punc = punc[-1] if punc else ""

      modal = [" ".join(x.leaves()).strip() for x in tree.subtrees() if x.label() == "MD"]
      modal = modal[0] if modal else ""

      whnp = [" ".join(x.leaves()).strip() for x in tree.subtrees() if x.label() == "WHNP"]
      whnp = whnp[0] if whnp else ""
      if "in which" in result[0] and rule is None:
        rule = "rule18"
        response = ruleSelector(rule)(tree,whnp,words,punc)

      if "how many" in whnp and rule is None:
        rule = "rule17"
        response = ruleSelector(rule)(tree,whnp,words,punc)

      if whnp and rule is None:
        rule = "rule4"
        # response = ruleSelector(rule)(tree,whnp,words,punc)
        response = text

      if "so that" in result[0] and modal and rule is None:
        rule = "rule9"
        response = ruleSelector(rule)(result[0],modal,words,punc)

      if "so" in words and "that" in words and words.index("so") + 1 < words.index("that") and rule is None:
        rule = "rule10"
        response = ruleSelector(rule)(result[0],modal,words,punc)


      nounphrase = [" ".join(x.leaves()).strip() for x in tree.subtrees() if x.label() == "NP"]
      verbphrase = [" ".join(x.leaves()).strip() for x in tree.subtrees() if x.label() == "VP"]
      # verbphrase = verbphrase[0] if verbphrase else verbphrase
      verbbase = [" ".join(x.leaves()).strip() for x in tree.subtrees() if x.label() in verbs]
      verbbase = verbbase[0] if verbbase else ""

      debugPrint("modal: ",modal)
      debugPrint("whnp: ",whnp)
      debugPrint("nounphrase: ",nounphrase)
      debugPrint("verbphrase: ",verbphrase)
      debugPrint("verbbase: ",verbbase)
      debugPrint("punc: ",punc)
      debugPrint("tree",list(tree.flatten()))
      debugPrint("words",words)

      if response:
        return generateResponse(response,rule,debug)
      return (text.capitalize(),False)

      # return ", ".join(result)
    elif(len(result) == 3):
      trees = [Tree.fromstring(chunkerserver(x)["result"]) for x in result]
      words = [list(x.flatten()) for x in trees]

      if words[0][0] == "since" and words[2][0] == "because":
        pass

    return (text.capitalize(),False)

  except Exception as e:
    debugPrint(e)
    return (text.capitalize(),False)