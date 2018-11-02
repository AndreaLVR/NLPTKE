# -*- coding: utf-8 -*-
# NLPTKE: NLP Text Keywords Extractor
# Author: Andrea Olivari
import sys
reload(sys) 
sys.setdefaultencoding('utf8')
import nltk
import language_check
from time import sleep
from nltk.corpus import words
from nltk.stem.wordnet import WordNetLemmatizer
from pattern.text.en import singularize

PROP_CHAIN_SCORE   = 25 # Chain composed by Capital letter names
NOUN_CHAIN_SCORE   = 9  # Chain composed by [JJ](NN)..(NN)
REPETITION_SCORE   = 8
PROP_NAME_SCORE    = 8
NOUN_SCORE		   = 4
ADJECTIVE_SCORE    = 2
VERB_SCORE         = 1
LENGTH_SCORE       = 0.5 
COMMON_WORDS_NUM   = float(955213)  
MIN_COMMON_PENALTY = 0.5/COMMON_WORDS_NUM
NOT_VALID_TERM_STR = "eXTRACT_KEYW0RD5_NoT_V4LID_T3RM_5STRiNg"
CHAIN_CONJS        = ["de","&","n"] # of, in
NOCHAIN_CONJS      = ["a","at","as"]
to_discard         = [".",",",":","(",")","[","]","{","}"]
common_words_file  = "en_full.txt"
#language_tool     = language_check.LanguageTool('en-US')

def loadCommonWords():
	common_words = {}
	print "\n[*] Loading %s.." %common_words_file
	with open(common_words_file,"r") as ins:
		for line in ins:
			if(len(line) > 0 and line[0] != "#"):
				split = line.split(" ")
				word  = split[0]
				val   = int(split[1])/COMMON_WORDS_NUM
				common_words[word] = val
	print "[+] Loaded successfully."
	return common_words

def checkIfEnglishWord(word):
	return word.lower() in words.words()

def normalize(words_values):
     max_key = max(words_values, key=lambda k: words_values[k])
     max_value = words_values[max_key]
     for word in words_values:
     	words_values[word] /= max_value

def showKeywords(words_values,treshold=0):
	d_view = [(v,k) for k,v in words_values.iteritems()]
	d_view.sort(reverse=True) 
	for v,k in d_view:
		if(v > treshold): # 0 to show them all
			print "%s -> %s" %(k,v)

def validTerm(term,cat):
	#print "entro in validTerm con term='%s' e cat='%s' --> term[len(term)-1] = %s\n" %(term,cat,term[len(term)-1])
	if(term[len(term)-1] == '\'' or term[len(term)-1] == '’'):
		term = term[:-1] 
	if(len(term) == 0):
		return NOT_VALID_TERM_STR
	if((cat == "POS" or (term == cat and cat != "TO") or cat == ".") and len(term) == 1):
		return NOT_VALID_TERM_STR
	if(term[0] == '\''): # per esempio 'James is the winner' non può trascurarmi la parola James!!
		print "entro.."
		if(cat == "VBP" or cat == "VBZ" or len(term) <= 3): # 's,'d,'m','ve','ll,'re
			return NOT_VALID_TERM_STR
		else:	
			term = term[1:]
			print "term = '%s'" %term
	return term

def removeUselessTerms(result):
	for i in range(0,len(result)):
		result[i][0] = validTerm(result[i][0],result[i][1])
	return result

def convertVerbsToInfinitive(verb):
	return WordNetLemmatizer().lemmatize(verb,'v')

def addIfNotExists(lst,el):
	if(el not in lst):
		lst.append(el)

def correctSentence(sentence):
	matches = language_tool.check(sentence)
	sentence = language_check.correct(sentence,matches)
	return sentence

def listOfTuplesToListOfLists(lt):
	ll = []
	for t in lt:
		ll.append(list(t))
	return ll

def removeNtIssue(l):
	for i in range(0,len(l)):
		if(i < (len(l)-1) and (l[i][0] == "ca" or l[i][0] == "wo") and l[i+1][0] == "n't"):
			l[i][0] = "can" if l[i][0] == "ca" else "will"
		elif(l[i][0] == "n't"):
			l[i][0] = "not"
	return l

def convertSpecialCasesWord(word):
	if(word == "an"):
		return "a"
	return word

def increaseValueIfExistsElseAdd(sentence,dic):
	if(sentence in dic):
		dic[sentence] += 1
	else:
		dic[sentence] = 1

def removePOSFromResult(result):
	newresult = []
	for pair in result:
		if(pair[1] != "POS"):
			newresult.append([pair[0],pair[1]])
	return newresult

