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
        print(f"[*] מתחבר לתיבת המייל: {EMAIL_ACCOUNT}...")
        if not EMAIL_ACCOUNT or not EMAIL_PASSWORD:
            print("[!] שגיאה: כתובת אימייל או סיסמה חסרים (הגדרות GitHub Secrets).")
            return []

        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        mail.select("inbox")
        result, data = mail.search(None, '(UNSEEN)')
        unread_msg_nums = data[0].split()
        
        print(f"[*] נמצאו {len(unread_msg_nums)} מיילים חדשים שלא נקראו.")
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
    except imaplib.IMAP4.error as e:
        print(f"[!] שגיאת התחברות ל-Gmail (אולי סיסמת אפליקציה שגויה?): {e}")
        return []
    except Exception as e:
        print(f"[!] שגיאה בשליפת מיילים: {e}")
        return []

def send_email(to_email, subject, body_text):
    try:
        print(f"[*] שולח תגובה אל: {to_email}...")
        formatted_text = body_text.replace('\n', '<br>')
        html_body = f"<html><body dir='rtl'>{formatted_text}</body></html>"
        msg = MIMEText(html_body, _subtype='html', _charset='utf-8')
        msg['From'] = EMAIL_ACCOUNT
        msg['To'] = to_email
        msg['Subject'] = subject
        with smtplib.SMTP_SSL(SMTP_SERVER, 465) as server:
            server.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ACCOUNT, to_email, msg.as_string())
        print(f"[*] המייל נשלח בהצלחה!")
    except Exception as e:
        print(f"[!] שגיאה בשליחת המייל: {e}")

def get_gemini_reply(prompt):
    try:
        if not GEMINI_API_KEY:
             print("[!] שגיאה: חסר מפתח API של Gemini (הגדרות GitHub Secrets).")
             return "שגיאת מערכת: מפתח API חסר."
             
        print("[*] שולח בקשה לבינה המלאכותית...")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        headers = {"Content-Type": "application/json"}
        data = {"contents": [{"parts": [{"text": "תענה למייל הבא בעברית (ללא נושא, רק גוף התשובה). המייל:\n" + prompt}]}]}
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            print("[*] התקבלה תשובה מ-Gemini בהצלחה.")
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        else:
            print(f"[!] שגיאת תקשורת עם Gemini: {response.text}")
            return "אירעה שגיאה בחיבור לבינה המלאכותית."
    except Exception as e:
        print(f"[!] שגיאה פנימית בקריאה ל-API: {e}")
        return "שגיאה פנימית."

def main():
    print("=== מתחיל ריצה של בוט האימייל ===")
    emails = get_unread_emails()
    
    if not emails:
        print("[*] אין מיילים חדשים להשיב עליהם. מסיים ריצה.")
        return
        
    for msg in emails:
        print(f"\n[*] מעבד הודעה מ: {msg['from']} | נושא: {msg['subject']}")
        reply = get_gemini_reply(msg["body"])
        send_email(msg["from"], f"Re: {msg['subject']}", reply)
        
    print("\n=== סיום ריצה ===")

if __name__ == "__main__":
    main()
