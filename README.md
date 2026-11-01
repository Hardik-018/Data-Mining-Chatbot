# AI-Powered Data Mining Chatbot

An AI-powered study assistant designed to help students understand Data Mining concepts, practise numerical problems, prepare exam answers, revise important topics, and ask questions using their own course notes.

Built using **Python, Google Gemini API, BM25 Information Retrieval, PDF Processing, and Gradio**.

## Key Features

- **PDF-based question answering:** Retrieves relevant passages from uploaded course notes using BM25 before generating an answer.
- **Seven study modes:**
  - Exam Answer
  - Explain Topic
  - Numerical
  - Comparison
  - Quiz
  - Quick Revision
  - Web Answer (Internet)
- **Image-based questions:** Upload an image containing a question, formula, table, or diagram.
- **Conversation context:** Uses recent chat history to support follow-up questions.
- **Gemini API key rotation:** Supports multiple API keys stored in Google Colab Secrets and rotates between available keys when quota errors occur.
- **Answer caching:** Stores recent text-question answers to reduce repeated API calls.
- **Error logging:** Records application and API errors in a log file in Google Drive.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application and backend logic |
| Google Gemini API (`google-genai`) | AI-generated explanations and answers |
| Gradio | Interactive chatbot interface |
| PyPDF | Extracts text from PDF course notes |
| BM25 (`rank_bm25`) | Retrieves relevant note sections |
| Pillow | Opens and processes uploaded question images |
| Google Colab & Google Drive | Notebook execution, secrets, notes, and log storage |

## How It Works

1. The notebook connects to the user's Google Drive and loads the configured course-note PDFs.
2. PyPDF extracts readable text from the PDF pages.
3. The extracted text is split into overlapping chunks.
4. BM25 ranks the chunks according to their relevance to the student's question.
5. The most relevant passages, recent conversation context, and selected study mode are sent to Gemini.
6. Gemini generates a response, which is displayed in the Gradio chatbot.

For **Web Answer (Internet)** mode, the backend can use Google Search through Gemini when the search tool is available. If web search fails, it falls back to a response without live search.

## Run the Project in Google Colab

### 1. Open the notebook

Download `Data_Mining_Chatbot.ipynb` from this repository and open it in [Google Colab](https://colab.research.google.com/).

### 2. Install dependencies

Run the notebook's dependency-installation cell, or install the packages from this repository:

```bash
pip install -r requirements.txt
```

### 3. Configure your own Gemini API key

This project requires a Gemini API key.

1. Obtain your own API key through [Google AI Studio](https://aistudio.google.com/apikey).
2. In Google Colab, open the **Secrets** panel.
3. Add your key as a secret named `GEMINI_KEY_1`.
4. Enable notebook access for that secret.

The notebook also supports additional secrets named `GEMINI_KEY_2`, `GEMINI_KEY_3`, and so on, up to `GEMINI_KEY_9`, if you choose to configure multiple keys. It also supports the older single-secret name `GEMINI_API_KEY`.

**Every user must provide and manage their own Gemini API key. The author's API keys are not included in this repository and are not shared with people who download the notebook.** Gemini API usage is subject to Google's quotas, pricing, and terms.

Never paste API keys directly into the notebook or commit them to GitHub.

### 4. Connect your own Google Drive and add PDF notes

Run the notebook's Google Drive connection cell and authorize access using your own Google account.

Create this folder in the root of your Google Drive:

```text
MyDrive/
└── DataMiningChatbot/
    ├── data_mining_notes.pdf
    └── data_mining_Notes (1).pdf
```

The current notebook expects both PDF files with these exact filenames. Add your own PDF files using those names, or update the file paths in the notebook to match your filenames.

**Each user must connect their own Google Drive and provide their own PDF materials.** Downloading this notebook does not give anyone access to the author's Drive, files, or account.

The current retrieval pipeline expects readable/selectable PDF text. Scanned PDFs may not work correctly because OCR is not included.

### 5. Run the notebook cells in order

Run each cell from top to bottom:

1. Install packages.
2. Connect Google Drive, load API keys, and verify PDF files.
3. Build the PDF retrieval and Gemini backend.
4. Create the Gradio chatbot interface.
5. Launch the chatbot.

The launch cell uses Gradio sharing to provide a temporary link to the running application. Anyone with access to an active public share link may be able to interact with that running app. Do not enter confidential information into a public session.

## Configuration Notes and Limitations

- The notebook uses the Gemini model configured in its backend cell.
- Answer length, request timeout, API-key cooldown, retrieved PDF passages, conversation history, and answer-cache size are configured in the notebook.
- Gemini availability, quotas, and usage limits depend on the user's account and Google's current policies.
- The current PDF retrieval pipeline expects readable PDF text; OCR for scanned documents is not included.
- The project is designed to run in Google Colab with Google Drive and a user-provided Gemini API key. It is not a permanently hosted service.

## Repository Structure

```text
Data-Mining-Chatbot/
├── Data_Mining_Chatbot.ipynb
├── README.md
├── requirements.txt
├── .gitignore
└── screenshots/
    └── chatbot_interface.png
```

The `screenshots/` folder is optional. Add screenshots only if they do not expose API keys, private files, personal information, or active session links.

## Security and Privacy

- Store Gemini API keys in Google Colab Secrets.
- Do not commit API keys, passwords, private logs, or personal information.
- Do not upload course PDFs or copyrighted material unless you have permission to share them.
- Users should connect only their own Google Drive and use documents they are authorized to access.
- A public Gradio share link may be accessible to anyone who has the link while it is active. Stop the session when it is no longer needed.
- Clear notebook outputs before publishing if they contain file paths, logs, credentials, personal information, or temporary share links.

## Future Enhancements

- Add OCR support for scanned PDFs.
- Improve retrieval accuracy and evaluate answer quality.
- Explore additional AI model integrations.
- Add deployment options beyond a temporary Gradio share link.

## Author

**Hardik Pareek**  
MBA Finance Student | Amity University Rajasthan

GitHub: [Hardik-018](https://github.com/Hardik-018)

---

If you find this project useful, feel free to explore the notebook and share feedback.
