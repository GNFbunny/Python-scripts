import fitz  # PyMuPDF
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

print("Script is starting...")

# Path to your service account JSON file
SERVICE_ACCOUNT_FILE = 'service-account-key.json'
YOUR_GMAIL = 'kaushal.pandey32047@gmail.com'  # <-- Change this to your Gmail

# Authenticate with the Google API
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=[
        "https://www.googleapis.com/auth/forms.body",
        "https://www.googleapis.com/auth/forms.responses.readonly",
        "https://www.googleapis.com/auth/drive"  # Required for sharing
    ]
)

print("Google API credentials loaded successfully.")

# Create the Forms and Drive API clients
service = build('forms', 'v1', credentials=credentials)
drive_service = build('drive', 'v3', credentials=credentials)

# PDF file path
pdf_path = "altruism.pdf"

# Extract questions and 3 options from the PDF
def extract_questions_from_pdf(pdf_path):
    questions = []
    doc = fitz.open(pdf_path)

    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        lines = page.get_text("text").split("\n")

        i = 0
        while i + 3 < len(lines):
            question = lines[i].strip()
            options = [
                lines[i + 1].strip(),
                lines[i + 2].strip(),
                lines[i + 3].strip()
            ]

            # Skip empty lines or malformed blocks
            if question and all(options):
                questions.append({
                    "question": question,
                    "options": options
                })
                print(f"✅ Question added: {question}")
            else:
                print(f"⚠️ Skipping malformed block at lines {i}-{i+3}")

            i += 4  # Move to next block

    print(f"\n✅ Total questions extracted: {len(questions)}")

    # Reverse the order to match the top-down sequence of the PDF
    questions.reverse()

    return questions

# Create Google Form with extracted questions
def create_google_form(form_title, questions):
    try:
        form = service.forms().create(
            body={
                "info": {
                    "title": form_title
                }
            }
        ).execute()

        form_id = form["formId"]
        print(f"Form created: https://docs.google.com/forms/d/{form_id}/edit")

        # ✅ Share with your Gmail
        try:
            drive_service.permissions().create(
                fileId=form_id,
                body={
                    'type': 'user',
                    'role': 'writer',
                    'emailAddress': YOUR_GMAIL
                },
                fields='id'
            ).execute()
            print(f"✅ Form shared with {YOUR_GMAIL}")
        except HttpError as e:
            print("⚠️ Failed to share form:", e)

        # Add questions
        requests = []

        for q in questions:
            print(f"Adding question: {q['question']}")
            requests.append({
                "createItem": {
                    "item": {
                        "title": q['question'],
                        "questionItem": {
                            "question": {
                                "required": True,
                                "choiceQuestion": {
                                    "type": "RADIO",
                                    "options": [{"value": option} for option in q['options']],
                                    "shuffle": False
                                }
                            }
                        }
                    },
                    "location": {
                        "index": 0
                    }
                }
            })

        if not requests:
            print("No questions to add. The request list is empty.")
            return

        service.forms().batchUpdate(
            formId=form_id,
            body={"requests": requests}
        ).execute()

        print("Questions added successfully.")

    except Exception as e:
        print("Failed to add questions.")
        print("Error:", e)

# Main execution
form_title = "Altruism Quiz"
questions = extract_questions_from_pdf(pdf_path)
create_google_form(form_title, questions)
