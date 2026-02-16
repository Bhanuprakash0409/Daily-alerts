import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import os

# ========= CONFIG =========
SEARCH_TERMS = [
    "Entry Level Data Analytics fresher jobs",
    "Entry Level Data Engineer fresher jobs"
]

EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

MIN_DATE_DIFF = 1   # jobs posted in the last 1 day
# ==========================


def fetch_jobs_from_site(search_query):
    """
    Example pulling from a public job board (Indeed)
    or other site with scrape-friendly HTML.
    """
    url = f"https://www.indeed.com/jobs?q={requests.utils.quote(search_query)}&sort=date"
    
    # Add headers to mimic a real browser to avoid being blocked
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error fetching jobs: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    job_list = []
    # Updated selectors for modern Indeed layout
    for card in soup.find_all("div", class_="job_seen_beacon"):
        title_tag = card.find("h2", class_="jobTitle")
        company_tag = card.find("span", {"data-testid": "company-name"})
        location_tag = card.find("div", {"data-testid": "text-location"})
        date_tag = card.find("span", class_="date")

        if title_tag and company_tag and location_tag and date_tag:
            posted_text = date_tag.text.strip()
            # filter for "1 day ago", "just posted", etc.
            if "day" in posted_text or "just" in posted_text.lower():
                link_tag = title_tag.find("a")
                link = "https://www.indeed.com" + link_tag["href"] if link_tag else "N/A"
                job_list.append({
                    "title": title_tag.text.strip(),
                    "company": company_tag.text.strip(),
                    "location": location_tag.text.strip(),
                    "link": link
                })

    return job_list


def compile_jobs():
    all_jobs = []

    for term in SEARCH_TERMS:
        jobs = fetch_jobs_from_site(term)
        all_jobs.extend(jobs)

    return all_jobs


def send_email(job_entries):
    if not job_entries:
        body = "No new entry-level roles found in the last 24 hours."
    else:
        body = "New Entry-Level Jobs Found:\n\n"
        for i, job in enumerate(job_entries, start=1):
            body += (
                f"{i}. {job['title']}\n"
                f"Company: {job['company']}\n"
                f"Location: {job['location']}\n"
                f"Apply: {job['link']}\n\n"
            )

    msg = MIMEText(body)
    msg["Subject"] = f"Daily Job Alert | {datetime.now().strftime('%Y-%m-%d')}"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())


if __name__ == "__main__":
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        print("Error: Environment variables EMAIL_SENDER or EMAIL_PASSWORD are missing.")
    else:
        recent_jobs = compile_jobs()
        send_email(recent_jobs)
