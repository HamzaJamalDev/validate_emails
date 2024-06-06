from urllib.parse import urlparse
import socket
import smtplib
import dns.resolver
import re
import csv
import time
import random
import logging
import os

# Set up logging
logging.basicConfig(filename='process_log.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def has_mx_record(domain):
    try:
        logging.info(f"Resolving MX records for domain: {domain}")
        answers = dns.resolver.resolve(domain, 'MX')
        mx_records = [str(r.exchange) for r in answers]
        logging.info(f"MX records for {domain}: {mx_records}")
        return True
    except dns.resolver.NoAnswer:
        logging.warning(f"No MX record found for domain: {domain}")
        return False
    except dns.resolver.NXDOMAIN:
        logging.warning(f"Domain does not exist: {domain}")
        return False
    except dns.resolver.Timeout:
        logging.warning(f"DNS resolution timeout for domain: {domain}")
        return False
    except Exception as e:
        logging.error(
            f"Unexpected DNS resolution error for domain {domain}: {e}")
        return False


def smtp_check(email_receive, email_send):
    domain = email_receive.split('@')[1]
    try:
        logging.info(f"Resolving MX records for domain: {domain}")
        records = dns.resolver.resolve(domain, 'MX')
        mx_record = str(records[0].exchange)
        logging.info(f"Using MX record: {mx_record}")

        logging.info("Attempting SMTP connection...")
        with smtplib.SMTP(mx_record, 25, timeout=10) as server:
            server.set_debuglevel(0)
            server.helo(server.local_hostname)
            server.mail(email_send)
            code, message = server.rcpt(email_receive)
            logging.info(f"SMTP response code: {code}, message: {message}")
            return code == 250
    except smtplib.SMTPConnectError as e:
        logging.error(f"SMTP connection error: {e}")
        return False
    except smtplib.SMTPServerDisconnected as e:
        logging.error(f"SMTP server disconnected error: {e}")
        return False
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error during SMTP check: {e}")
        return False


def is_valid_email(email_receive, email_send):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email_receive):
        domain = email_receive.split('@')[1]
        if has_mx_record(domain):
            if smtp_check(email_receive, email_send):
                return "Valid email"
            else:
                return "Can't check SMTP connection"
        else:
            return "Doesn't have MX record"
    else:
        return "Bad format"


def is_valid_url(url):
    # Regular expression to match URL format
    pattern = r'^(https?://)?(www\.)?([a-zA-Z0-9-]+)(\.[a-zA-Z]{2,}){1,2}(/.*)?$'
    return re.match(pattern, url)


def get_base_url(url):
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"


def is_valid_website(website):
    website = website.replace(" ", "")
    if not is_valid_url(website):
        logging.warning(f"Invalid URL format for website: {website}")
        return None

    base_url = get_base_url(website)
    if base_url.startswith("http://"):
        base_url = base_url[len("http://"):]
    elif base_url.startswith("https://"):
        base_url = base_url[len("https://"):]

    if base_url.startswith("www."):
        base_url = base_url[len("www."):]

    try:
        ip_address = socket.gethostbyname(base_url)
        logging.info(f"Resolved IP address for {base_url}: {ip_address}")
        return base_url
    except socket.error as e:
        logging.error(f"Error resolving IP address for {base_url}: {e}")
        return None


def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=50, fill='#'):
    percent = f"{100 * (iteration / float(total)):.{decimals}f}"
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='\r')
    if iteration == total:
        print()


def save_intermediate_results(results, output_file):
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        writer.writerow(['name', 'original_website', 'base_website', 'main_category', 'categories',
                             'rating', 'phone', 'address', 'link', 'email', 'status'])

        writer.writerows(results)
    logging.info(f"Intermediate results saved to {output_file}")


def process_websites(input_file, output_file, email_send, quota):
    results = []
    websites = set()
    full_url_websites = set()
    verified_emails_count = 0
    batch_size = 10  # Save results after processing each batch of 10 websites

    # Get previous valid emails' websites
    if os.path.isfile(output_file):
        with open(output_file, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)

            # Skip header row
            next(reader)

            for row in reader:
                websites.add(row[2])  # base_website
                full_url_websites.add(row[1])  # original_website
                results.append(row[:11])
        save_intermediate_results(results, output_file)

    with open(input_file, mode='r') as file:
        reader = csv.reader(file)
        next(reader, None)
        total_rows = sum(1 for _ in reader)

    with open(input_file, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for i, row in enumerate(reader, start=1):
            try:
                website = row.get('website')
                name = row.get('name')
                main_category = row.get('main_category')
                categories = row.get('categories')
                rating = row.get('rating')
                phone = row.get('phone')
                address = row.get('address')
                link = row.get('link')

                if website in full_url_websites:
                    logging.info(f"Ignore full website link: {website}")
                    continue

                full_url_websites.add(website)

                website_base_url = is_valid_website(website)
                if website_base_url:
                    if website_base_url in websites:
                        logging.info(f"Ignore website link: {website}")
                        continue
                    websites.add(website_base_url)
                    roles = ['info', 'contact']
                    for role in roles:
                        verified_emails_count += 1
                        email_receive = f"{role}@{website_base_url}"
                        status = is_valid_email(email_receive, email_send)
                        results.append([name, website, website_base_url, main_category, categories,
                                       rating, phone, address, link, email_receive, status])

                        if status == "Valid email":
                            break
                        else:
                            # Introduce a random delay between 1 and 10.0 seconds
                            delay = random.uniform(1.0, 10.0)
                            time.sleep(delay)

                    if quota and verified_emails_count >= quota:
                        break

                    # Introduce a random delay between 1 and 5.0 seconds
                    delay = random.uniform(1.0, 5.0)
                    time.sleep(delay)

                    print_progress_bar(i, total_rows, prefix='Progress',
                                    suffix='Complete', length=50)
                    logging.info(f"Processed {i}/{total_rows}")

                    if i % batch_size == 0:
                        save_intermediate_results(results, output_file)

            except Exception as e:
                logging.error(f"Error processing row {i}: {e}")
                continue

    save_intermediate_results(results, output_file)
    logging.info(f"Final results written to {output_file}")


if __name__ == "__main__":
    input_csv = 'all_results.csv'
    output_csv = 'emails.csv'
    quota = 500 # None or number
    email_send = 'your_email@example.com'
    process_websites(input_csv, output_csv, email_send, quota)
