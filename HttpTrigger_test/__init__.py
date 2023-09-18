import logging
import pandas as pd
import azure.functions as func
import telebot
from telebot import apihelper, types
from wordle import Wordle

APIK_KEY = "6382184170:AAGTn0MjeUMnR1nLCFvJJJGnwhwj3FO-u2o"

# bot = telepot.Bot('APIK_KEY')
URL = "https://yianfirstazurefunction.azurewebsites.net/httptrigger_test"


logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

# Set bot token
TOKEN = APIK_KEY


user = {}
SOLVER_MODE = "SOLVER"
WORDLE_MODE = "WORDLE"



isSessionStarted = False 
solverMode = False 

# Uncomment this for using proxy for request
# PROXY = ''
# apihelper.proxy = {'https': PROXY}

# Set WEBHOOK as your Azure Functions url (https://...azurewebsites.net/HttpTrigger)
WEBHOOK = URL
bot = telebot.TeleBot(TOKEN)


def userChecker( message ):

    return "user_{0}".format ( message.chat.id ) in user.keys()
    
def isFiveLetter( message ):

    if not userChecker( message ):
        return False
    
    WordleSession = user[ "user_{0}".format ( message.chat.id )]
    
    letter = message.text.lower()

    return letter in WordleSession.allWords.values 
    # if "/" in letter:
    #     return False


    # if len( letter ) == 5:

    #     extractedLetter = re.sub('[^a-zA-Z]+', '', letter )

    #     if len( extractedLetter ) == 5:
    #         return True
    #     else:
    #         return False 
    # else:
    #     return False
    
def notFiveLetter( message ):

    if not userChecker( message ):
        return False

    WordleSession = user[ "user_{0}".format ( message.chat.id )]

    if len( WordleSession.guess ) > len( WordleSession.scores ):
        return False
    
    if ( WordleSession.mode == SOLVER_MODE ) and ( len( WordleSession.choiceSpace ) ==1 ) :
        return False

    if "/" in message.text:
        return False
        

    return not isFiveLetter( message ) 


def genStatus( message ):
    
    WordleSession = user[ "user_{0}".format ( message.chat.id ) ]
    
    reply = ""
    for oneOfGuess, oneOfScore in zip( WordleSession.guess, WordleSession.scores ):
        reply = reply + " guess: " +  oneOfGuess.upper() + "\n" + "score: " + oneOfScore + "\n"
    
    return reply

@bot.message_handler( commands = ['start'])
def start( message ):

    user[ "user_{0}".format ( message.chat.id )] = Wordle()

    bot.reply_to( message, "Enter /wordle to start a game \n Enter /hint to get a hint \n use /solver to solve " )

@bot.message_handler( commands = ['hello'])
def hello( message ):
    bot.send_message( message.chat.id, "hi there" )


@bot.message_handler( commands = ['wordle'])
def newSession( message ):

    if userChecker( message ):

        WordleSession = user[ "user_{0}".format ( message.chat.id )]
        WordleSession.reset()
        # WordleSession._mode = "WORDLE"

    else:
        user[ "user_{0}".format ( message.chat.id )] = Wordle()

    # print( user[ "user_{0}".format ( message.chat.id )].answer )
    bot.send_message( message.chat.id, "Enter a 5 letter word for guess: " )


@bot.message_handler( commands = ['rollback'])
def rollback( message ):

    if not userChecker( message ):
        return 
    

    WordleSession = user[ "user_{0}".format ( message.chat.id )]
    
    if WordleSession.mode != SOLVER_MODE:
        return 
    
    WordleSession.guess = WordleSession.guess[:-1]
    WordleSession.scores = WordleSession.scores[:-1]

    WordleSession.choiceSpace = WordleSession.allWords

    for guess, score in zip( WordleSession.guess, WordleSession.scores ):
        WordleSession.updateChoices( guess, score )
    

    reply = genStatus( message )
    # print( user[ "user_{0}".format ( message.chat.id )].answer )
    bot.send_message( message.chat.id, "Here are your guesses and scores: \n" +reply )
    bot.send_message( message.chat.id, "Please eneter a new guess: "  )

    

@bot.message_handler( func= isFiveLetter )
def getGuess(message):

    WordleSession = user[ "user_{0}".format ( message.chat.id )]
    guess = message.text.lower()
    WordleSession.getGuess( guess )


    mode = WordleSession.mode
    ## if Solver we need score

    if mode == SOLVER_MODE :

        if len( WordleSession.choiceSpace ) ==1:

            bot.send_message( message.chat.id, "Use /rollback if *{0}* was not ur answer, or /solver or /wordle for a new session".format( WordleSession.hint.upper() ), parse_mode= "Markdown"  )
            return 

        bot.send_message( message.chat.id, "Please provide the score from Wordle for *{0}*: ".format( guess.upper()), parse_mode= "Markdown" ) 

    else: 

        # print( WordleSession.guess[-1], WordleSession.answer)
        newScore = WordleSession.getScore( WordleSession.guess[-1] )

        if newScore =="22222":
            reply = "you Win. Session Ended"
    
            WordleSession.reset()
        else:  
            WordleSession.updateChoices( WordleSession.guess[-1], WordleSession.scores[-1] )

            reply = genStatus( message )

        bot.send_message( message.chat.id, reply )


