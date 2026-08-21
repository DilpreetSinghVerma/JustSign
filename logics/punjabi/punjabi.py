import re

HelpingVerbs = [['ਹਾਂ','ਹੈ','ਹਨ','ਹੋ'],['ਸੀ','ਸਨ'],['ਨਹੀਂ'],['ਕੀ','ਕਿੱਥੇ','ਕਦੋਂ']]
CompoundWords = ['ਜਿਵੇ', 'ਜਿਵੇਂ','ਕਿਉਕਿ',"ਕਿਉਂਕਿ","ਜਿਸਨੂੰ","ਤਾਂਕਿ" ,"ਜੋ ਕਿ", "ਪਰ",'ਕਿ','ਤਾਂ','ਅਤੇ','ਜਾਂ','ਅਤੇ','ਤੇ','ਫਿਰ ਵੀ']
stopwords=['ਕੁੱਝ']
reqiredwords=['ਜਾਂ',"ਪਰ"]
SymbolsList = ['|','?','!']
GatheredIndexVerb =[]
GatheredVerb=[]
GatheredIndexSymbol =[]
GatheredSymbol = []


def compundget(orignall):
    ListCoordinateConjunction = ['ਜਿਵੇ', 'ਜਿਵੇਂ','ਕਿਉਕਿ',"ਕਿਉਂਕਿ","ਜਿਸਨੂੰ","ਤਾਂਕਿ" ,"ਜੋ ਕਿ",'ਫਿਰ', "ਪਰ",'ਕਿ','ਤਾਂ','ਅਤੇ','ਜਾਂ','ਤੇ','ਫਿਰ ਵੀ']
    ListCoordinateConjunction1 = ['ਅਤੇ','ਤੇ','ਫਿਰ ਵੀ']
    i=0
    for x in orignall:
        for y in ListCoordinateConjunction:
            #print(i)
            i+=1
            #print(x+"--------------"+y)
            if x == 'ਜੋ' or x=='ਫਿਰ':
                m = orignall.index(x)
                if orignall[m+1]=='ਕਿ' or orignall[m+1]=='ਵੀ':
                    # print("Here")
                    try:
                        joindex = m
                        w = x
                        zz= orignall[m+1]
                        #print(w)
                    except:
                        pass
                    break

            if y == x:
                try:
                    ccindex = orignall.index(y)
                    w = y
                except:
                   pass
        if x == 'ਜੋ':
            break
    try:
        return [2,  w, zz, joindex, joindex+1]
    except:
        pass
    try:
        return [1, w, ccindex]
    except:
        return [0]




def remove_stopwords(sen):
    for x in stopwords:
        sen=sen.replace(x,'')
    return sen
def sic(ParaRecieved):
    # WordsArray = ParaRecieved.split()
    for Word in CompoundWords:
        LocationOfCompound = ParaRecieved.find(Word)
        #print(Word)
        if not(LocationOfCompound == -1):
            SplitWord = Word
            break
        else:
            SplitWord = "-1"
    #print(SplitWord)
    SplittedLines = ParaRecieved.split(SplitWord)
    SplittedLines[0]+=" ।"
    return SplittedLines

def TellType(line):
    HasExclamation = False
    HasImperitive = False
    HasSimple = False
    HasNegative = False
    x = line.find('!')
    if x != -1 :
        HasExclamation = True
    x = line.find('|')
    if x != -1 :
        HasSimple = True
    x = line.find('।')
    if x != -1 :
        HasSimple = True
    x = line.find('?')
    if x != -1 :
        HasImperitive = True
    x = line.find('ਨਹੀਂ')
    if x != -1 :
        HasNegative = True
    return HasNegative,HasExclamation,HasImperitive,HasSimple

