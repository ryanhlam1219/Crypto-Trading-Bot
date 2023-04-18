# Crypto bot

Crypto trading bot written using Python 3.9. In order for this bot to establish a connection to the binance.us API, you must establish a network connection using IPv4 and not IPv6 as IPv6 is not supported. 

If your active network is WiFi enter the following command:
```
networksetup -setv6off Wi-Fi
```
If you are on Ethernet:
```
networksetup -setv6off Ethernet
```
You may combine both of commands to disable IPv6 on WiFi and Ethernet at the same time:
```
networksetup -setv6off Ethernet && networksetup -setv6off Wi-Fi
```
To re-enable IPv6, you need to replace setv6off to setv6automatic (the default state in macOS), for example:
```
networksetup -setv6automatic Wi-Fi && networksetup -setv6automatic Ethernet
```

## Pre-Requisites
### Create Github Account and Install Github Desktop
```
https://docs.github.com/en/desktop/installing-and-configuring-github-desktop/installing-and-authenticating-to-github-desktop/installing-github-desktop
```
### Clone Repository into local environment

## Install and configure project

### Install dependencies

```For Mac OS
python3 -m pip install --no-cache-dir -r requirements.txt
```
### Usage

You can set particular symbol pair by using an argument
```bash
python3 main.py BTC_EUR
```

You can override any env parameter like so
```bash
MODE=live ./main.py BTC_EUR
```
