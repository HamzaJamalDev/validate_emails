# Email and Website Validation Script

This script processes a list of websites, checks their validity, and attempts to verify emails associated with those websites. The results are saved in a CSV file, and logs are maintained for any errors or issues encountered during processing.

## Requirements

- Python 3.x
- Required Python packages listed in `requirements.txt`

## Setup

1. **Install Required Packages**

Use the following command to install the required packages:
```sh
pip install -r requirements.txt
```

2. **Prepare Input CSV File**

The input CSV file should be named `all_results.csv` and must contain the following headers:
- `name`
- `website`
- `main_category`
- `categories`
- `rating`
- `phone`
- `address`
- `link`

## Usage

1. **Modify Email Sender**

Ensure the `email_send` variable in the script is set to your sender email address:
```python
email_send = 'your_email@example.com'
```

2. **Run the Script**

Execute the script from the command line:
```sh
python validate_email.py
```

## Script Details

### Functions

- **has_mx_record(domain)**
  - Checks if the specified domain has MX (Mail Exchange) records.
  - Logs the process and results.

- **smtp_check(email_receive, email_send)**
  - Attempts an SMTP connection to verify the email address.
  - Logs the process and results.

- **is_valid_email(email_receive, email_send)**
  - Validates the email format and checks MX records and SMTP connection.
  - Returns validation status.

- **is_valid_url(url)**
  - Validates the URL format using a regular expression.

- **get_base_url(url)**
  - Extracts and returns the base URL from a given URL.

- **is_valid_website(website)**
  - Validates the website URL and resolves its IP address.
  - Logs the process and results.

- **print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=50, fill='#')**
  - Displays a progress bar in the terminal.

- **save_intermediate_results(results, output_file)**
  - Saves intermediate results to the specified output CSV file.

- **process_websites(input_file, output_file, email_send)**
  - Processes each website from the input CSV file, validates emails, and saves results.
  - Logs the progress and handles errors.

### Logging

Logs are saved to `process_log.log` and include timestamps, log levels, and messages for DNS resolution, SMTP checks, and other processes.

### CSV Files

- **Input File:** `all_results.csv`
  - Contains website and other related data to be processed.

- **Output File:** `emails.csv`
  - Stores the results of email and website validations.

## Useful Server Commands

- Count the number of failed SMTP connections (response code 550) in the log file:
```sh
grep -o 'code: 550' process_log.log | wc -l
```

- Get the progress:
```sh
grep 'Processed' process_log.log | tail -n 1
```

- Check the status of the current process (replace `53653` with the actual process ID):
```sh
ps -p 53653
```
