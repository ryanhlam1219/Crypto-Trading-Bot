# Crypto bot

Crypto trading bot written using Python 3.9. 

## Pre-Requisites

### Setup Python3 and VS Code on your Desktop
```
# install homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
export PATH=/usr/local/bin:/usr/local/sbin:$PATH

#install python3
brew install python3

```
### Create Github Account and Install Github Desktop
```
https://docs.github.com/en/desktop/installing-and-configuring-github-desktop/installing-and-authenticating-to-github-desktop/installing-github-desktop
```
### Clone Repository into local environment

## Install and configure project

### Install dependencies

```For Mac OS
python3 -m pip install --no-cache-dir -r requirements.txt

### Usage

You can set particular symbol pair by using an argument
```bash
./main.py BTC_EUR
```

You can override any env parameter like so
```bash
MODE=live ./main.py BTC_EUR
```