def get_keywords(sentence): 
	if(sentence[len(sentence)-1] != '.'):
		sentence = "%s." %sentence
	text = nltk.word_tokenize(sentence)
	result = nltk.pos_tag(text)
	result = listOfTuplesToListOfLists(result)
	result = removeNtIssue(result)
	print "len(result) = %s" %len(result)
	print result
	result = removeUselessTerms(result)
	result = removePOSFromResult(result)
	print "\n\n%s\n" %result

	words_repetition = {}
	words_values = {}
	chain = ""
	chain_words = 0
	last_chain_term_type = None
	noun_chain = ""
	noun_chain_nouns = 0
	noun_chain_words = 0	
	chains = []
	verbs_found = []
	index = 0

	for term in result:
		is_chain = False
		score = len(term[0])*LENGTH_SCORE
		if(noun_chain_nouns <= 1 and "JJ" in term[1]):
			noun_chain = "%s %s" %(noun_chain,term[0])
			noun_chain_words += 1
		elif(noun_chain_nouns == 1 and "IN" in term[1] and term[0] not in NOCHAIN_CONJS):
			noun_chain = "%s %s" %(noun_chain,term[0])
			noun_chain_words += 1
			last_chain_term_type = "IN"
		elif(last_chain_term_type == "IN" and term[1] == "DT" and term[0] not in NOCHAIN_CONJS):
			noun_chain = "%s %s" %(noun_chain,term[0])
			noun_chain_words += 1
		elif("NN" in term[1]): #or term[1] == "NN" or term[1] == "NNS"):
			noun_chain = "%s %s" %(noun_chain,term[0])
			print "noun_chain = %s" %noun_chain
			noun_chain_words += 1
			noun_chain_nouns += 1
		else:	
			noun_chain = noun_chain.strip()
			if(noun_chain_words > 1):
				last_chain_term_type = None
				print "\nFound NOUN CHAIN -> '%s'\n" %noun_chain
				words_values[noun_chain] = (len(noun_chain)-(noun_chain_words-1)+noun_chain_words)*LENGTH_SCORE+NOUN_CHAIN_SCORE*noun_chain_nouns/float(noun_chain_words)
				chains.append(noun_chain)
				increaseValueIfExistsElseAdd(noun_chain,words_repetition)
			noun_chain = ""
			noun_chain_words = 0
			noun_chain_nouns = 0
		if(term[0][0].isupper()):
			chain = "%s %s" %(chain,term[0])
			chain_words += 1
		else:	
			if(chain_words >= 1 and term[0] in CHAIN_CONJS):
				chain = "%s %s" %(chain,term[0])
				chain_words += 1
			else:	
				if(len(chain) > 0):
					if(chain_words > 1):
						chain = chain.strip()
						print "chain = %s" %chain
						chain_split = chain.split(" ")
						while(chain_split[len(chain_split)-1] in CHAIN_CONJS):
							del chain_split[-1]
							chain_words -= 1
						chain = ""
						for chain_piece in chain_split:
							chain = "%s %s" %(chain,chain_piece)
						chain = chain.strip()
						print "new chain = %s" %chain
						if(chain_words == 1):
							is_chain = False
							words_values[chain] = (len(chain)-(chain_words-1))*LENGTH_SCORE+PROP_NAME_SCORE
						else:
	 						is_chain = True
							chain_score = (len(chain)-(chain_words-1)+chain_words)*LENGTH_SCORE+PROP_CHAIN_SCORE
							chains.append(chain)
							print "words_values[%s] = %s" %(chain,chain_score)
							words_values[chain] = chain_score
							print "'%s' (CHAIN) -> %s" %(chain,chain_score)
						increaseValueIfExistsElseAdd(chain,words_repetition)
					chain = ""
					chain_words = 0

		cat = term[1]
		vterm = term[0] #validTerm(term[0],cat) 
		if(vterm != NOT_VALID_TERM_STR):
			if("NNP" in cat):
				score += PROP_NAME_SCORE
			elif("NN" in cat and "NNP" not in cat):
				score += NOUN_SCORE
			elif("JJ" in cat):
				score += ADJECTIVE_SCORE
			elif("VB" in cat):
				score += VERB_SCORE
				addIfNotExists(verbs_found,vterm)

			increaseValueIfExistsElseAdd(term[0],words_repetition)
			if(vterm in words_values):
				#print "%s è già in words_values" %vterm
				if(words_values[vterm] < score):
					#print "ma ha uno score inferiore a quello corrente, quindi sostituisco"
					words_values[vterm] = score
					if(vterm in verbs_found):
						#print "rimuovo '%s' da verbs_found" %vterm
						verbs_found.remove(vterm)   
			else:
				words_values[vterm] = score
		index += 1

	for word in words_values:
		words_values[word] += words_repetition[word]*REPETITION_SCORE

	useless_chains = []
	for chain in chains:
		cchain = chain.lower()
		for other_chain in chains:
			cother_chain = other_chain.lower()
			if chain != other_chain and cchain in cother_chain and words_values[other_chain] >= words_values[chain]:
				useless_chains.append(chain)
				break  
		words_split = chain.split(" ")
		for word in words_split:
			try:
				if(words_values[word] < words_values[chain]):
					del words_values[word]
			except:
				continue

	for chain in useless_chains:
		try:
			del words_values[chain]
		except:
			pass

	print ""
	for word in words_values:
		check_word = convertSpecialCasesWord(word)
		if(check_word in common_words):
			#print "words_values['%s'] -> %s / %s" %(word,words_values[word],common_words[word])
			words_values[word] /= float(common_words[check_word])
		else:	
			done = False
			if(word in verbs_found): 
				inf_verb = convertVerbsToInfinitive(word)
				print "converting '%s' -> '%s'" %(word,inf_verb)
				if(inf_verb in common_words):
					#print "words_values['%s'] -> %s / %s" %(word,words_values[word],common_words[inf_verb])
					words_values[word] /= float(common_words[inf_verb])
					done = True
			else: 
				singular_word = singularize(word)
				if(singular_word in common_words):
					#print "words_values['%s'] -> %s / %s" %(word,words_values[word],common_words[singular_word])
					words_values[word] /= float(common_words[singular_word])
					done = True 
			if(done is False): 
				#print "words_values['%s'] -> %s / %s" %(word,words_values[word],MIN_COMMON_PENALTY)
				words_values[word] /= float(MIN_COMMON_PENALTY)

	print "\nwords_values:\n%s\n" %words_values
	normalize(words_values)
	print "\nNormalized words_values: \n"
	showKeywords(words_values,0.1)


