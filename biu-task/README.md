# Flask E-Learning Task Fetcher

This project is a Flask web application that integrates Selenium to fetch e-learning tasks from a specified platform, check their deadlines, and display the status of submitted and unsubmitted tasks.

## Project Structure

```
flask-selenium-app
├── app
│   ├── __init__.py          # Initializes the Flask application and sets up configuration
│   ├── routes.py            # Contains route definitions for the Flask application
│   ├── selenium_utils.py     # Selenium-related functions for automation
│   └── templates
│       └── index.html       # HTML template for the index page
├── requirements.txt          # Lists the dependencies required for the project
├── run.py                    # Entry point for running the Flask application
└── README.md                 # Documentation for the project
```

## Setup Instructions

1. **Clone the repository**:

   ```
   git clone <repository-url>
   cd flask-selenium-app
   ```

2. **Install dependencies**:
   Make sure you have Python installed, then run:

   ```
   pip install -r requirements.txt
   ```

3. **Run the application**:
   Execute the following command to start the Flask application:

   ```
   python run.py
   ```

4. **Access the application**:
   Open your web browser and go to `http://127.0.0.1:5000/` to access the application.

## Usage

- Enter your e-learning platform username and password in the provided form.
- Submit the form to fetch your tasks.
- The application will display the tasks along with their start and end dates, as well as their submission status.

## Dependencies

- Flask
- Selenium
- WebDriver Manager

## Notes

- Ensure that you have the appropriate WebDriver installed for your browser.
- The application is designed to run in a headless mode for Selenium, which means it will not open a browser window during execution. Adjust the `selenium_utils.py` file if you wish to run it in a visible mode for debugging purposes.

## FIX VERSION OF BIUTASK CREATE BY ZETTA

## -This is Currently fixed in 1 week and fix version of BIUTASK notifications,

## How To Use

---

1. Create Account On the /register endpoint its means to create
2. is account created go to the main application
3. fill the username as NPM and password as password ecampus real,if you all fill the fields randomly it will be error,cause this application needed account ecampus to receive the notification
4. choice the schedule time to send the notification, for now the time send its 2 minutes, i will update the time to 24 hours from your registration to this application
