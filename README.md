# AI-Powered Data Mining Chatbot

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Hardik-018/Data-Mining-Chatbot/blob/main/Data_Mining_Chatbot.ipynb)

🌐 **Live Chatbot:** [https://data-mining-chatbot.netlify.app](https://data-mining-chatbot.netlify.app)

💻 **GitHub Repository:** [https://github.com/Hardik-018/Data-Mining-Chatbot](https://github.com/Hardik-018/Data-Mining-Chatbot)

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
- **Gemini API key rotation:** Supports multiple API keys configured through environment variables on Render and Google Colab Secrets in the notebook.
- **Answer caching:** Stores recent text-question answers to reduce repeated API calls.
- **Error logging:** Records application and API errors to help identify issues.
- **Public chatbot access:** The application is publicly accessible through Netlify and does not require visitors to open Google Colab or provide their own Gemini API key.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application and backend logic |
| Google Gemini API (`google-genai`) | AI-generated explanations and answers |
| Gradio | Interactive chatbot interface |
| PyPDF | Extracts text from PDF course notes |
| BM25 (`rank_bm25`) | Retrieves relevant note sections |
| Pillow | Opens and processes uploaded question images |
| Google Colab & Google Drive | Original notebook execution and study materials |
| Render | Backend hosting and deployment |
| Netlify | Frontend hosting and public chatbot access |
| GitHub | Source-code management and version control |

## How It Works

The project uses a hybrid deployment architecture combining Netlify and Render.

### System Architecture

1. Students access the chatbot through the public Netlify website.
2. Netlify displays the Gradio chatbot hosted on Render through an embedded interface.
3. The Render backend runs the Python application and processes user questions.
4. PyPDF extracts readable text from the PDF course materials stored in the `knowledge_base/` folder.
5. The extracted text is split into overlapping chunks.
6. BM25 ranks the chunks according to their relevance to the student's question.
7. The most relevant passages, recent conversation context, and selected study mode are sent to Gemini.
8. Gemini generates a response, which is displayed in the Gradio chatbot interface.

For **Web Answer (Internet)** mode, the backend can use Google Search through Gemini when the search tool is available. If web search fails, it falls back to a response without live search.

## Run the Project on Render and Netlify

The chatbot is publicly deployed using a hybrid hosting setup.

**Live Application:** [Open Data Mining AI Chatbot](https://data-mining-chatbot.netlify.app)

### Deployment Architecture

| Platform | Responsibility |
|---|---|
| Netlify | Hosts the public landing page and embeds the chatbot |
| Render | Runs the Python backend and Gradio application |
| GitHub | Stores the project source code and deployment files |
| Google Gemini API | Generates AI-powered responses |

### Important Deployment Notes

- The application runs using the Python backend in `app.py`.
- Dependencies are installed using `requirements.txt`.
- Gemini API keys are configured through Render's Environment Variables section.
- Course-note PDFs are stored in the `knowledge_base/` folder.
- Gradio provides the interactive chatbot interface.
- Netlify displays the chatbot directly without requiring visitors to access Render separately.
- Render automatically deploys the application when changes are committed to the connected GitHub branch.
- Netlify automatically deploys the frontend when changes are committed to its connected GitHub repository.

**Free Hosting Limitation:** The Render free instance may spin down after periods of inactivity. The first request after inactivity can take approximately 50 seconds or longer to respond.

## Run the Project Locally

### 1. Clone the repository

```bash
git clone https://github.com/Hardik-018/Data-Mining-Chatbot.git
cd Data-Mining-Chatbot
```

### 2. Install dependencies

Run the following command:

```bash
pip install -r requirements.txt
```

### 3. Configure your own Gemini API key

This project requires a Gemini API key.

1. Obtain your API key through [Google AI Studio](https://aistudio.google.com/apikey).
2. Configure an environment variable named `GEMINI_KEY_1`.
3. Add your API key as its value.

The application also supports additional keys named `GEMINI_KEY_2`, `GEMINI_KEY_3`, and so on, if you choose to configure multiple keys.

**Every user running the project independently must provide and manage their own Gemini API key.** The author's API keys are not included in this repository.

Visitors using the publicly hosted chatbot do not need to provide their own API key.

Gemini API usage is subject to Google's quotas, pricing, and terms.

Never paste API keys directly into the Python code or commit them to GitHub.

### 4. Add PDF notes

Place your readable PDF course materials inside the following folder:

```text
knowledge_base/
├── data_mining_notes.pdf
└── data_mining_Notes (1).pdf
```

You can add your own PDF files to this folder. The retrieval pipeline expects readable/selectable PDF text. Scanned PDFs may not work correctly because OCR is not included.

### 5. Run the chatbot

Run the following command:

```bash
python app.py
```

The Gradio application will start and provide a local URL through which you can access the chatbot.

## Run the Project in Google Colab

The original notebook is also available for users who want to explore the project or run it independently.

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

**Every user must provide and manage their own Gemini API key.** The author's API keys are not included in this repository and are not shared with people who download the notebook.

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

- The application uses the Gemini model configured in its backend code.
- Answer length, request timeout, API-key cooldown, retrieved PDF passages, conversation history, and answer-cache size are configured in the application.
- Gemini availability, quotas, and usage limits depend on the user's account and Google's current policies.
- The PDF retrieval pipeline expects readable PDF text; OCR for scanned documents is not included.
- The deployed application runs independently of Google Colab.
- The Render free instance may spin down after inactivity, resulting in a wake-up delay.
- The original notebook continues to support Google Colab and Google Drive as an alternative execution method.
- The public chatbot can be accessed through the Netlify website, while the backend is hosted separately on Render.

## Repository Structure

```text
Data-Mining-Chatbot/
├── knowledge_base/
│   ├── data_mining_notes.pdf
│   └── data_mining_Notes (1).pdf
│
├── netlify/
│   └── index.html
│
├── .env.example
├── .gitignore
├── Data_Mining_Chatbot.ipynb
├── README.md
├── README_DEPLOYMENT.md
├── app.py
├── render.yaml
└── requirements.txt
```

The `knowledge_base/` folder contains the course-note PDFs used by the deployed chatbot. The `netlify/` folder contains the frontend landing page hosted on Netlify.

## Security and Privacy

- Store Gemini API keys in Render Environment Variables or Google Colab Secrets.
- Do not commit API keys, passwords, private logs, or personal information.
- Do not upload course PDFs or copyrighted material unless you have permission to share them.
- Users running the notebook independently should connect their own Google Drive and use documents they are authorized to access.
- The public chatbot link may be accessed by anyone who has the URL.
- Do not enter confidential or sensitive information into a publicly accessible chatbot.
- Clear notebook outputs before publishing if they contain file paths, logs, credentials, personal information, or temporary share links.

## Future Enhancements

- Add OCR support for scanned PDFs.
- Improve retrieval accuracy and evaluate answer quality.
- Explore additional AI model integrations.
- Add more course materials and study resources.
- Improve response evaluation and reliability.

## Study Resources

The chatbot uses PDF-based study materials to retrieve relevant information and generate answers.

The following resources are provided for educational purposes:

- [Data Mining Notes – PDF 1](https://drive.google.com/file/d/10HXr0TDsLY4w_4-L_Qol4ZxEbD_YAnUL/view?usp=sharing)
- [Data Mining Notes – PDF 2](https://drive.google.com/file/d/1mnNy6Kgv7c3avfSBk6cRGe6MB-Zc3unX/view?usp=drive_link)

## Author

**Hardik Pareek**  
MBA Finance & Data Science and AI  
Amity University Rajasthan

GitHub: [Hardik-018](https://github.com/Hardik-018)

---

If you find this project useful, feel free to explore the notebook and share feedback.
