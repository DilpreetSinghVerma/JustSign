import os
import re
from nltk.tag import pos_tag
from nltk.tree import Tree, ParentedTree
from pattern.en import conjugate, lemma, lexeme,PRESENT,PAST,FUTURE
from logics.chunker import chunkerserver
from logics.lists.verbs_to_nouns import verbToNoun
from logics.sentencereplacements import getSentenceReplacements

prereplacements = {
  "even though":"although",
  "and therefore":"so",
  "therefore":"so",
  "’":"'",
  "‘":"'",
  " ":" ",
  "“":"\"",
  "”":"\"",
  ";":",",
}

replacements = {
  " n't":"n't",
  "can not":"cannot",
  "even though":"although",
  "young":"young age",
  "old":"old age",
  "Dying, he was":"He died in",
  "sweet be":"sweetness",
  "Without being not":"Not",
}

modals = ["will","won't","wouldn't","can't","couldn't"]

verbs = ["VB", "VBP", "VBZ", "VBG", "VBN", "VBD"]
punctuations = ["SYM", "LS", ".", "!", "?", ",", ":", "(", ")", "\"", "#", "$"]
possesivedeterminers = {"i":"my","you":"your","he":"his","she":"her","it":"its","we":"our","they":"their","one":"one's"}
possesivepronouns = {"i":"mine","you":"yours","he":"his","she":"hers","it":"its","we":"ours","they":"theirs","one":"one's"}
objects = {"i":"me","you":"you","he":"him","she":"her","it":"it","we":"us","they":"them","one":"one"}
negations = {"am":"ain't", "are":"aren't", "can":"can't", "could":"couldn't", "dare":"daren't", "did":"didn't", "does":"doesn't", "do":"don't", "had":"hadn't", "has":"hasn't", "have":"haven't", "is":"isn't", "may":"mayn't", "might":"mightn't", "must":"mustn't", "need":"needn't", "ought":"oughtn't", "shall":"shan't", "should":"shouldn't", "was":"wasn't", "were":"weren't", "will":"won't", "would":"wouldn't",}

contractions = {"ain't":"am not","daren't":"dare not","mayn't":"may not","shan't":"shall not","isn't":"is not","aren't":"are not","wasn't":"was not","weren't":"were not","haven't":"have not","hasn't":"has not","hadn't":"had not","won't":"will not","wouldn't":"would not","don't":"do not","doesn't":"does not","didn't":"did not","can't":"can not","couldn't":"could not","shouldn't":"should not","mightn't":"might not","mustn't":"must not","would've":"would have","should've":"should have","could've":"could have","might've":"might have","must've":"must have","i'm":"i am","you're":"you are","he's":"he is","she's":"she is","it's":"it is","'tis it":"is","we're":"we are","they're":"they are","that's":"that is","who's":"who is","what's":"what is","what're":"what are","where's":"where is","when's":"when is","why's":"why is","how's":"how is","i'll":"i will","you'll":"you will","he'll":"he will","she'll":"she will","it'll":"it will","we'll":"we will","they'll":"they will","that'll":"that will","who'll":"who will","what'll":"what will","where'll":"where will","when'll":"when will","why'll":"why will","how'll":"how will","i'd":"i would","you'd":"you would","he'd":"he would","she'd":"she would","it'd":"it would","we'd":"we would","they'd":"they would","that'd":"that would","who'd":"who would","what'd":"what would","where'd":"where would","when'd":"when would","why'd":"why would","how'd":"how would","i've":"i have","you've":"you have","we've":"we have","they've":"they have","ma'am":"madam","'twas":"it was","she\'d\'ve":"she would have","\'tisn\'t":"it is not","there's":"there is",}

ignoreingify = ["he","she","they","them","that","the","you","him","his","her","me","my","i","lied","would","should","could","in","it","tea","rang"]
lemmacorpus = {"paid":"pay","laid":"lay",}
ingifycorpus = {"sings":"singing","love":"loving","needs":"needing",}
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
  debugPrint("after replacement:",response)
  if os.environ.get("FLASK_ENV") and os.environ.get("FLASK_ENV") == "development" and debug:
    return (response + " - " + rule,True)
  return (response,True)

