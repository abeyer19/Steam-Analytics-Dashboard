# Steam Analytics Dashboard
Repository for Georgia Tech's CSE 6242 DVA Project - Spring 2026 Team 40

# ℹ️ Description
This project is a part of a semester long team collaboration effort for Georgia Tech's CSE 6242 course in the OMSA program, Spring semester 2026.

Our mission is to empower developers, game studios, and researchers on the world’s largest gaming platform by bridging the gap between academic research and actionable analytics through an intuitive, interactive dashboard.

Using free and open-source software, we are able to collect mass amounts of data using [Steam](https://store.steampowered.com/) storefront endpoints and official APIs about the platforms 200K+ App IDs and 100K+ Games. All data collection, tranformations, algorithmic implementations, and visualizations are engineered and maintained by our team while ensuring reproducibility.

# 💾 Installation
### 0. Prerequesites
- Python 3.14+ required.
- R version 4.5.2+ required.
- CLI (*Command Line Iterface*)

### 1. Cloning the repository
#### Clone Repository:
```Bash
git clone https://github.com/USER/Steam-Analytics-Dashboard
```

Once cloned, either open the cloned repo in your IDE of choice or change directories to the respective path in your CLI and continue to [installing dependencies](#installingd-dependencies).

**It is highly recommended that you create a virtual environment prior to downloading dependencies with the following CLI commands.**
```Bash
python3 -m venv .venv
source .venv/bin/activate # On Windows: .venv\Scripts\activate
```

### 2. Installing Dependencies
#### Install Dependencies (Python):
> a. Install dependencies **without** the ability to make changes to current code.
```Bash
python3 -m pip install .
```
> b. Install dependencies in editable mode **for development**.
```Bash
python3 -m pip install -e .
```

#### Install Dependencies (R):
> a. Install dependencies within the CLI.
```Bash
Rscript -e "renv::restore()"
```
> b. Install dependencies within the R console for RStudio.
```R
renv::restore()
```

### 3. Obtaining a Steam Web API Key
Follow the instruction from the [Steam Web API Documentation](https://steamcommunity.com/dev) to obtain an API Key prior to running any scripts. 
\
Once completed, open the ```config.env``` file from the downloaded Repository and replace ```YOUR API KEY HERE```, in line one, with your newly obtained Steam Web API Key. 

# 🚀 Execution
### 0. Code Demo's
#### Initial Start
We recommend starting with ```appdetails_scraper.py```, as this will pull a majority of the metadata for all App IDs. \
**Please Note: each script may take a few days to complete given the size of data being scraped, your network connection, your computers hardware capabilities, and the rate limiting put in place by our team. This rate limiting is for your protecion, please do not adjust or remove from the scripts.**

> a. CLI
```Bash
python3 -m Scrapers.appdetails_scraper.py
```
> b. IDE 
```
Run Python script.
```

Once   ```appdetails_scraper.py``` is completed, continue with other scripts until all have finished. \
These residual scripts include: ```appreviews_scraper.py```, ```currentplayers_scraper.py```, ```tags_scraper.py```, and ```achievements_scraper.py```

### 1. Algorithm Implementations

### 2. Dashboard Demo's
