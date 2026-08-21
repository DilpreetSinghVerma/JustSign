import os
import re

from nltk.tree import Tree
from pattern.en import conjugate, lemma, lexeme, PRESENT, PAST, FUTURE, singularize

from logics.chunker import chunkerserver
from logics.sentencereplacements import getSimpleSentenceReplacements

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
  "much how":"how much",
}

punctuations = ["SYM", "LS", ".", "!", "?", ",", ":", "(", ")", "\"", "#", "$"]
possesivedeterminers = {"i":"my","you":"your","he":"his","she":"her","it":"its","we":"our","they":"their","one":"one's"}
possesivepronouns = {"i":"mine","you":"yours","he":"his","she":"hers","it":"its","we":"ours","they":"theirs","one":"one's"}
objects = {"i":"me","you":"you","he":"him","she":"her","it":"it","we":"us","they":"them","one":"one"}
negations = {"am":"ain't", "are":"aren't", "can":"can't", "could":"couldn't", "dare":"daren't", "did":"didn't", "does":"doesn't", "do":"don't", "had":"hadn't", "has":"hasn't", "have":"haven't", "is":"isn't", "may":"mayn't", "might":"mightn't", "must":"mustn't", "need":"needn't", "ought":"oughtn't", "shall":"shan't", "should":"shouldn't", "was":"wasn't", "were":"weren't", "will":"won't", "would":"wouldn't",}
contractions = {"ain't":"am not","daren't":"dare not","mayn't":"may not","shan't":"shall not","isn't":"is not","aren't":"are not","wasn't":"was not","weren't":"were not","haven't":"have not","hasn't":"has not","hadn't":"had not","won't":"will not","wouldn't":"would not","don't":"do not","doesn't":"does not","didn't":"did not","can't":"can not","couldn't":"could not","shouldn't":"should not","mightn't":"might not","mustn't":"must not","would've":"would have","should've":"should have","could've":"could have","might've":"might have","must've":"must have","i'm":"i am","you're":"you are","he's":"he is","she's":"she is","it's":"it is","'tis it":"is","we're":"we are","they're":"they are","that's":"that is","who's":"who is","what's":"what is","what're":"what are","where's":"where is","when's":"when is","why's":"why is","how's":"how is","i'll":"i will","you'll":"you will","he'll":"he will","she'll":"she will","it'll":"it will","we'll":"we will","they'll":"they will","that'll":"that will","who'll":"who will","what'll":"what will","where'll":"where will","when'll":"when will","why'll":"why will","how'll":"how will","i'd":"i would","you'd":"you would","he'd":"he would","she'd":"she would","it'd":"it would","we'd":"we would","they'd":"they would","that'd":"that would","who'd":"who would","what'd":"what would","where'd":"where would","when'd":"when would","why'd":"why would","how'd":"how would","i've":"i have","you've":"you have","we've":"we have","they've":"they have","ma'am":"madam","'twas":"it was","she\'d\'ve":"she would have","\'tisn\'t":"it is not","there's":"there is",}

objectification = {possesivedeterminers[x]:x for x in possesivedeterminers}
objectification.update({possesivepronouns[x]:x for x in possesivepronouns})
objectification.update({objects[x]:x for x in objects})

removals = ["is", "am", "are", "shall", "will", "did"]
removal_tags = ["TO",]


removal_tag_words = {
  "DT" : ["a", "an", "the"],
  "CC" : ["and", "or", "for", "so"],
  "IN" : ["although", "as" ,"at", "because", "by", "how", "if", "of", "once", "since", "than", "that", "though", "till", "until", "when", "where", "whether", "while","with", "unless","in", "for","from"],
  "MD" : ["can", "could", "may", "might", "must", "ought", "shall", "should", "will", "would", "dare"],
  "UH" : ["my", "oh", "o", "please", "see", "ouch", "uh-huh", "uh", "um", "umm", "eh", "er", "hmm", "alas", "dear", "well", "yes", "hello", "hullo"],
  "VBZ" : ["be","is", "am", "are", "was", "were", "been", "has", "have"],
  "VBD" : ["be","is", "am", "are", "was", "were", "been", "has", "have"],
  "VBG" : ["be","is", "am", "are", "was", "were", "been", "has", "have"],
  "VBP" : ["be","is", "am", "are", "was", "were", "been", "has", "have"],
  "VBN" : ["be","is", "am", "are", "was", "were", "been", "has", "have"],
  "RB" : [],
}





