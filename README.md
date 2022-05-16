# pyDeodoriser

## Install Server Dependencies

1. `python -m venv venv`
1. `pip install -r requirements.txt` from root directory
1. `source venv/bin/activate` on Mac, `.\env\Scripts\activate` on Windows
1. Create `.vscode/settings.json` file and set `python.pythonPath` to point to your python environment where `pygls` is installed

`deactivate` to deactivate the virtual enviroment

## Install Client Dependencies

Open terminal and execute following commands:

1. `npm install`
1. `cd client/ && npm install`

## Run Example

1. Open this directory in VS Code
1. Open debug view (`ctrl + shift + D`)
1. Select `Server + Client` and press `F5`
