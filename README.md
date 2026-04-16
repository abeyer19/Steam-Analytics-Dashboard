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
\
Once cloned, either open the cloned repo in your IDE of choice or change directories to the respective path in your CLI and download depedencies.

**It is highly recommended that you create a virtual environment prior to downloading dependencies with the following CLI commands.**
```Bash
python3 -m venv .venv
source .venv/bin/activate # On Windows: .venv\Scripts\activate
```

#### Install Dependencies:
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

# 🚀 Execution
### 0. Code Demo's

### 1. Algorithm Implementations

### 2. Dashboard Demo's