def isValidScore( message ):

    if not userChecker( message ):
        return False
    
    if "/" in message.text:
        return False
    

    WordleSession = user[ "user_{0}".format ( message.chat.id )]

    if len( WordleSession.choiceSpace ) == 1:
        return False
    

    if WordleSession.guess == []:
        return False
    
    if WordleSession.mode != SOLVER_MODE:
        return False

    score = message.text 

    if score.isdigit():
        return len( score ) == 5
    else:
        return False


@bot.message_handler( func= isValidScore )
def updateScore(message):

    score = message.text
    
    WordleSession = user[ "user_{0}".format ( message.chat.id )]


    if len( WordleSession.choiceSpace ) ==1:

        bot.send_message( message.chat.id, "Use /rollback if *{0}* was not ur answer, or /solver or /wordle for a new session".format( WordleSession.hint.upper() ) , parse_mode= "Markdown" )
        return 
    
    
    WordleSession.scores.append( score )

    if len( WordleSession.scores ) == len( WordleSession.guess )+1:
        WordleSession.getGuess( WordleSession.hint )
    
    assert len( WordleSession.scores ) == len( WordleSession.guess )

    nextChoices = WordleSession.seeNextChoices( WordleSession.guess[-1], score  )

    if len( nextChoices ) == 0:
        bot.send_message( message.chat.id, "Very likely you made a typo for score or guess, please check" )
        bot.send_message( message.chat.id, "Use /rollback to rollback a guess, below are your current guesses and scores" )
        bot.send_message( message.chat.id, ""+ genStatus( message ) )
        bot.send_message( message.chat.id, "Or the answer is missing from our dictionary... :( " )

        return 


    WordleSession.updateChoices( WordleSession.guess[-1], score )

    hint = WordleSession.genHint().upper()

    if len( WordleSession.choiceSpace ) == 1:
        bot.send_message( message.chat.id, "Answer is: *{0}*".format(  hint.upper()) , parse_mode= "Markdown")
        bot.send_message( message.chat.id, "Use /rollback to rollback a guess, if you think you made a typo" )
        bot.send_message( message.chat.id, ""+ genStatus( message ) )
        return 

    bot.send_message( message.chat.id, "try: *{0}*".format ( hint.upper()) )
    bot.send_message( message.chat.id, "Please provide the score for *{0}* or enter the word you actually tried: ".format( hint ), parse_mode= "Markdown" )

def isNOTValidScore( message ):

    if not userChecker( message ):
        return False
    
    if "/" in message.text:
        return False
    
    WordleSession = user[ "user_{0}".format ( message.chat.id )]

        # WordleSession = user[ "user_{0}".format ( message.chat.id )]

    if len( WordleSession.choiceSpace ) ==1:

        return False
    
    if WordleSession.guess == []:
        return False
    if WordleSession.mode != SOLVER_MODE:
        return False
    
    return not( isValidScore(message) )

@bot.message_handler( func= isNOTValidScore )
def notGoodScore(message):

    bot.send_message( message.chat.id, "Enter a five digit score")

## exception Handler for ivalud Guess


@bot.message_handler( func=notFiveLetter )
def askUserForFiveLetter(message):
    bot.send_message( message.chat.id, "please enter a proper five letter word" )




@bot.message_handler( commands = ['hint'])
def getHint( message ):

    if not userChecker( message ):
        bot.send_message( message.chat.id, "/wordle to start" )
        return 

    WordleSession = user[ "user_{0}".format ( message.chat.id )]

    currentHint = WordleSession.genHint().upper()

    bot.send_message( message.chat.id, "try: *{0}*".format( currentHint), parse_mode= "Markdown" )


@bot.message_handler( commands = ['solver'])
def solverStart( message ):

    if not userChecker( message ):
        user[ "user_{0}".format ( message.chat.id )] = Wordle()
        user[ "user_{0}".format ( message.chat.id )].mode = SOLVER_MODE
    else:

        WordleSession = user[ "user_{0}".format ( message.chat.id )]
        WordleSession.reset( SOLVER_MODE )


    # # print("Enter your: ")
    bot.send_message( message.chat.id, "Ener the first 5 letter word guess you made: " )











def main(req: func.HttpRequest) -> func.HttpResponse:
    bot.set_webhook(url=WEBHOOK)
    request_body_dict = req.get_json()
    update = telebot.types.Update.de_json(request_body_dict)
    bot.process_new_messages([update.message])
    return func.HttpResponse(body='', status_code=200)

# Sometimes "requests" version is important.
# azure-functions==1.0.4
# PySocks==1.7.1
# pyTelegramBotAPI==3.6.6
# requests==2.10.0