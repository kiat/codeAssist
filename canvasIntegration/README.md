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

4. Change the HOST to your school's canvas URL.

### How to get Access Token
<img width="442" alt="Screen Shot 2023-04-07 at 4 08 06 PM" src="https://user-images.githubusercontent.com/100271213/230679168-3d271847-b8ce-4d6b-ae6d-23d323da69ae.png">
<img width="819" alt="Screen Shot 2023-04-07 at 4 08 42 PM" src="https://user-images.githubusercontent.com/100271213/230679228-d3a00962-f6bc-43e2-8fc4-1806fcd327df.png">

Account -> Settings -> New Access Token -> Generate Token
### Usage


1. Run `sync_roster.py` to synchronize course, instructor, assignment, and student information between Canvas and the local PostgreSQL database.
python3 sync_roster.py
   

2. Run `send_grades_from_codeassist_canvas.py` to send grades from the CodeAssist database to Canvas.


## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


