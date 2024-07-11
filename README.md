# 🚀 Mini Pascal Interpreter

## 📖 Overview

This project implements a Mini Pascal Interpreter, capable of parsing, analyzing, and interpreting a subset of the Pascal programming language. This code is an expanded version of the interpreter described in [Ruslan Spivak's "Let's Build A Simple Interpreter" series](https://ruslanspivak.com/lsbasi-part1/).

## 🛠️ Features

- Lexical analysis
- Syntax parsing
- Semantic analysis
- Interpretation of Pascal programs
- Support for basic Pascal constructs including:
  - Variables and data types
  - Arithmetic operations
  - Control structures (if-else, while)
  - Procedures
  - Input/Output operations

## 🏗️ Project Structure

The main components of the interpreter are:

- Lexer: Tokenizes the input
- Parser: Builds an Abstract Syntax Tree (AST)
- Semantic Analyzer: Performs semantic checks
- Interpreter: Executes the Pascal program

## 🚀 Getting Started

### Prerequisites

- Python 3.6+

### Installation

1. Clone the repository:

```
git clone https://github.com/yourusername/mini-pascal-interpreter.git
cd mini-pascal-interpreter
```

2. No additional dependencies are required as the project uses Python standard libraries.

## 🖥️ Usage

Run the interpreter with a Pascal source file:
```

python interpreter.py your_pascal_file.pas
```

### Command-line Options

- `--scope`: Print scope information
- `--stack`: Print call stack
- `--lexer`: Print lexer tokens
- `--visitor`: Print visitor information
- `--mips`: Print MIPS-related information

## 📝 Example

Example files are included in the repo.

## 📄 Project Paper

For a detailed explanation of the project, including its design, implementation, and analysis, please refer to our [project paper](https://drive.google.com/file/d/1fsDcubbnExg5KrOdlny1wHMiuiFkp2Gh/view?usp=sharing).