def debugPrint(*args):
  if os.environ.get("FLASK_ENV") and os.environ.get("FLASK_ENV") == "development":
    print(*args)

def rule1convert(tree,verb,subject,conjunction,words,punc):
  debugPrint("rule1")
  verbfinal = ingify(verb)
  modal = ""
  if words[words.index(subject)+1] in modals:
    modal = words[words.index(subject)+1]
    del words[words.index(subject)+1]
  part1 = " ".join(words[:words.index(conjunction)]).replace(verb,verbfinal)
  # part2 = " ".join(trees[1].leaves()).strip().replace(subject2,subject1)
  part1 = re.sub(r"\b%s\b" % subject, "", part1).strip()
  subject = subject + " " + modal if modal else subject
  part2 = subject + " " + " ".join(words[words.index(conjunction) + 1:]).replace(modal,"")
  return " ".join([part1, part2]).strip()

def rule2convert(tree,words,punc):
  debugPrint("rule2")
  text = " ".join(words)
  s1 = "not only"
  s2 = "but also"
  prefix = "besides being"
  subject = text[:text.index(s1)].strip()
  part1 = text[text.index(s1)+len(s1):text.index(s2)].strip()
  part2 = text[text.index(s2)+len(s2):].strip()
  return " ".join([prefix, part1, subject, part2]).strip()

def rule3convert(tree,verb,subject,conjunction,words,punc):
  debugPrint("rule3")
  prefix = "in spite of"
  verbfinal = ingify(verb)
  text = " ".join(words)
  part1 = verbfinal + " " + text[text.index(verb)+len(verb):text.index(conjunction)].strip()
  part2 = text[text.index(conjunction)+len(conjunction):].strip()
  if subject not in part2:
    part2 = f"{subject} {verb} {part2}"
  return " ".join([prefix, part1+",", part2]).strip()

def rule4convert(trees,words,punc):
  debugPrint("rule4")
  conjunction = "otherwise" if "otherwise" in words[0] else "or"
  part1 = " ".join(words[0][:words[0].index(conjunction)]).strip()
  part2 = " ".join(words[1][words[1].index("not") + 1:]).strip()
  return " ".join([part1,"to",part2 ]).strip()

def rule5convert(trees,words,verb2,punc):
  debugPrint("rule5")
  finalVerb2 = verbToNoun(lemma(verb2))
  gerundVerb2 = ingify(lemma(verb2))
  conjunction = "otherwise" if "otherwise" in words[0] else "or"
  part1 = " ".join(words[0][:words[0].index(conjunction)]).strip()
  part2 = " ".join(words[1][words[1].index("will") + 1:]).strip()
  if verb2 != finalVerb2:
    part2 = re.sub(r"\b%s\b" % verb2, finalVerb2, part2)
    return " ".join([part1,"to escape",part2 ]).strip()
  if verb2 != gerundVerb2:
    part2 = re.sub(r"\b%s\b" % verb2, gerundVerb2, part2)
    return " ".join([part1,"to avoid",part2 ]).strip()

def rule6convert(trees,words,adjp,punc):
  debugPrint("rule6")
  part1 = " ".join(["being",adjp]).strip()
  part2 = " ".join(words[1][words[1].index("and") + 1:]).strip()
  return " ".join([part1,part2 ]).strip()

def rule7convert(trees,words,subject1,subject2,nounphrases1,nounphrases2,adjp,vbd,punc):
  debugPrint("rule7")
  text1 = " ".join(words[0])
  text2 = " ".join(words[1])
  joiner = "for"
  if subject2 in possesivedeterminers.keys():
    text1 = re.sub(r"\b%s\b" % subject1,subject2,text1)
    text2 = re.sub(r"\b%s\b" % subject2,subject1,text2)
    subject1,subject2 = subject2,subject1
  debugPrint(nounphrases1)
  debugPrint(nounphrases2)
  # debugPrint(subject1)
  # debugPrint(len(subject1))
  # debugPrint(vbd)
  # debugPrint(text1.index(vbd))
  # debugPrint(text1.index(subject1))
  # debugPrint(text1[text1.index(subject1)+len(subject1):text1.index(vbd)])
  part1 = possesivedeterminers[subject1] if subject1 in possesivedeterminers.keys() else subject1
  part1 = f"{part1} {text1[text1.index(subject1)+len(subject1):text1.index(vbd)]}".strip()
  # part1 = f"{part1} {' '.join(words[0][words[0].index(subject1)+1:words[0].index(vbd)])}".strip()
  part1 = f"{part1} {adjp} {lemma(vbd)}"
  if re.sub(r" +"," ",part1).endswith("there be") and len(nounphrases1) > 1:
    part1 = f"due to {nounphrases1[1]}"
    joiner = ""

  part2 = text2[text2.index("so ")+len("so "):].strip().replace(punc,"")
  return " ".join([part2,joiner,part1+punc]).strip()

