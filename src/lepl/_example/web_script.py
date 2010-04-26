# Welcome to LEPL - a parser for Python 2.6+ (including 3!)

# All these examples will assume that we have imported the main package
from lepl import *

# Let's start with a typical problem: we want to parse the input for
# a search engine.  A request might be:
#   spicy meatballs OR "el bulli restaurant"

# Here is how we define the parser:
word = ~Lookahead('OR') & Word()
phrase = String()
with DroppedSpace():
    text = (phrase | word)[1:] > list
    query = text[:, Drop('OR')]

# and here is how we can use it:
query.parse('spicy meatballs OR "el bulli restaurant"')

# If you want to pause this demo, so that you can scroll back and 
# have a think, just click on the screen (click again to restart).

# It's interesting to see what is happening in a little more detail:
with TraceVariables():
    word = ~Lookahead('OR') & Word()
    phrase = String()
    with DroppedSpace():
        text = (phrase | word)[1:] > list
        query = text[:, Drop('OR')]

query.config.auto_memoize(full=True)
query.parse('spicy meatballs OR "el bulli restaurant"')
# The display above shows the results for the different matchers as
# the input stream is consumed.  This can be very useful for debugging.

# Just before calling the parser above we configured full memoization.
# This means that each matcher records previous matches and so avoids
# earlier work.  The (lack of a) trace on a second call reflects this:
query.parse('spicy meatballs OR "el bulli restaurant"')
# (the response appeared without calling any more matchers)


# You probably noticed some "surprising" syntax above, in the way 
# that we specify repeated matches - using [1:] for "one or more".
# This may seem a little odd, but soon feels very natural.

# For example, this means "between 3 and 5" (inclusive):
Any()[3:5].parse('1234')
Any()[3:5].parse('123456')
# (the error above is expected - our grammar specified 3 to 5
# characters, but the input contained 6.  This can be disabled 
# using matcher.config.no_full_first_match())

# It's also common to use [:] or [0:] to mean "zero or more":
Any()[:].parse('123456')
# (LEPL is greedy by default, and so matches as much as possible) 

# And often, once we've matched something several times, we want to
# join the results together - we can use [...] for that:
Any()[3:5, ...].parse('1234')

# And (even more!) we can also specify a separator...
Any()[3:5, ';'].parse('1;2;3;4')
# ...which we often discard:
Any()[3:5, Drop(';')].parse('1;2;3;4')

# While we're looking at LEPL's syntax, it's worth pointing out that
# & and | do what you would expect:
(Digit() | Letter())[6].parse('abc123')
(Digit() & Letter()).parse('1a')


# It's also easy to define your own matchers.  They can be as simple
# as a single function:
from string import ascii_uppercase

@function_matcher
def Capital(support, stream):
    if stream[0] in ascii_uppercase:
        return ([stream[0]], stream[1:])
# As you can see, a matcher takes a stream and, if the start of the
# stream matches, returns that (in a list) and the rest of the stream.

# This works (and fails) as you would expect:
Capital().parse('A')
Capital().parse('a')
# (again, this error is expected - we defined a matcher for capitals,
# but the input was lower case).

# So far we have focused mainly on recognising structure in text,
# but parsing is also about processing that structure.

# We can process text as it is matched by calling functions.
# The function is called with the results just matched:
def print_and_group_text(results):
    # print what we just matched
    print('matched', results)
    # wrap in an extra list for grouping
    return list(results)

word = ~Lookahead('OR') & Word()
phrase = String()
with DroppedSpace():
    text = (phrase | word)[1:] > print_and_group_text
    query = text[:, Drop('OR')]

query.parse('spicy meatballs OR "el bulli restaurant"')

# Another way LEPL can help with processing is by constructing a tree
# (eg an AST).  To illustrate this, let's extend the original example
# to include labelled parameters, like "site:acooke.org":

class Text(Node): pass

class Parameter(Node): pass

class Alternative(Node): pass

word = ~Lookahead('OR') & Word()
phrase = String()
label = word & Drop(':') > 'label'
value = (phrase | word) > 'value'
with DroppedSpace():
    parameter = label & value > Parameter
    text = (phrase | word) > 'text'
    alternative = (parameter | text)[1:] > Alternative
    query = alternative[:, Drop('OR')]

result = query.parse('word "a phrase" OR that OR this site:within.site')

# Each alternative is a separate tree
for alt in result:
    print(str(alt))


# and tree members can be accessed directly:
result[2].Parameter[0].label[0]


# LEPL can also handle ambiguous grammars, returning multiple results,
# so can be used to solve problems that occupy a middle ground between
# parsing and search.

# For example, we can use LEPL to list all the possible ways that a
# phone number can be displayed, if the characters on the keypad are
# used.

# This also shows how easy it is to extend LEPL with a new matcher that
# returns multiple (alternative) matches.  Here the matcher Digit() 
# enumerates all possible ways the number can be displayed.

@sequence_matcher
def Digit(support, stream):
    digits = {'1': '',     '2': 'abc',  '3': 'def',
              '4': 'ghi',  '5': 'jkl',  '6': 'mno',
              '7': 'pqrs', '8': 'tuv',  '9': 'wxyz',
              '0': ''}
    if stream:
        digit, tail = stream[0], stream[1:]
        yield ([digit], tail)
        if digit in digits:
            for letter in digits[digit]:
                yield ([letter], tail)

results = Digit()[13, ...].parse_all('1-800-7246837')
assert ['1-800-painter'] in results
