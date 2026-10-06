# Finalizer

Finalizer is a specialized automation tool designed for South African accountants, bookkeepers, and founders to parse, clean, and format raw financial trial balance data in seconds.

## Overview

Manually cleaning trial balances and dealing with messy historical books is a massive time sink. Finalizer automates the tedious formatting grunt work, allowing finance professionals to bypass late-night spreadsheet prep and focus on actual business strategy.

## Tech Stack

**Language:** Python
**Framework:** Streamlit
**Data Processing:** Pandas, Openpyxl
**Data Logging:** JSON (`usage_logs.json') with UTC timestamps (standardized for global handling, mapped locally to SAST / UTC+2).

## Features

* Automated parsing and cleaning of trial balance sheets
* Usage tracking and logging via local JSON structures.
* Lightweight, fast, and simple user interface built for speed.

## Local Installation & Setup

To run this application locally, follow these steps:

1. **Clone the repository:**
bash
git clone <your-repository-url>
cd finalizer