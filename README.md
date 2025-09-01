# the nebula programming language
a general purpose, simple language

## Features!
- Inferred typing
- Object oriented
- Simple to learn
- Python interoperability

```python
def example() {
    hello = lambda (s) { print("Hello", s) }

    greets = [
        "World"
        "Solar System"
        "Universe"
    ]

    map(hello, greets)
}

example()
```

New feature: List comprehensions!
```java
// Prints the first 1000 prime numbers
[n | n, range(2, 1000), 1 | True not in 
  [True | d, range(2,(int(n/2)+1)), 1 | ((n % d) == 0) and n != 2]
]
```

## Start using nebula!
Download this repository, run `main.py` with a file name to run a script, or with none to start the REPL:
```python
# python3 main.py
>>> 2 + 2
4
>>> 'Hello World'
Hello World
``` 
## Examples!
Look inside `examples/` in this repository!

## Read the docs!
See [docs.md](doc/basics.md) for details.

## Install the vscode language server!
See [install.md](nebula-lsp/README.md) for details.
The Neovim treesitter extension will be added soon.
