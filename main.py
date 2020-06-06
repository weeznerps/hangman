#!flask/bin/python
from flask import Flask, request, session, redirect
from random_word import RandomWords

app = Flask(__name__)
app.secret_key = 'secret_key'
app.config['SESSION_TYPE'] = 'filesystem'

incorrect_guesses_allowed = 6

@app.route('/health')
def health():
    return 'true'

@app.route('/')
def root():
    return start_page

@app.route('/start', methods=['GET'])
def start_game():
    # Reset the session vars
    word = RandomWords().get_random_word(hasDictionaryDef=True, maxLength=12, minLength=5).lower()
    while not word.isalpha():
        word = RandomWords().get_random_word(hasDictionaryDef=True, maxLength=12, minLength=5).lower()
    session['word'] = word
    session['correct_guesses'] = ''
    session['incorrect_guesses'] = ''
    return redirect("/guess", code=302)

@app.route('/guess', methods=['GET','POST'])
def guess():

    # Restart the game if no word is present
    if 'word' not in session:
        return redirect("/start", code=302)

    word = session['word']

    if not request.args.get('letter'):
        return create_page(word, session['correct_guesses'], session['incorrect_guesses'], "Guess a letter")

    letter = request.args.get('letter').lower()

    if len(letter) > 1:
        return create_page(word, session['correct_guesses'], session['incorrect_guesses'], "Slow down! Only one letter at a time!")
    elif not letter.isalpha():
        return create_page(word, session['correct_guesses'], session['incorrect_guesses'], "Your guess must be a letter!")

    # Don't punish the player for guessing the same letter twice
    if letter in session['correct_guesses'] or letter in session['incorrect_guesses']:
        return create_page(word, session['correct_guesses'], session['incorrect_guesses'], "You've already guessed that letter")

    if letter in word:

        # Add copies of the letter for each one present in the word to track success
        for i in range(word.count(letter)):
            session['correct_guesses'] += letter

        # if 'word' and 'correct_guesses' are the same length, the player won
        if len(session['correct_guesses']) == len(word):
            return win_page.format(word)
        return create_page(word, session['correct_guesses'], session['incorrect_guesses'], "Well done! Guess another letter")
    else:
        session['incorrect_guesses'] += letter
        if len(session['incorrect_guesses']) == incorrect_guesses_allowed:
            return loss_page.format((hangman_map[len(session['incorrect_guesses'])]), word)
        return create_page(word, session['correct_guesses'], session['incorrect_guesses'], "Oops! That's not in the word. Guess another letter")

def create_page(word, correct, incorrect, message):
    # Display
    correct_progress_display = ''
    for l in word:
        if l in correct:
            correct_progress_display += l
        else:
            correct_progress_display += "_"
        correct_progress_display += " "  
    return guess_page.format(message, hangman_map[len(incorrect)], correct_progress_display, ", ".join(incorrect))


'''
HTML pages for the application
'''

start_page = """
Hi! Click <a href="/start">here</a> to begin
"""

win_page = """
Hooray! You win! the word was \"{0}\".
<br>
Click <a href="/start">here</a> to play again!
"""


loss_page = """
<pre>
{0}
</pre>
<br>
Oh no! You lost! The word was \"{1}\".
Click <a href="/start">here</a> to try again!
"""

guess_page = """
{0}
<br>
<pre>
{1}
</pre>
<br>
<pre>
{2}
</pre>
<br>
Incorrect guesses:
<pre>
{3}
</pre>
<br>
<form>
<input type="text" id="letter" name="letter"><br><br>
<input type="submit" value="Submit">
</form>
"""

hangman_map = {
0:
"""
 +-----    
 |    |
 |    
 | 
 |
 |
 |  
============
""",
1:
"""
 +-----    
 |    |
 |    o
 | 
 |
 |
 |  
============
""",
 2:
"""
  +-----    
  |    |
  |    o
  |    |
  |
  |
  |  
============
""",
 3:
"""
  +-----    
  |    |
  |    o
  |   -|
  |
  |
  |  
============
""",
 4:
"""
  +-----    
  |    |
  |    o
  |   -|-
  |
  |
  |  
============
""",
 5:
"""
  +-----    
  |    |
  |    o
  |   -|-
  |   /
  |
  |  
============
""",
 6:
"""
  +-----    
  |    |
  |    o
  |   -|-
  |   / \\
  |
  |  
============
"""}