def rule8convert(trees,words,punc):
  debugPrint("rule8")
  conjunction = "otherwise" if "otherwise" in words[0] else "or"
  prefix = "in the event of being"
  part1 = " ".join(words[0][:words[0].index(conjunction)]).strip()
  part1 = part1[part1.index("must not be")+len("must not be"):]
  part2 = " ".join(words[1]).strip()
  return " ".join([prefix,part1,part2 ]).strip()

def rule9convert(trees,words,subject1,subject2,nounphrases1,nounphrases2,adjp,vbd,punc):
  debugPrint("rule9")
  text1 = " ".join(words[0])
  text2 = " ".join(words[1][1:])
  part1 = text1.strip().replace(punc,"")
  part2 = text2.strip().replace(punc,"")
  return "; ".join([part2,part1+punc]).strip()

def rule10convert(tree,sents,conjunction,words,punc):
  debugPrint("rule10")
  final = " ".join(tree.leaves())
  if re.sub(r"[^a-zA-Z0-9]",""," ".join(tree.leaves()).lower()).strip() == re.sub(r"[^a-zA-Z0-9]","",sents[0].lower()).strip():
    final = re.sub(r"\b%s\b" % conjunction, punc if punc else "." , final)
  return final

def rule11convert(trees,words,punc):
  debugPrint("rule11")
  debugPrint("words",words)
  final = " ".join(words[0])
  if words[1][0] == "and":
    final = final + punc if punc else "."
    final = final + " " + " ".join(words[1][1:])
  if words[1][0] == "so":
    final = final + punc if punc else "."
    final = final + " " + " ".join(words[1][1:])
  if words[1][0] == "or":
    final = final + punc if punc else "."
    final = final + " " + " ".join(words[1])
  return final

def rule12convert(tree,sents,conjunction,words,punc):
  debugPrint("rule12")
  final = " ".join(tree.leaves())
  if re.sub(r"[^a-zA-Z0-9]",""," ".join(tree.leaves()).lower()).strip() == re.sub(r"[^a-zA-Z0-9]","",sents[0].lower()).strip():
    final = re.sub(r"\b%s\b" % conjunction, (punc if punc else ".") + " " + conjunction , final)
  return final
  # verbfinal = ingify(verb)
  # modal = ""
  # if words[words.index(subject)+1] in modals:
  #   modal = words[words.index(subject)+1]
  #   del words[words.index(subject)+1]
  # part1 = " ".join(words[:words.index(conjunction)]).replace(verb,verbfinal)
  # # part2 = " ".join(trees[1].leaves()).strip().replace(subject2,subject1)
  # part1 = re.sub(r"\b%s\b" % subject, "", part1).strip()
  # subject = subject + " " + modal if modal else subject
  # part2 = subject + " " + " ".join(words[words.index(conjunction) + 1:]).replace(modal,"")
  # return " ".join([part1, part2]).strip()


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
  }
  return rules.get(rulename, lambda *args: None)


