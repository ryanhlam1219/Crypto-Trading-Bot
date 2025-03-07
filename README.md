# Crypto bot
Crypto trading bot written using Python 3.9. In order for this bot to establish a connection to the binance.us API, you must establish a network connection using IPv4 and not IPv6 as IPv6 is not supported. ([read more on this here](https://dev.binance.vision/t/ipv6-support-for-trading/17876))

## IPv4 Check
A connection to IPv4 will be requried for this application. Confirming your device is connected will depend on your operating system.
To confrim a connection to Binance.US API exists at any point run:
```
curl -I https://api.binance.us
```

### Check for MacOS Users
Open Terminal (Cmd + Space, type Terminal, press Enter). From here run:
```
ipconfig getifaddr en0
```
If connected via Wi-Fi, this should return an IPv4 address (e.g., 192.168.x.x). If connected via Ethernet, run:
```
ipconfig getifaddr en1
```
If an IPv4 address appears, you are already connected to IPv4. If no IPv4 address appears, or you only see an inet6 (IPv6) address, proceed to Disable for MacOS Users.

### Check for Windows Users
Open Command Prompt (Win + R, type cmd, press Enter). From here run:
```
ipconfig
```
Look for "IPv4 Address" under your active network to confirm a connection exists. If it doesn't, proceed to Enable for Windows Users.

### Disable for MacOS Users
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

### Enable for Windows Users
Enable IPv4 in Network Settings:

Open Control Panel → Network and Sharing Center.
Click Change adapter settings on the left.
Right-click your active network (Wi-Fi or Ethernet) → Properties.
Find Internet Protocol Version 4 (TCP/IPv4).
If unchecked, check the box and click OK.

If IPv4 is enabled but still missing, try:
```
ipconfig /release
ipconfig /renew
```

## Pre-Requisites

### Setup a Binance.US Account
You will need a Binance.US account in order to utilize the trading bot. Following the [Binance.US](https://support.binance.us/en/articles/9842800-how-to-create-an-api-key-on-binance-us) Documentation. 

Make sure to save your Secret Key and API Key! You will only be able to view your secret key once, and you will need to configure your bot. 

### Create Github Account and Install Github Desktop (Optional)
```
https://docs.github.com/en/desktop/installing-and-configuring-github-desktop/installing-and-authenticating-to-github-desktop/installing-github-desktop
```
### Clone Repository into local environment

## Install and configure project

### Install dependencies

```For Mac OS
python3 -m pip install --no-cache-dir -r requirements.txt
```

### Install dependencies

Update the .env file with your API keys. This is found in your Binance.US account under API Management. Update the lines in .env here:
```
BINANCE_API_KEY=""
BINANCE_API_SECRET=""
```

### Usage

You can set particular symbol pair by using an argument
```bash
python3 main.py BTC_US
```

You can override any env parameter like so
```bash
./main.py BTC_US
```

Afterwards, within your .env file you can update your program to run on one of two modes:
```bash
TRADING_MODE="test" will run your backtest for testing your strategy
TRADING_MODE="real" will run your program against an actual binance client and will use the live binance APIs
```
