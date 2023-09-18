import pandas as pd 

five_word_lists = pd.read_csv("validated__words.csv")
five_word_lists.columns=['words']
five_word_lists['words'] =  five_word_lists.words.str.lower()

WORDSERIES = five_word_lists[['words']].drop_duplicates()


def genScore( guess, answer ):
    ## if that spot is the letter, score = 2 
    ## if the letter is taken elsewhere, i.e has a score of 2, score = 0
    ## if the letter is in the word,  score = 1
    ## if the letter is not in the word, score = 0 

    score = {}

    reduced_answer = answer[:]
    
    for i in range(5):

        if guess[i] == answer[i]:
            score[i] = "2"
            reduced_answer = reduced_answer[:i] + "_" + reduced_answer[i+1:]
            
        elif guess[i] not in answer:
            score[i] = "0"

    for i in range(5):
        if i not in score.keys():
            position = reduced_answer.find( guess[i] )

            if position == -1:
                score[i] = "0"
            else:
                score[i] = "1"
                reduced_answer = reduced_answer[:position]+"_"+reduced_answer[ position+1:]

    
    #         # else:
    #         # score = score + "0"

    
    # scoreDict = {}

    # for s, letter in zip(score, guess):
    #     scoreDict[ letter ] = max( int(s), scoreDict.get(letter, 0) )
    
    # newScore = score
    # for i in range(5):
    #     if scoreDict[ guess[i] ] > int( score[i] ) :
            # newScore = newScore[:i] +"0" + newScore[i+1:]
    
    
    return "".join( [ score[i] for i in range(5) ] )

## filter for the choice of words 
def nextChoices( wordList, guess, scores ):
    scoreOfGuessGivenAnswer = wordList.words.apply( lambda x: genScore( guess, x ) ) 

    return wordList[ scoreOfGuessGivenAnswer == scores ]

def genGuessImpact( guess, wdList ):
#     wdList = wdList.copy()
#     wdList['score'] = 
    score_count = wdList.groupby( wdList.words.apply( lambda x: genScore(guess, x) ) )['words'].count()
    # print( score_count)

    nextLen = ( (score_count) * ( score_count)  ).sum() / len(wdList) 
    return nextLen


def genBestGuess( wordList ):
    
    # eachGuessImpact = wordList.words.apply( lambda x: genGuessImpact( x, wordList ) )
    
    bestGuess = bestSolver(wordList, wordList) # wordList.loc[ eachGuessImpact == eachGuessImpact.min() ,'words' ].values[0]
    
    return bestGuess

def bestSolver( choiceSpace, answerSpace ):
    
    if len( answerSpace ) == 1:
        return answerSpace.words.values[0]

    eachGuessImpact = choiceSpace.words.apply( lambda x: genGuessImpact( x, answerSpace ) )
    
    bestGuess = choiceSpace.loc[ eachGuessImpact == eachGuessImpact.min() ,'words' ].values[0]
    return bestGuess

def _isGoodGuess( self, guess ):
    pass



class Wordle():

    def __init__(self):
        self.guess = []
        self.scores = []
        self.allWords = WORDSERIES
        self.answer = self.allWords.words.sample(1).values[0] ## will be replaced 
        self.choiceSpace = self.allWords
        self.hint = "raise"

        self.mode = "WORDLE" ## "SOLVER" 
    
    def reset(self, mode="WORDLE"):
        self.answer = self.allWords.words.sample(1).values[0]
        self.guess = []
        self.scores = []
        self.choiceSpace = self.allWords
        self.hint = "raise"
        self.mode = mode ## "SOLVER" 


    def getGuess( self, currentGuess ):
        # print("--------------------------")
        # print("Enter Your %s Guess:" % i )
        # print("--------------------------")
        # currentGuess = input()
        self.guess.append( currentGuess )

        return currentGuess
    def getScore ( self, guess ):
        currentScore = genScore( guess, self.answer )
        self.scores.append( currentScore )

        return currentScore 
    
    def updateChoices( self, guess, score ):
        self.choiceSpace = nextChoices( self.choiceSpace , guess, score )

        return self.choiceSpace
    
    ## check if it's a valid guess 
    def seeNextChoices( self, guess, score  ):
        return nextChoices( self.choiceSpace , guess, score )
    

    def genHint( self ):

        if len ( self.guess ) == 0:
            return self.hint 
        else:
            self.hint = genBestGuess( self.choiceSpace  )

        return self.hint 
    
    def genSlowHint( self ):

        if len ( self.guess ) == 0:
            return self.hint 
        else:
            self.hint = bestSolver( self.allWords, self.choiceSpace  )

        return self.hint 
    
    def genHintOptimal( self ):
        if len ( self.guess ) == 0:
            return self.hint 

        elif sum( [int(i) for i in self.scores[-1] ]) >=6 :
            self.hint = bestSolver( self.allWords, self.choiceSpace  )
        else:
            self.hint = genBestGuess( self.choiceSpace  )

        return self.hint 
    
    def printCurrent( self ):
        for guess, score in zip ( self.guess, self.scores ):
            print( "======")
            print( guess )
            print( score )
            print( "======")



# answer_haha = "alarm"

# test_guess = "chart"
# print ( genScore(test_guess, answer_haha) )


# if __name__ == "__main__":
#     WordleSession = Wordle() 

#     # WordleSession.answer = "wrath"


#     for i in range(5):
#         print("enter your guess: \n")
#         currentGuess = input()
#         WordleSession.getGuess(currentGuess)
#         newScore = WordleSession.getScore( WordleSession.guess[-1] )

#         if newScore =="22222":
#             print("you Win")
#             break
#         else:
#             WordleSession.printCurrent()
        
#         WordleSession.updateChoices( WordleSession.guess[-1], WordleSession.scores[-1] )

#         print('----')
#         print( "hint", WordleSession.genHint() )
        

