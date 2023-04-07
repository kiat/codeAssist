# canvasIntegration

This repository contains Python scripts to synchronize course, roster, and grade information between CodeAssist and Canvas Learning Management System (LMS). The scripts connect to a local PostgreSQL database to store and retrieve the necessary data.

## Overview

There are three main Python scripts in this repository:

1. `canvasMethods.py`: Contains utility methods for interacting with Canvas API and the local PostgreSQL database.
2. `sync_roster.py`: Retrieves course, instructor, assignment, and student information from Canvas and synchronizes it with the local PostgreSQL database.
3. `send_grades_from_codeassist_canvas.py`: Retrieves grades from the CodeAssist database and sends them to Canvas.

## Getting Started

### Prerequisites

- Python 3.6 or higher
- PostgreSQL
- `canvasapi` and `psycopg2` Python libraries

### Installation

1. Clone the repository:
git clone https://github.com/your_username/codeAssist/canvasIntegration.git
   

2. Install required Python libraries:
pip install canvasapi psycopg2
   

3. Update the database credentials and Canvas API access token in `sync_roster.py` and `send_grades_from_codeassist_canvas.py` scripts.

### Usage

1. Run `sync_roster.py` to synchronize course, instructor, assignment, and student information between Canvas and the local PostgreSQL database.
python3 sync_roster.py
   

2. Run `send_grades_from_codeassist_canvas.py` to send grades from the CodeAssist database to Canvas.