def TranslateSimple(line):
    line=line.replace('|', ' |')
    line=line.replace('।', ' ।')
    line=line.replace('?', ' ?')
    line=line.replace('!', ' !')
    LineRecievedArray = line.split()
    try :
        i=0
        stop = len(LineRecievedArray)
        while i < stop :
            if LineRecievedArray[i] == '?':
                LineRecievedArray.remove('?')
                stop = len(LineRecievedArray)
            if LineRecievedArray[i]=='ਹਾਂ|' or LineRecievedArray[i]=='ਹੈ|' or LineRecievedArray[i]=='ਹਨ|'or LineRecievedArray[i]== 'ਹੋ|' or LineRecievedArray[i]== 'ਹੀ|':
                LineRecievedArray.pop(i)
                LineRecievedArray.insert(len(LineRecievedArray),'|')
                stop = len(LineRecievedArray)
            if LineRecievedArray[i]=='ਲਾ' or LineRecievedArray[i]=='ਜਾ' or LineRecievedArray[i]=='ਲਵੋ':
                    if LineRecievedArray[i+1]=='|' or LineRecievedArray[i+1]=='।' :
                        LineRecievedArray.pop(i)
                        stop = len(LineRecievedArray)
            if LineRecievedArray[i]=='ਹਾਂ' or LineRecievedArray[i]=='ਹੈ' or LineRecievedArray[i]=='ਹਨ' or LineRecievedArray[i]=='ਸੀ' or LineRecievedArray[i]=='ਸਨ' or LineRecievedArray[i]== 'ਹੋ' or LineRecievedArray[i]== 'ਹੀ':
                    if LineRecievedArray[len(LineRecievedArray)-1]=='ਨਹੀਂ':
                        LineRecievedArray.insert(len(LineRecievedArray),'|')
                    LineRecievedArray.pop(i)
                    stop = len(LineRecievedArray)
            if LineRecievedArray[len(LineRecievedArray)-1]=='ਨਹੀਂ':
                if LineRecievedArray[i]=='ਸੀ' or LineRecievedArray[i]=='ਸਨ':
                    if LineRecievedArray[i+1]=='|' or LineRecievedArray[i+1]=='?' or LineRecievedArray[i+1]=='।':
                        LineRecievedArray.insert(len(LineRecievedArray),LineRecievedArray[i+1])
                        LineRecievedArray.pop(i+1)
                    stop = len(LineRecievedArray)
            if LineRecievedArray[len(LineRecievedArray)-1]=='!':
                if LineRecievedArray[i]=='ਹਾਂ' or LineRecievedArray[i]=='ਹੈ' or LineRecievedArray[i]=='ਹਨ':
                    LineRecievedArray.pop(i)
                    stop = len(LineRecievedArray)
            i=i+1
        SimpleResult = ' '.join(LineRecievedArray)
        return SimpleResult
    except ValueError :
        SimpleResult = "Element not in list !"
        return SimpleResult

def TranslateNegative(line):
    line=line.replace('|', ' |')
    line=line.replace('।', ' ।')
    line=line.replace('?', ' ?')
    line=line.replace('!', ' !')
    LineRecievedArray = line.split()
    try :
        i=0
        stop = len(LineRecievedArray)
        while i < stop :
            if LineRecievedArray[i]=='ਨਹੀਂ':
                LineRecievedArray.insert(len(LineRecievedArray),'ਨਹੀਂ')
                LineRecievedArray.pop(i)
                stop = len(LineRecievedArray)
            i=i+1
        NegativeResult = ' '.join(LineRecievedArray)
        NegativeResult=NegativeResult.replace('|', '')
        NegativeResult=NegativeResult.replace('।', '')
        NegativeResult=NegativeResult.replace('?', '')
        #print(NegativeResult)
        NegativeResult = TranslateSimple(NegativeResult)
        #print(NegativeResult)
        return NegativeResult
    except ValueError :
        NegativeResult = "Element not in list !"
        return NegativeResult

def TranslateImperitive(line):
    line=line.replace('?', '')
    LineRecievedArray = line.split()
    try :
        i=0
        stop = len(LineRecievedArray)
        while i < stop :
            x = re.search("ਕਿ.*", LineRecievedArray[i])
            if LineRecievedArray[i]=='ਕੀ' or x or LineRecievedArray[i]=='ਕੌਣ' or LineRecievedArray[i]=='ਕਦੋਂ':
                LineRecievedArray.insert(len(LineRecievedArray),LineRecievedArray[i])
                LineRecievedArray.pop(i)
                stop = len(LineRecievedArray)
            if(LineRecievedArray[i]=='ਹੋ'):
                LineRecievedArray.pop(i)
                stop = len(LineRecievedArray)
            i=i+1
        ImperitiveResult = ' '.join(LineRecievedArray)
        ImperitiveResult=ImperitiveResult.replace('?', '')
        #print(ImperitiveResult)
        ImperitiveResult = TranslateSimple(ImperitiveResult)
        #print(ImperitiveResult)
        return ImperitiveResult
    except ValueError :
        ImperitiveResult = "Element not in list !"
        return ImperitiveResult

def TranslateExclamatory(line):
    line=line.replace('!', ' !')
    LineRecievedArray = line.split()
    #print(LineRecievedArray)
    try :
        i=0
        stop = len(LineRecievedArray)
        while i < stop :
            if LineRecievedArray[i]=='!':
                rev=i
                m=0
                while rev >= 0:
                    LineRecievedArray.insert(len(LineRecievedArray)-m,LineRecievedArray[rev])
                    LineRecievedArray.pop(rev)
                    m=m+1
                    rev=rev-1
                stop = len(LineRecievedArray)
            i=i+1

        ExclamatoryResult = ' '.join(LineRecievedArray)
        #print("res :"+ExclamatoryResult)
        ExclamatoryResult = TranslateSimple(ExclamatoryResult)
        #print(ExclamatoryResult)
        return ExclamatoryResult
    except ValueError :
        ExclamatoryResult = "Element not in list !"
        return ExclamatoryResult