noun_types = ["NN","NNS","NNP","NNPS","NP"]
pronoun_types = ["PR", "PRP", "PRP$"]
verb_types = ["VB","VBD","VBG","VBN","VBP","VBZ","VP"]
adjective_types = ["JJ","JJR","JJS"]
adverb_types = ["RB","RBR","RBS"]

wh_words = ["who", "where", "why", "when", "how", "what", "which", "whose", "whom"]


def generateResponse(text,debug):

  # db = get_db().cursor()
  # synonyms =  db.execute("select * from synonyms")
  # for row in synonyms:
  #   text = re.sub(r"\b%s\b" % row['word'], row['replacement'], text)
  text = text.lower().split(" ")
  text = " ".join([x for i,x in enumerate(text) if i == len(text) - 1 or text[i] != text[i+1]])

  response = text.replace(" my "," i ")
  response = re.sub(r"\bi i\b","i",response)
  response = re.sub(r"\bmuch how\b","how much",response)
  response = response.capitalize()
  response = response.replace(" i "," I ")
  response = re.sub(r" ([^\w\d])",r"\1",response)
  response = re.sub(r" +"," ",response)
  debugPrint("Generated Response:",response)
  return response

def debugPrint(*args):
  if os.environ.get("FLASK_ENV") and os.environ.get("FLASK_ENV") == "development":
    print(*args)

def simpleToISL(text,debug=False):
  debugPrint("Running Simple to ISL Module")
  sentreplacements = getSimpleSentenceReplacements() 
  for sent in sentreplacements:
    if re.sub(r"[^a-zA-Z0-9]","",text.lower()).strip() == re.sub(r"[^a-zA-Z0-9]","",sent["sent"].lower()).strip():
      return (sent["repl"].capitalize(),True)

  
  original_text = text.strip()
  for c in contractions.keys():
    text = re.sub(r"\b%s\b" % c, contractions[c],text.lower())
  text = text.replace(";",".")
  text = text.lower().strip()
  for x in ["in spite of"]:
    if text.startswith(x):
      text = text[text.index(x)+len(x):]
      if text.count(","):
        comma = text.index(",")
        if "also" in text[comma:]:
          text = text.replace(",",", plus",1)
        else:
          if " still " in text:
            text = text.replace(" still "," ")
          text = text.replace(",",", still",1)
  if "that" in text:
    text = re.sub(r"\b%s\b" % "that",",",text)
    text = "what " + text
  if "yet" in text:
    text = re.sub(r"\b%s\b" % "yet","but",text)
  if re.findall(r"[\.\,]\s*or",text):
    debugPrint(re.findall(r"[\.\,]\s*or",text))
  results = chunkerserver(text)["result"]
  results = ["(ROOT" + x.strip() for x in results.split("(ROOT") if x]
  final = [simpleToISLConvert(Tree.fromstring(x)) for x in results]
  return ("\n".join(final).strip(),True)


