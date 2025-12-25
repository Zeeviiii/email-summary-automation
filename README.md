# Email Summary Automation | אוטומציה לסיכום מיילים

מערכת אוטומטית לסיכום מיילים באמצעות בינה מלאכותית (AI). המערכת מתחברת לשרת IMAP, שולפת מיילים, ומסכמת אותם באמצעות מודלי AI מתקדמים.

## ✨ תכונות עיקריות

- 📧 **חיבור לשרת IMAP** - תמיכה בכל ספקי האימייל (Gmail, Outlook, וכו')
- 🤖 **סיכום AI מתקדם** - תמיכה ב-OpenAI GPT-4 ו-Anthropic Claude
- 🌍 **תמיכה רב-לשונית** - סיכומים בעברית, אנגלית וספרדית
- ⏰ **אוטומציה מתוזמנת** - הרצה אוטומטית על פי לוח זמנים
- 💾 **פורמטי פלט מגוונים** - TXT, JSON, HTML
- 📤 **שליחה באימייל** - אפשרות לשלוח סיכום באימייל
- 🎨 **ממשק צבעוני** - לוגים ברורים וקלים לקריאה

## 📋 דרישות מקדימות

- Python 3.8 ומעלה
- חשבון אימייל עם גישת IMAP
- API key של OpenAI או Anthropic

## 🚀 התקנה

### 1. שכפול הפרויקט

```bash
git clone <repository-url>
cd Ddd
```

### 2. יצירת סביבה וירטואלית

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. התקנת תלויות

```bash
pip install -r requirements.txt
```

### 4. הגדרת קונפיגורציה

העתק את קובץ הדוגמה ועדכן אותו:

```bash
cp config/config.example.yaml config/config.yaml
```

ערוך את `config/config.yaml` והזן את הפרטים שלך:

```yaml
email:
  imap_server: "imap.gmail.com"
  imap_port: 993
  email_address: "your-email@gmail.com"
  password: "your-app-password"

summarization:
  provider: "anthropic"  # או "openai"
  anthropic_api_key: "your-api-key"
```

### 5. הגדרת App Password (Gmail)

אם אתה משתמש ב-Gmail, אתה צריך ליצור App Password:

1. עבור ל-https://myaccount.google.com/security
2. הפעל אימות דו-שלבי (2FA)
3. עבור ל-"App passwords"
4. צור סיסמה חדשה ליישום
5. השתמש בסיסמה זו ב-`config.yaml`

## 📖 שימוש

### הרצה חד-פעמית

```bash
python main.py --once
```

### הרצה מתוזמנת

```bash
python main.py --schedule
```

המערכת תריץ סיכום אוטומטית על פי הזמן שהוגדר ב-`config.yaml`.

### עזרה

```bash
python main.py --help
```

## ⚙️ הגדרות קונפיגורציה

### Email Settings

```yaml
email:
  imap_server: "imap.gmail.com"     # שרת IMAP
  imap_port: 993                     # פורט IMAP (בדרך כלל 993)
  email_address: "user@gmail.com"    # כתובת אימייל
  password: "app-password"           # סיסמת אפליקציה
  folder: "INBOX"                    # תיקיית מיילים
  days_to_check: 7                   # כמה ימים אחורה לבדוק
  max_emails: 50                     # מקסימום מיילים לעיבוד
```

### Summarization Settings

#### שימוש ב-Anthropic Claude (מומלץ)

```yaml
summarization:
  provider: "anthropic"
  anthropic_api_key: "sk-ant-..."
  anthropic_model: "claude-3-5-sonnet-20241022"
  max_tokens: 500
  temperature: 0.3
  summary_language: "he"  # he/en/es
```

#### שימוש ב-OpenAI GPT

```yaml
summarization:
  provider: "openai"
  openai_api_key: "sk-..."
  openai_model: "gpt-4-turbo-preview"
  max_tokens: 500
  temperature: 0.3
  summary_language: "he"
```

### Automation Settings

```yaml
automation:
  enabled: true        # הפעל/כבה אוטומציה מתוזמנת
  schedule: "09:00"    # זמן הרצה יומי (HH:MM)
```

### Output Settings

```yaml
output:
  output_dir: "summaries"           # תיקיית פלט
  format: "txt"                     # txt/json/html
  send_email: false                 # שלח סיכום באימייל
  recipient_email: "user@gmail.com" # נמען לשליחה
```

## 🗂️ מבנה הפרויקט

```
Ddd/
├── main.py                    # סקריפט ראשי
├── requirements.txt           # תלויות Python
├── README.md                  # תיעוד
├── .gitignore                # קבצים להתעלמות
├── config/
│   ├── config.example.yaml   # דוגמת קונפיגורציה
│   └── config.yaml           # קונפיגורציה אישית (לא בגרסאות)
├── src/
│   ├── __init__.py
│   ├── email_fetcher.py      # מודול שליפת מיילים
│   ├── email_summarizer.py   # מודול סיכום AI
│   ├── config_loader.py      # טעינת קונפיגורציה
│   ├── logger_setup.py       # הגדרת לוגים
│   └── output_handler.py     # ניהול פלט
├── logs/                      # קבצי לוג (נוצר אוטומטית)
└── summaries/                 # סיכומים (נוצר אוטומטית)
```

## 💡 דוגמאות שימוש

### דוגמה 1: סיכום יומי אוטומטי

```yaml
# config/config.yaml
automation:
  enabled: true
  schedule: "08:00"  # כל בוקר ב-8:00
```

```bash
python main.py --schedule
```

### דוגמה 2: סיכום שבועי

```yaml
email:
  days_to_check: 7  # שבוע אחרון
  max_emails: 100
```

```bash
python main.py --once
```

### דוגמה 3: שליחת סיכום באימייל

```yaml
output:
  format: "html"
  send_email: true
  recipient_email: "manager@company.com"
```

## 🔐 אבטחה

- **אל תשמור API keys בקוד** - השתמש ב-`config.yaml` או במשתני סביבה
- **השתמש ב-App Passwords** - לא בסיסמאות חשבון רגילות
- **הוסף `config.yaml` ל-.gitignore** - כדי שלא לשתף מידע רגיש

### שימוש במשתני סביבה

```bash
# .env
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
ANTHROPIC_API_KEY=sk-ant-...
```

המערכת תקרא אוטומטית ממשתני סביבה אם הם מוגדרים.

## 🐛 פתרון בעיות

### בעיה: "Authentication failed"

**פתרון:**
- ודא שהשתמשת ב-App Password ולא בסיסמה רגילה
- בדוק שאימות דו-שלבי מופעל (לגרסאות Google)

### בעיה: "Configuration file not found"

**פתרון:**
```bash
cp config/config.example.yaml config/config.yaml
```

### בעיה: "API key invalid"

**פתרון:**
- ודא שה-API key תקין ופעיל
- בדוק שבחרת את הספק הנכון (openai/anthropic)

### בעיה: "No emails found"

**פתרון:**
- בדוק את הגדרת `days_to_check`
- ודא שיש מיילים בתיקייה שבחרת
- בדוק את חיבור האינטרנט

## 📊 פורמטי פלט

### TXT
```
================================================================================
סיכום מיילים - 2025-12-25 10:30:00
================================================================================

מספר מיילים שנסרקו: 15

[סיכום AI...]
```

### JSON
```json
{
  "timestamp": "2025-12-25T10:30:00",
  "email_count": 15,
  "summary": "...",
  "emails": [...]
}
```

### HTML
דוח HTML מעוצב עם CSS, מתאים לצפייה בדפדפן.

## 🤝 תרומה

תרומות יתקבלו בברכה! אנא:

1. צור Fork של הפרויקט
2. צור branch לפיצ'ר שלך
3. Commit את השינויים
4. Push ל-branch
5. פתח Pull Request

## 📝 רישיון

פרויקט זה הוא קוד פתוח ונמצא תחת רישיון MIT.

## 📧 יצירת קשר

לשאלות או בעיות, אנא פתח Issue בגיטהאב.

## 🙏 תודות

- OpenAI GPT-4 - מודל שפה מתקדם
- Anthropic Claude - מודל שפה מתקדם
- Python IMAP - ספריית אימייל
- וכל התורמים לפרויקט

---

**נוצר ב-2025 | Made with ❤️ for email productivity**