def MiddleThing(IsSimple,IsNegative,IsImperitive,IsExclamatory,line):
    if IsImperitive :
        line = TranslateImperitive(line)
    if IsNegative and not IsImperitive:
        line = TranslateNegative(line)
    if IsExclamatory :
        line = TranslateExclamatory(line)
    if IsSimple :
        line = TranslateSimple(line)
    return line

def remove_dandi_from_first_sentence(res):
    res[0]=res[0].replace('|','')
    res[0] = res[0].replace('।', '')
    return res

def addprjan(Split,ans):
    #print(ans[len(ans)-1])
    if(ans[1] in reqiredwords):
        Split[0]+=" "+ans[len(ans)-2]
        #print("I am here")

    return Split

def reorder_neg(res):
    tempres = ["",""]
    i = 0
    while i < len(res):
        TypeTupple = TellType(res[i])
        IsNegative = TypeTupple[0]
        if IsNegative:
            tempres[len(res)-1]=res[i]
        if not(IsNegative):
            tempres[0]=res[i]
        i+=1
    return tempres

def splitcompound(OrignalSentence,wheretosplit):
    d = OrignalSentence
    noOfSubstring = wheretosplit[0]
    SplittedSen = ""
    i = 1
    while (noOfSubstring):
        m = re.split(wheretosplit[i], d)
        try:
            while (1):
                m.remove('')
        except:
            pass
        d = ''
        for x in m:
            # #print("Before strip:"+x)
            x=x.strip()
            # #print("After Strip:"+x)
            d += x
            d += "`"
        i += 1
        noOfSubstring -= 1
    # #print(d)

    t = d.split("`")
    # #print(t)
    try:
        while (1):
            t.remove('')
    except:
        pass
    return t

def appendsymbol(Split,TypeTupple):
    IsNegative = TypeTupple[0]
    IsExclamatory = TypeTupple[1]
    IsImperitive = TypeTupple[2]
    IsSimple = TypeTupple[3]
    if len(Split)>1:
        if IsImperitive:
            Split[0]+=" ?"
        if IsSimple:
            Split[0]+=" |"
    return Split
def keepSimple(res):
    #print(res)
    to_keep = ['ਉਸਨੇ','ਉਹ','ਨੇ ਕਿਹਾ' ]
    to_remove =['ਉਹ']
    dup=['ਸ਼ਹਿਰ' ,'ਜਾਵਾ' ,'ਜਾਵਾਂ']
    tr=-1
    for w in to_keep:
        x=res[0].find(w)
        if not (x == -1):
            tr=x
            trw=w
    #print("here")
    #print(tr)
    if not(tr == -1):
        for q in to_remove:
            res[1]=res[1].replace(q,'')
    return res

def test(res):
    dup=['ਸ਼ਹਿਰ' ,'ਜਾਵਾ' ,'ਜਾਵਾਂ']
    l = res.split()
    k = []
    for i in reversed(l):
        if i in dup:
            if (res.count(i) > 1 and (i not in k) or res.count(i) == 1 ):
                k.append(i)
        else:
            k.append(i)
    res=" ".join(reversed(k))
    return res


def punjabiToISL(req):
    ParaRecieved = req
    TypeTupple = TellType(ParaRecieved)
    h = TypeTupple[0]
    g = TypeTupple[2]
    res=[]
    SplittedSentenceinWords = ParaRecieved.split()
    wheretosplit = compundget(SplittedSentenceinWords)
    #print(wheretosplit)
    SplitIfCompount = splitcompound(ParaRecieved,wheretosplit)
    SplitIfCompount = appendsymbol(SplitIfCompount,TypeTupple)
    gloisneg=False
    for ParaRecieved in SplitIfCompount:
        TypeTupple = TellType(ParaRecieved)
        IsNegative = TypeTupple[0]
        IsExclamatory = TypeTupple[1]
        IsImperitive = TypeTupple[2]
        IsSimple = TypeTupple[3]
        if IsNegative:
            gloisneg=True
        res.append(MiddleThing(IsSimple,IsNegative,IsImperitive,IsExclamatory,ParaRecieved))
    #print(res)
    if len(SplitIfCompount) > 1:
        if gloisneg:
            res=reorder_neg(res)
        #print(res)
        res=remove_dandi_from_first_sentence(res)
        res = addprjan(res,wheretosplit)
        #print(res)
        res = keepSimple(res)


    res = " ".join(res)
    res = remove_stopwords(res)
    if g:
        res=TranslateImperitive(res)
    res=test(res)
    return res