# PyDeodoriser

A Visual Studio Code extension for Python that detects common anti-patterns as they are written. The extension provides descriptions of any detected anti-patterns and examples of better style.

![image](https://user-images.githubusercontent.com/22739847/172131008-a849a776-b2cb-44ff-9523-b061cc166557.png)

## Technologies

Python 3.10 (language server)
 * pygls v0.11.3  
 * qChecker v1.0.2  

Node.js TypeScript (language client)  
  * vscode-languageclient v7.0.0  

## How to Build

### Install Server Dependencies

1. `python -m venv venv`
1. `pip install -r requirements.txt` from root directory
1. `source venv/bin/activate` on Mac, `.\venv\Scripts\activate` on Windows
1. Create `.vscode/settings.json` file and set `python.defaultInterpreterPath` to point to your python environment where `pygls` is installed

`deactivate` to deactivate the virtual enviroment

### Install Client Dependencies

Open terminal and execute following commands:

1. `npm install`
1. `cd client`
1. `npm install`

### Run Extension

1. Open this directory in VS Code
1. Open debug view (`ctrl + shift + D`)
1. Select `Server + Client` and press `F5`

### Package Extension

`vsce package` (requires node package vsce)  

## Future Plans

* Any new anti-patterns added to qChecker can be added to the extension by adding them to the configuration section of the package.json.  
* Support for different languages could be added.  
* Extensions for different IDES could be developed.  

## Acknowledgements

James Finnie-Ansley for their work on qChecker.
