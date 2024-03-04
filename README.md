To start the project make sure python 3 is installed.
Open a terminal and navigate to this project folder.
Run the following command to create a python virtual environment.
                    
                    py -3 -m venv .venv

If this command (py -3 -m venv .venv) does not work run
                    python -m venv .venv

To start the virtual environment run this command.

                    .venv\scripts\activate

To exit the virtual environment run this command.

                    deactivate

While within the virtual environment, to installed python packages run:

                    pip install -r requirements.txt

To start the flask app use the following command.

                    flask --app main run
                
This does not start in debug mode, to run in debug mode, run the following command after activating the .venv:

                    py main.py