def compoundToSimple(text,debug=False):
  debugPrint("Running Compound to Simple Module")
  try:
    sentreplacements = getSentenceReplacements()
    for sent in sentreplacements:
      if re.sub(r"[^a-zA-Z0-9 ]","",text.lower()).strip() == re.sub(r"[^a-zA-Z0-9 ]","",sent["sent"].lower()).strip():
        return (sent["repl"].capitalize(),True)

    for c in contractions.keys():
      text = re.sub(r"\b%s\b" % c, contractions[c],text.lower())
    # text = text.replace(";",",")
    result = [x.strip() for x in text.lower().split(",")]
    for w in ["even though","and therefore","therefore"]:
      if len(result) == 1 and w in text.lower() and not text.lower().startswith(w):
        text = re.sub(r"\b%s\b" % w,f",{w}",text.lower())
        result = [x.strip() for x in text.lower().split(",")]

    if len(result) == 1 and "must" in text.lower() and "or" in text.lower() and "will" in text.lower():
      text = re.sub(r"\bor\b",f"or,",text.lower())
    if len(result) == 1 and "must" in text.lower() and "otherwise" in text.lower() and "will" in text.lower():
      text = re.sub(r"\botherwise\b",f"otherwise,",text.lower())
    result = [x.strip() for x in text.lower().split(",")]
    if len(result) == 2 and result[1].startswith("but"):
      text = " ".join(result)
      result = [x.strip() for x in text.lower().split(",")]
    # if len(result) == 2 and result[1].startswith("and"):
    #   text = " ".join(result)
    #   result = [x.strip() for x in text.lower().split(",")]

    for i in range(len(result)):
      for x in prereplacements.keys():
        # result[i] = result[i].replace(x,prereplacements[x])
        result[i] = re.sub(r"\b%s\b" % x, prereplacements[x], result[i])
    rule = None
    response = None
    debugPrint("result input",result)

    if len(result) == 2 and ";" in result[0]:
      
      return generateResponse("; ".join([result[0][:result[0].index(";")],result[1]]),"rule0",debug)


    if len(result) == 3 and result[1].count(" ") == 0:
      # if result[1].strip() in ["indeed"]:
      #   result[1] = f"{result[2]}"
      # else:
      result[1] = f"{result[1]} {result[2]}"
      del result[2]

    proceed = False

    metarule = ["or","and","otherwise","so","but","not","either","neither","for","yet","therefore"]
    for r in metarule:
      if re.findall(r"\b%s\b" % r, text.lower()):
        proceed = True

    if not proceed:
      if "," in text.lower():
        text = text.replace(",",";")
      return generateResponse("; ".join(result),"rule0",debug)


    
    debugPrint("result input final",result)

    if(len(result) == 2):
      trees = [Tree.fromstring(chunkerserver(x)["result"]) for x in result]
      words = [list(x.flatten()) for x in trees]

      tree1 = trees[0]
      tree2 = trees[1]

      punc = [" ".join(x.leaves()).strip() for x in tree2.subtrees() if x.label() in punctuations]
      punc = punc[-1] if punc else ""

      if "must not be" in result[0] and "otherwise" in result[0] and result[0].index("otherwise") > result[0].index("must not be") and "will not be" in result[1]:
        rule = "rule8"
        response = ruleSelector(rule)(trees,words,punc)
      elif "must not be" in result[0] and "or" in result[0] and result[0].index("or") > result[0].index("must not be") and "will not be" in result[1]:
        rule = "rule8"
        response = ruleSelector(rule)(trees,words,punc)

      if response:
        return generateResponse(response,rule,debug)

      if "must" in result[0] and "otherwise" in result[0] and result[0].index("otherwise") > result[0].index("must") and "will not" in result[1]:
        rule = "rule4"
        response = ruleSelector(rule)(trees,words,punc)
      elif "must" in result[0] and "or" in result[0] and result[0].index("or") > result[0].index("must") and "will not" in result[1]:
        rule = "rule4"
        response = ruleSelector(rule)(trees,words,punc)

      if response:
        return generateResponse(response,rule,debug)

      verb2 = [" ".join(x.leaves()).strip() for x in tree2.subtrees() if x.label() in verbs]
      verb2 = verb2[0] if verb2 else ""
      
      if "must" in result[0] and "otherwise" in result[0] and result[0].index("otherwise") > result[0].index("must") and "will" in result[1]:
        rule = "rule5"
        response = ruleSelector(rule)(trees,words,verb2,punc)
      elif "must" in result[0] and "or" in result[0] and result[0].index("or") > result[0].index("must") and "will" in result[1]:
        rule = "rule5"
        response = ruleSelector(rule)(trees,words,verb2,punc)

      if response:
        return generateResponse(response,rule,debug)


      adjp = [" ".join(x.leaves()).strip() for x in tree1.subtrees() if x.label() == "ADJP"]
      adjp = adjp[0] if adjp else ""

      # if adjp and words[1][0] == "and":
      #   rule = "rule6"
      #   response = ruleSelector(rule)(trees,words,adjp,punc)

      # if response:
      #   return generateResponse(response,rule,debug)



      vbd = [" ".join(x.leaves()).strip() for x in tree1.subtrees() if x.label() in verbs]
      vbd = vbd[0] if vbd else ""

      nounphrases1 = [" ".join(x.leaves()).strip() for x in tree1.subtrees() if x.label() == "NP"]
      nounphrases2 = [" ".join(x.leaves()).strip() for x in tree2.subtrees() if x.label() == "NP"]
      
      subject1 = [" ".join(x.leaves()).strip() for x in tree1.subtrees() if x.label() == "NP"]
      subject1 = subject1[0] if subject1 else ""

      subject2 = [" ".join(x.leaves()).strip() for x in tree2.subtrees() if x.label() == "NP"]
      subject2 = subject2[0] if subject2 else ""


      if words[1][0] in ["and","or","but","so"]:
        rule = "rule11"
        response = ruleSelector(rule)(trees,words,punc)

      if response:
        return generateResponse(response,rule,debug)


      if words[1][0] == "so" and subject1 and subject2:
        if adjp and vbd and words[0].index(adjp) - 1 == words[0].index(vbd):
          rule = "rule7"
          debugPrint("rule7a")
          response = ruleSelector(rule)(trees,words,subject1,subject2,nounphrases1,nounphrases2,adjp,vbd,punc)
        else:
          rule = "rule7"
          debugPrint("rule7b")
          response = ruleSelector(rule)(trees,words,subject1,subject2,nounphrases1,nounphrases2,adjp,vbd,punc)
      if response:
        return generateResponse(response,rule,debug)


      if words[1][0] == "indeed" and subject1 and subject2:
        rule = "rule9"
        response = ruleSelector(rule)(trees,words,subject1,subject2,nounphrases1,nounphrases2,adjp,vbd,punc)
      if response:
        return generateResponse(response,rule,debug)





    if(len(result) == 1):
      tree = [Tree.fromstring(chunkerserver(x)["result"]) for x in result][0]
      words = list(tree.flatten())
      punc = [" ".join(x.leaves()).strip() for x in tree.subtrees() if x.label() in punctuations]
      punc = punc[-1] if punc else ""

      if "not only" in text.lower() and "but also" in text.lower() and text.lower().index("not only") < text.lower().index("but also"):
        rule = "rule2"
        response = ruleSelector(rule)(tree,words,punc)

      if response:
        return generateResponse(response,rule,debug)

      subject = [" ".join(x.leaves()).strip() for x in tree.subtrees() if x.label() == "NP"]
      subject = subject[0] if subject else subject
      verb = [" ".join(x.leaves()).strip() for x in tree.subtrees() if x.label() in verbs]
      verb = verb[0] if verb else verb

      conjunction = [" ".join(x.leaves()).strip() for x in tree.subtrees() if x.label() == "CC"]
      conjunction = conjunction[0] if conjunction else ""

      sents = [" ".join(x.leaves()).strip() for x in tree.subtrees() if x.label() == "S"]

      debugPrint("subject",subject)
      debugPrint("verb",verb)
      debugPrint("conjunction",conjunction)
      debugPrint("sents",sents)


      
      if conjunction and len(sents) > 1 and conjunction not in ["but","or"]:
        rule = "rule10"
        response = ruleSelector(rule)(tree,sents,conjunction,words,punc)

      if response:
        return generateResponse(response,rule,debug)

      if conjunction in ["but","or"]:
        rule = "rule12"
        response = ruleSelector(rule)(tree,sents,conjunction,words,punc)

      if response:
        return generateResponse(response,rule,debug)

      
      if conjunction:
        rule = "rule10"
        response = ruleSelector(rule)(tree,sents,conjunction,words,punc)

      if response:
        return generateResponse(response,rule,debug)




      return (text.capitalize(),False)

      # return ", ".join(result)

    return (text.capitalize(),False)

  except Exception as e:
    debugPrint(e)
    # if os.environ.get("FLASK_ENV") and os.environ.get("FLASK_ENV") == "development":
    #   raise e
    return (text.capitalize(),False)