ifile = open("nlptke_input.txt","r")	
text  = ifile.read()
ifile.close() 
common_words = loadCommonWords()
print "\n"

#text = "Will has to win. will you win for me? I'll win. I don't know you. Francis' house is wonderful & but I can't afford it. I'd like to say 'I haven't the best'. the reason that's the best verison is because it's very obvious what you want to do, and you won't confuse yourself or whoever else is going to come in contact with that code later."
#text = "Real Madrid Club de Fútbol, commonly known as Real Madrid, or simply as Real outside Spain frontiers, is a professional football club based in Madrid, Spain."
#text = "Guns' n Roses is an American hard rock band from Los Angeles formed in 1985, but I love Alice In Chains too."
#text = """In reality, John and Jane are both skilled contract killers working for different firms, both among the best in their field, each concealing their true professions from one another. The couple live in a large Colonial Revival house in the suburbs and, to keep up appearances, socialise with their "conventionally" wealthy (and disliked by each Smith) neighbors."""
#text = "Arch Enemy is a Swedish melodic death metal band, originally a supergroup, from Halmstad, formed in 1996. Arch Enemy's members were in bands such as Carcass, Armageddon, Carnage, Mercyful Fate, Spiritual Beggars, Nevermore, supergroup and Eucharist. It was founded by Carcass guitarist Michael Amott along with supergroup, Johan Liiva, who were both originally from the influential death metal band Carnage. The band has released ten studio albums, three live albums, three video albums and four EPs. The band was originally fronted by Johan Liiva, who was replaced by German Angela Gossow as lead vocalist in 2000. Gossow left the band in March 2014 and was replaced by Canadian Alissa White-Gluz, while remaining as the group's manager."
#text = "this year we had some food security, but also a incredibile forest management. foods are fundamental."
#text = "melodic death metal band called Arch Enemy will play tonight at Live Club. personally I prefer W.A.S.P. but they are as good as them. anyway W.A.S.P. has the great vocalist Blackie Lawless, which is one of the best singers ever."
#text = "in 1975, Gates and Allen launched Microsoft, which became the world's largest PC software company. during his career at Microsoft, Gates held the positions of chairman, CEO and chief software architect, while also being the largest individual shareholder until May 2014. Gates stepped down as chief executive officer of Microsoft in January 2000, but he remained as chairman and created the position of chief software architect for himself. in June 2006, Gates announced that he would be transitioning from full-time work at Microsoft to part-time work and full-time work at the Bill & Melinda Gates Foundation. he gradually transferred his duties to Ray Ozzie and Craig Mundie. he stepped down as chairman of Microsoft in February 2014 and assumed a new post as technology adviser to support the newly appointed CEO Satya Nadella."
get_keywords(text)



