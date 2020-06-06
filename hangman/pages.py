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
{2}
<br>
{3}
<br>
<form>
<input type="text" id="letter" name="letter"><br><br>
<input type="submit" value="Submit">
</form>
"""

man = {
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