#!flask/bin/python
import os
from flask import Flask, jsonify, request, session, redirect
from random_word import RandomWords
import json

from hangman import pages

app = Flask(__name__)
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'

@app.route('/health')
def health():
    return 'true'

@app.route('/')
def root():
    return pages.start_page

@app.route('/start', methods=['GET'])
def start_game():
    session['word'] = RandomWords().get_random_word(hasDictionaryDef=True, maxLength=15, minLength=5)
    session['correct_guesses'] = ''
    session['incorrect_guesses'] = ''
    return redirect("/guess", code=302)

@app.route('/guess', methods=['GET','POST'])
def guess():
    word = session['word']
    letter = request.args.get('letter')
    if letter and len(letter) > 1:
        return create_page(word, session['correct_guesses'], session['incorrect_guesses'], "Slow down there sparky! Only one letter at a time!")
    if letter == None:
        return create_page(word, session['correct_guesses'], session['incorrect_guesses'], "Guess a letter")
    if 'word' not in session:
        return redirect("/start", code=302)
    if letter in session['correct_guesses'] or letter in session['incorrect_guesses']:
        return create_page(word, session['correct_guesses'], session['incorrect_guesses'], "You've already guessed that letter")
    if letter in word:
        if len(session['correct_guesses']) == len(word):
            return "Congrats, you won!"
        for i in range(word.count(letter)):
            session['correct_guesses'] += letter
        return create_page(word, session['correct_guesses'], session['incorrect_guesses'], "Well done! Guess another letter")
    else:
        session['incorrect_guesses'] += letter
        if len(session['incorrect_guesses']) == 6:
            return pages.loss_page.format((pages.man[len(session['incorrect_guesses'])]), word)
        return create_page(word, session['correct_guesses'], session['incorrect_guesses'], "Oops! That's not in the word. Guess another letter")

def create_page(word, correct, incorrect, message):
    correct_progress_display = ''
    for l in word:
        if l in correct:
            correct_progress_display += l
        else:
            correct_progress_display += "_"
    return pages.guess_page.format(message, pages.man[len(incorrect)], correct_progress_display, incorrect)
