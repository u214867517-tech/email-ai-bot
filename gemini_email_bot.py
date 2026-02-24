import os
import imaplib
import email
import smtplib
import requests
from email.mime.text import MIMEText

IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_unread_emails():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        mail.select("inbox")
        result, data = mail.search(None, '(UNSEEN)')
        unread_msg_nums = data[0].split()
        messages = []
        for num in unread_msg_nums:
            result, msg_data = mail.fetch(num, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            sender = email.utils.parseaddr(msg["From"])[1]
            subject = msg["Subject"] if msg["Subject"] else "(ללא נושא)"
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        charset = part.get_content_charset() or "utf-8"
                        body += part.get_payload(decode=True).decode(charset, errors="ignore")
            else:
                charset = msg.get_content_charset() or "utf-8"
                body += msg.get_payload(decode=True).decode(charset, errors="ignore")
            messages.append({"from": sender, "subject": subject, "body": body})
        mail.logout()
        return messages
    except Exception as e:
        print(f"[!] Error fetching emails: {e}")
        return []

def send_email(to_email, subject, body_text):
    try:
        formatted_text = body_text.replace('\n', '<br>')
        html_body = f"<html><body dir='rtl'>{formatted_text}</body></html>"
        msg = MIMEText(html_body, _subtype='html', _charset='utf-8')
        msg['From'] = EMAIL_ACCOUNT
        msg['To'] = to_email
        msg['Subject'] = subject
        with smtplib.SMTP_SSL(SMTP_SERVER, 465) as server:
            server.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ACCOUNT, to_email, msg.as_string())
    except Exception as e:
        print(f"[!] Error sending email: {e}")

def get_gemini_reply(prompt):
    try:
        url = f"[https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=](https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=){GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        data = {"contents": [{"parts": [{"text": "תענה למייל הבא בעברית (ללא נושא, רק גוף התשובה). המייל:\n" + prompt}]}]}
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return "אירעה שגיאה בחיבור לבינה המלאכותית."
    except Exception:
        return "שגיאה פנימית."

def main():
    emails = get_unread_emails()
    for msg in emails:
        reply = get_gemini_reply(msg["body"])
        send_email(msg["from"], f"Re: {msg['subject']}", reply)

if __name__ == "__main__":
    main()
