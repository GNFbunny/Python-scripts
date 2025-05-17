import fitz  # PyMuPDF
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ====== CONFIGURATION ======
SERVICE_ACCOUNT_FILE = 'service-account-key.json'
FORM_ID = '1Boo7zp3Kpyn6SMlhJAf2rpXJjjpU9pEalzOPdX5GYMY'
PDF_PATH = "altruism2.pdf"
# ===========================

# Authenticate with Google API
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=[
        "https://www.googleapis.com/auth/forms.body",
        "https://www.googleapis.com/auth/forms.responses.readonly",
        "https://www.googleapis.com/auth/drive"
    ]
)

# Build the API client
service = build('forms', 'v1', credentials=credentials)

# Get the existing number of items
def get_existing_item_count(form_id):
    try:
        form = service.forms().get(formId=form_id).execute()
        items = form.get("items", [])
        print(f"🔍 Existing questions in form: {len(items)}")
        return len(items)
    except Exception as e:
        print("❌ Failed to get form details:", e)
        return 0

# Extract questions and options from PDF
def extract_questions_from_pdf(pdf_path):
    questions = []
    doc = fitz.open(pdf_path)

    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        lines = page.get_text("text").split("\n")

        i = 0
        while i + 5 < len(lines):
            question = lines[i].strip()
            options = [lines[i + j].strip() for j in range(1, 6)]

            if question and all(options):
                questions.append({"question": question, "options": options})
                print(f"✅ Parsed question: {question}")
            else:
                print(f"⚠️ Skipping malformed block at lines {i}-{i+5}")
            i += 6

    print(f"\n✅ Total questions extracted: {len(questions)}")
    return questions

# Add questions to the form
def append_to_google_form(form_id, questions):
    try:
        start_index = get_existing_item_count(form_id)

        for i, q in enumerate(questions):
            index = start_index + i
            print(f"📌 Adding to index {index}: {q['question']}")
            request_body = {
                "requests": [
                    {
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
                                "index": index
                            }
                        }
                    }
                ]
            }

            response = service.forms().batchUpdate(formId=form_id, body=request_body).execute()
            print(f"✅ Successfully added: {q['question']}")

        # Confirm final form length
        final_count = get_existing_item_count(form_id)
        print(f"✅ Final total questions in form: {final_count}")

    except HttpError as e:
        print(f"❌ API error: {e}")
    except Exception as e:
        print(f"❌ General error: {e}")

# ==== MAIN ====
questions = extract_questions_from_pdf(PDF_PATH)
append_to_google_form(FORM_ID, questions)
