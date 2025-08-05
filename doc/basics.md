# The Basics
This document should cover the basic principles of nebula.

## Table of Contents
[Introduction](#introduction) \
[Comments](#comments) \
[Datatypes](#datatypes) \
&nbsp;&nbsp;&nbsp;[Numbers](#numbers) \
&nbsp;&nbsp;&nbsp;[Booleans](#booleans) \
&nbsp;&nbsp;&nbsp;[Strings](#strings) \
&nbsp;&nbsp;&nbsp;[Containers](#containers) \
&nbsp;&nbsp;&nbsp;[Typehints](#typehints) \
[Variables](#variables) \
[Functions](#functions) \
&nbsp;&nbsp;&nbsp;[Definition](#definition) \
&nbsp;&nbsp;&nbsp;[Calling](#invoking) \
[Builtin Functions](#builtin-functions) \
[Builtin Methods](#builtin-methods) \
[Including External Functions](#including-external-functions) \
[If, elif, else](#if-elif-else) \
[For loops](#for-loops) \
[While loops](#while-loops) \
[Break and Continue](#break-and-continue) \
[Membership Testing](#membership-testing) \
[Try, catch, throw](#try-catch-throw) \
[FFI](#ffi) \
[Classes](#classes) \
&nbsp;&nbsp;&nbsp;[Definition](#declaration) \
&nbsp;&nbsp;&nbsp;[Usage](#usage) \
&nbsp;&nbsp;&nbsp;[A more in depth example](#a-more-in-depth-example) \
[Match Case](#match-case) \
[Ternary Operator](#ternary) \
[Lambda Expressions](#lambda) \
[Higher Order](#higher-orderedness) 

## Introduction
The interpreter can run scripts or evaluate expressions using the REPL.
To run the REPL, run `main.py`:
```bash
$ python3 main.py
```
A prompt `>>>` will pop up. Try typing some expressions:
```python
>>> 2 + 2
4
>>> print("Hello World")
Hello World
```
Or, create a file with the content:
```python
print("Hello World!")
```
Provide a `file` argument to run scripts:
```bash
$ python3 main.py hello.fn
'Hello World!'
```
## Comments
Comments start with `//`.
```rust
// This is a comment. 
```
Multiline comments start with `/*` and end with `*/`.
```rust
/*
This is a multi line comment.
*/
```

## Datatypes
#### Numbers
Numbers (ints and floats) work the same in Python as they do here:
The operators `+`, `-`, `*`, `/`, `%` work with brackets `()` changing the order of operation:
```python
>>> 1 + 1
2
>>> 4 / 2 * 10
20.0
>>> 4 / (2 * 10)
0.2
```
When mutating a variable, we can use augmented assignment operators:
The operators `+=`, `-=`, `*=`, `/=`, `%=`, with `++` and `--` being the equivalent of `x += 1` and `x -= 1`.
```python
>>> a = 1
1 
>>> a++
2
>>> a -= 4
-2
```
#### Booleans
The variables True and False work the same as they do in Python:
```python
>>> True 
True
>>> False
False
```

#### Strings
Strings work like Python strings do except escape characters do not mutate the string:
```python
>>> 'a'
'a'
>>> 'a' + 'a'
'aa'
>>> 'a \n a' // This will not be changed
'a \n a' 
>>> 'string'[0] // Strings and containers can be sliced the same
's'
```
```python
>>> 'string'.reverse()
gnirts
>>> 'STRing'.lower()
string
>>> 
```

#### Containers
Lists and dictionaries work the same as they do in Python:
```python
>>> [1, 2, 3]
[1, 2, 3]
>>> [1, 2, 3][0]
1
>>> {'a':1, 'b':2}
{'a': 1, 'b': 2}
>>> {'a':1, 'b':2}['a']
1
```
Like strings, methods also apply as if the container was an instance of a class:
```python
>>> a = [1, 2, 3]
[1, 2, 3]
>>> print(a.append(4))
[1, 2, 3, 4]
>>> 
```

#### Typehints
Show what type a variable is meant to be with `:: <type>`:
They are not enforced by the interpreter.

```python
def f(x :: <int> ) :: <int> {
    x * x
}

x ::<int> = 4
print(f(x))
```

## Variables
All variables are mutable - meaning they can be assigned or reassigned at any time.

```rust
Balance = 0
Name = "Dave"
```

Variables can be assigned to the value of another variable:
```rust
N = "Bob"
Username = N
```

Variables can also be assigned to the return status of a function (more on functions soon):
```rust
BankBalance = getBalance()
```
Variables can also point to functions:
```rust
BankBalance = getBalance
BankBalance()
```

The `global` keyword makes a variable accessible to all functions:
```python
def getBal() {
    global Balance
    print(Balance)
}
Balance = 100
getBal()
```

## Functions
#### Definition
Functions must be defined with:
- The **`def`** keyword
- The functions **name**
- Any arguments the function takes, if applicable
```python
def main() {
```
```python
def calculateBankBalance(num1, num2) {
```
Functions can have default values:
```python
def calculateBankBalance(num1=100, num2=200) {
```
```python
def calculateBankBalance(*args, **kwargs) {
```
Functions return the last value computed automatically, or `return` will return early:
```rust
// Both functions do the same:
def f(x) {
    x * x
}
def f(x) {
    return x * x
}
```
#### Invoking
Functions must be called (or invoked) with:
- The functions **name**
- Any arguments the function takes.
```rust
calculateBankBalance(10, 20)
```
```rust
calculateBankBalance(num1=100, num2=200)
```
```rust
balanceDB = {"num1": 100, "num2": 200}
calculateBankBalance(**balanceDB)
```
## Builtin Functions
s interpeter has functions built in to the interpreter:
#### `print(args)`
Prints _args_ to the screen.
#### `range(start=0, stop, step=1)` 
Returns a list of numbers starting from _start_ to _stop_ with _step_.
#### `input(prompt="")` 
Returns whatever user inputs, while printing _prompt_.
#### `type(data)`
Returns the type of _data_.
#### `int(data)`
Returns a integer representation of _data_.
#### `float(data)`
Returns a floating point integer representation of _data_.
#### `str(data)`
Returns a string representation of _data_.
#### `list(data)`
Returns a list representation of _data_.
#### `dict(data)`
Returns a dictionary representation of _data_.
#### `length(data)`
Returns the length of _data_.
#### `open(file)`
Creates a new _file_ instance.
#### `map(function, iterables)`
Executes _function_ for each item in _iterables_.
#### `filter(function, iterables)`
Executes a _function_ to test if the item is accepted or not.
#### `reduce(function, iterables)`
Reduces _iterables_ contents into one value using _function_.

## Builtin Methods
### String Methods
#### `.reverse()` 
Returns the string in reverse order.
#### `.upper()`
Converts all characters in the string to uppercase.
#### `.lower()` 
Converts all characters in the string to lowercase.
#### `.split(sep=' ')` 
Splits the string into a list using _sep_.
#### `.strip(sep=' ')`
Removes leading and trailing characters matching _sep_.

### List Methods
#### `.append(data)`
Adds a single element to the end of the list.
#### `.extend(list)`
Adds all elements from another list to the end.
#### `.remove(data)`
Removes the first occurrence of the specified _data_.
#### `.sort()` 
Sorts the list in ascending order in place.
#### `.reverse()`
Reverses the elements of the list in place.
#### `.pop()`
Removes and returns the last item from the list.
#### `.index()` 
Returns the index of the first occurrence of a value.

### File Methods
#### `.read()`
Reads the entire contents of the file as a string.
#### `.write(data)` 
Writes _data_ to the file.
#### `.close()`
Closes the file instance.
#### `.readlines()`
Reads all lines from the file into a list.
#### `.readline()` 
Reads the next line from the file as a string.

## Builtin Variables
#### `__argc`
The amount of arguments the script ran with.
#### `__argv`
The contents of the arguments the script ran with.

## Including External Functions
Functions are included into our script with:
- The **`include`** keyword
- The libraries **name**

All data in that file is given to the assigned variable and can be called upon like a class.
```rust
// lib.fn
def copy(src, dest) {
    f = open(src, "r")
    l = f.read()
    g = open(dest, "w")
    g.write(l)
}
```
```rust
// main.bake
lib = include("lib.fn")
lib.copy("a.txt", "b.txt")
```

The `include` statement is the only thing interpeted before functions. Any other code will be ignored if it is not within a function.

## If, elif, else
If statements can have any amount of elif (else if) statements and a singular else statement is optional.

```rust
a = 10
if (a > 5) {
    // a was more than 5
}
elif (a == 10) {
    // a was exactly 10
    // if a was more than 5, we would skip this
}
else {
    // a was neither
}
```
Elif chains will continue executing until a condition is met then skip to the next block of code, unlike regular if statements which will always execute as long as the statement is True.

## For loops
For loops iterate over strings, lists, tuples and any other iterable data type.
For loops syntax is:
`for (index, iterable item, optional increment)`

```rust 
fruits = ["apple", "banana", "cherry"]
for (index, fruits, 1) {
    print(index)
}
```

## While loops
While loops continue executing until a condition is false.
```rust
x = 10
while (x != 0) {
    x -= x
}
```

## Break and continue
In loops, break manually stops the loop, and continue skips the remaining iteration and skips to the next iteration of the loop.
```rust
while (True) {
    if (True) {
        break
    }
    else {
        continue
    }
}
```

## Membership Testing
Use the `in` operator to check if some data is inside some other data.
```python
>>> 'a' in 'apple'
True
```
```python
if ('a' in 'apple') {
    print("Yay")
}
```
```python
>>> lis = ["a", "b", "c"]
>>> while ("a" in lis) {
...     lis.pop() 
... }
>>> print(lis)
[]
```
## Try, catch, throw
Try blocks attempt to run code that is expected to sometimes fail, and catch executes code instead of raising an error.
```js
try {
    y = 5 / 0  
} catch (err) {
    print("Caught error:", err)
}
```
The above code is going to fail as you cannot divide by 0.
You can also declare catch without a variable:
```js
catch {
    print("Cannot divide by 0.")
}
```
You can manually theow an Exception with `throw`.
Unlike Python, that tracks the current exception being handled, Bake will throw any exception at any time.
```python
if (err != 0) {
    throw "SyntaxError"
}
```

## FFI
Since Nebula can't do much by itself, we can outsource anything we need with the foriegn function interface (or FFI) to Python.
Variables will automatically be passed to Python and will be updated immediately within FFI:
```python
ffi {
    print("We are running Python code!");
}
```
Indented statements, like `if`, or functions must be all on the same line in the FFI block:
```python
ffi {
    # Good
    print(a) if a == 1 else print("No");
    # Bad
    if a == 1:
        print(a);
}
```


## Classes
class are custom datatypes that hold one or more variables.
A class can hold any type of variable.
class cannot hold methods.

#### Declaration
Classes must be defined with:
- The **`class`** keyword
- The class **name**
- The variables that the class holds

Heres a simple example:
```rust
class Point {
    x
    y
}
```
#### Usage
class can be used when declaring a variable:
```rust
p = Point(1, 2)
```
Then, to access the variables the class holds, use `class instance`.`class variable`:
```rust
print(p.x)
```

#### A more in-depth example
 also supports full object orientedness - classes, polymorphism, inheritance:
```rust
class PersonUtils {
    def self.fullName() {
        self.firstname + " " + self.lastname
    }
}

// Person inherits everything PersonUtils contains
class Person(PersonUtils) {
    /* Its a good idea to construct classes such that any positional arguments are declared *before* declarations
    This is because the interpreter sees the first arguments given as positional and they are declared the same as variables */
    firstname = "John"
    lastname = "Doe"
    age = 34
    // If `close` was above the first three, all the positional arguments will be shifted one 
    close = None

    def self.getAge() {
        self.age
    }
}
// Polymorphism
def getInfo(user) {
    print(user.fullName())
    print(user.getAge())
}

person1 = Person()
person2 = Person("Jane", "Doe", 43)
getInfo(person1)
getInfo(person2)
```

## Match Case
Match cases work similar to if statements.

Matches can have any amount of case statements but a singular else and singluar case statement is required.

Cases can be integers, floats, or strings. Cases can span multiple lines.
```js
a = 1
match (a) {
    case 2 | 3 | 4 { print("hello...") }
    case 1 { print("hello!") }
    else { print("world?") }
}
```

## Ternary
Ternary expressions are one line if-else statements.
`Condition ? execute if True : execute if False`.
```rust
a = 1
print(a > 0 ? "A is more than 0" : "A is less than or equal to 0")
```

## Lambda
Lambda expressions are first class, anonymous functions that can be assigned to variables.
```rust
a = lambda (x, y) {x * y}
print(a(1, 2))  
```

```rust
print(lambda (x, y) {x * y}(1, 2))  
```

## Higher Orderedness
Functions can be given and executed by other functions as a variable:
```rust
def map(function, list) {
    result = []
    for (i, list, 1) {
        result.append(function(i))
    }
    return result
}

def f(x) { x * x }

print(map(lambda (x){x * x}, [1, 2, 3]))

print(map(f, [1, 2, 3]))
```

Lambdas can also be given and executed by other lambdas:
```rust
doTwice = lambda (f) {
    f()
    f()
}
sayHello = lambda () {
    print("Hello!")
}
// doTwice executes a lambda while itself is also a lambda
doTwice(sayHello)
```