def simpleToISLConvert(trees,debug=False):
  try:
    text = " ".join(list(trees.flatten())).lower()
    words = text.split(" ")
    tags = [str(x)[1:-1].split(" ")[1]+"/"+str(x)[1:-1].split(" ")[0] for x in trees.subtrees() if str(x).count("(") == 1 ]

    wh_word = None
    wh_index = None
    not_word = None
    not_index = None
    please_word = None
    please_index = None

    if words[0] == "please":
      please_word = "please/VB"
      please_index = 0
      words = words[1:]
      tags = tags[1:]

    

    if "please" in words and not please_word:
      i = words.index("please")
      del words[i]
      del tags[i]
      please_index = i
      please_word = "please/RB"



    if words[0] in wh_words:
      wh_word = tags[0]
      wh_index = 0
      words = words[1:]
      tags = tags[1:]


    for nots in ["not","n't","no","nor"]:
      if nots in words:
        i = words.index(nots)
        del words[i]
        del tags[i]
        if i > 0:
          del words[i-1]
          del tags[i-1]
        not_index = i
        not_word = "not/RB"
        break




    punc = tags[-1] if words[-1] in punctuations else None

    if punc:
      words = words[:-1]
      tags = tags[:-1]


    if not_word:
      if "," in words:
        if words.index(",") >= not_index:
          i = words.index(",")
          words.insert(i,not_word.split("/")[0])
          tags.insert(i,not_word)
        else:
          words.append(not_word.split("/")[0])
          tags.append(not_word)
      else:
        words.append(not_word.split("/")[0])
        tags.append(not_word)

    if wh_word:
      if "," in words:
        if words.index(",") >= wh_index:
          i = words.index(",")
          words.insert(i,wh_word.split("/")[0])
          tags.insert(i,wh_word)
        else:
          words.append(wh_word.split("/")[0])
          tags.append(wh_word)
      else:
        words.append(wh_word.split("/")[0])
        tags.append(wh_word)

    if please_word:
      if "," in words:
        if words.index(",") >= please_index:
          i = words.index(",")
          words.insert(i,please_word.split("/")[0])
          tags.insert(i,please_word)
        else:
          words.append(please_word.split("/")[0])
          tags.append(please_word)
      else:
        words.append(please_word.split("/")[0])
        tags.append(please_word)

    if punc:
      words.append(punc.split("/")[0])
      tags.append(punc)


    for i in range(len(words)):
      if words[i].endswith("ing") and tags[i].split('/')[1] in ["VBG"]:
        words[i] = lemma(words[i])
        tags[i] = f"{words[i]}/{tags[i].split('/')[1]}"

    for i in range(len(words)):
      if words[i].endswith("es") and tags[i].split('/')[1] in ["VBZ"]:
        words[i] = lemma(words[i])
        tags[i] = f"{words[i]}/{tags[i].split('/')[1]}"
      # if words[i] not in ["our","us"]:
      #   words[i] = singularize(words[i])
      #   tags[i] = f"{words[i]}/{tags[i].split('/')[1]}"

    # for i in range(len(words)):
    #   if words[i] in objectification.keys():
    #     words[i] = objectification[words[i]]
    #     tags[i] = f"{words[i]}/{tags[i].split('/')[1]}"


    for i in range(len(words) - 1):
      if tags[i].endswith("/CD"):
        tempt = tags[i]
        tempw = words[i]
        if tags[i+1].split("/")[1] not in punctuations and tags[i+1].split("/")[1] not in ["CC"]:
          tags[i] = tags[i+1]
          tags[i+1] = tempt
          words[i] = words[i+1]
          words[i+1] = tempw


    

    i = 0

    while i < len(words) - 1:
      if tags[i].split("/")[1] == "NN" and tags[i+1].split("/")[1] == "NN" and not re.match(r"i\.*",words[i]) and not re.match(r"i\.*",words[i+1]):
        words[i] = f"{words[i]}_{words[i+1]}"
        tags[i] = f"{words[i]}/NN"
        del words[i+1]
        del tags[i+1]
        i = i - 1
      i = i + 1

    for w in removals:
      while w in words:
        i = words.index(w)
        del words[i]
        del tags[i]
    
    for t in removal_tags:
      for j,tag in enumerate(tags):
        if tag.endswith(f"/{t}"):
          i = j
          del words[j]
          del tags[j]

    for tw in removal_tag_words.keys():
      tws = removal_tag_words[tw]
      for ws in tws:
        while f"{ws}/{tw}" in tags:
          i = tags.index(f"{ws}/{tw}")
          del words[i]
          del tags[i]


    i = 0
    new_words = []
    new_tags = []
    add_ignore = False
    while i < len(words) - 1:
      if tags[i].split("/")[1] in verb_types and (tags[i+1].split("/")[1] in noun_types or tags[i+1].split("/")[1] in pronoun_types):
        new_words.append(words[i+1])
        new_tags.append(tags[i+1])
        new_words.append(words[i])
        new_tags.append(tags[i])
        if i == len(words) - 2:
          add_ignore = True
        else:
          i = i + 1
      else:
        new_words.append(words[i])
        new_tags.append(tags[i])
      i = i + 1
    if not add_ignore:
      new_words.append(words[i])
      new_tags.append(tags[i])
    words = new_words
    tags = new_tags

    i = 0
    new_words = []
    new_tags = []
    add_ignore = False
    while i < len(words) - 1:
      if tags[i].split("/")[1] in adjective_types and tags[i+1].split("/")[1] in noun_types:
        new_words.append(words[i+1])
        new_tags.append(tags[i+1])
        new_words.append(words[i])
        new_tags.append(tags[i])
        if i == len(words) - 2:
          add_ignore = True
        else:
          i = i + 1
      elif tags[i].split("/")[1] in verb_types and tags[i+1].split("/")[1] in adjective_types:
        new_words.append(words[i+1])
        new_tags.append(tags[i+1])
        new_words.append(words[i])
        new_tags.append(tags[i])
        if i == len(words) - 2:
          add_ignore = True
        else:
          i = i + 1
      elif tags[i].split("/")[1] in verb_types and tags[i+1].split("/")[1] in noun_types:
        new_words.append(words[i+1])
        new_tags.append(tags[i+1])
        new_words.append(words[i])
        new_tags.append(tags[i])
        if i == len(words) - 2:
          add_ignore = True
        else:
          i = i + 1
      elif tags[i].split("/")[1] in verb_types and tags[i+1].split("/")[1] == "IN" and tags[i+2].split("/")[1] in noun_types:
        new_words.append(words[i+2])
        new_tags.append(tags[i+2])
        new_words.append(words[i+1])
        new_tags.append(tags[i+1])
        new_words.append(words[i])
        new_tags.append(tags[i])
        if i == len(words) - 3:
          add_ignore = True
        else:
          i = i + 2
      elif tags[i].split("/")[1] in adverb_types and tags[i+1].split("/")[1] in noun_types:
        new_words.append(words[i+1])
        new_tags.append(tags[i+1])
        new_words.append(words[i])
        new_tags.append(tags[i])
        if i == len(words) - 2:
          add_ignore = True
        else:
          i = i + 1
      elif tags[i].split("/")[1] in adverb_types and tags[i+1].split("/")[1] in adjective_types and words[i] != "very":
        new_words.append(words[i+1])
        new_tags.append(tags[i+1])
        new_words.append(words[i])
        new_tags.append(tags[i])
        if i == len(words) - 2:
          add_ignore = True
        else:
          i = i + 1
      elif tags[i].split("/")[1] in adverb_types and tags[i+1].split("/")[1] in verb_types:
        new_words.append(words[i+1])
        new_tags.append(tags[i+1])
        new_words.append(words[i])
        new_tags.append(tags[i])
        if i == len(words) - 2:
          add_ignore = True
        else:
          i = i + 1
      elif tags[i].split("/")[1] in adjective_types and (tags[i+1].split("/")[1] in verb_types or tags[i+1].split("/")[1] in noun_types) and i == len(words) - 2:
        new_words.append(words[i+1])
        new_tags.append(tags[i+1])
        new_words.append(words[i])
        new_tags.append(tags[i])
        if i == len(words) - 2:
          add_ignore = True
        else:
          i = i + 1
      else:
        new_words.append(words[i])
        new_tags.append(tags[i])
      i = i + 1
    if not add_ignore:
      new_words.append(words[i])
      new_tags.append(tags[i])
    words = new_words
    tags = new_tags



    debugPrint("words",words)
    debugPrint("tags",tags)

    sentence = " ".join(words)
    debugPrint("returning")
    if sentence:
      if text.startswith("at"):
        if sentence.startswith("time") or sentence.startswith("age"):
          sentence = " ".join(sentence.split(" ")[1:])
        return generateResponse(str("when " + sentence),debug)
      return generateResponse(sentence,debug)
    
    return text.capitalize()

  except Exception as e:
    debugPrint(e)
    # if os.environ.get("FLASK_ENV") and os.environ.get("FLASK_ENV") == "development":
    #   raise e
    return text.capitalize()