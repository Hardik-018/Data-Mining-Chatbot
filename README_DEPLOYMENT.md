# Data Mining Chatbot — Hybrid deployment (free tier)

This package adapts the existing Colab chatbot for a public Netlify landing page + Render Python/Gradio backend. All seven study modes and image upload support are retained.

## What is preserved
- Exam Answer, Explain Topic, Numerical, Comparison, Quiz, Quick Revision, Web Answer (Internet)
- PDF text extraction and BM25 retrieval
- Gemini responses, Google Search tool in Web Answer mode, short conversation history and answer cache
- Image upload and image understanding
- Existing orange/light Gradio interface

## 1. Prepare the repository
1. Copy the contents of this folder into your GitHub project (repository root).
2. Put the two course PDFs (or other PDFs you are allowed to use) in `knowledge_base/`. The app indexes every `.pdf` file there.
3. Do not put API keys in GitHub. Do not commit `.env` files.
4. If the PDFs are copyrighted or provided by your professor, only publish/use them if you have permission. Consider keeping the repository private if needed.

## 2. Deploy the backend on Render
1. Sign in at https://render.com and choose **New → Web Service**.
2. Connect the GitHub repository containing these files.
3. Runtime: Python; Build command: `pip install -r requirements.txt`; Start command: `python app.py`.
4. Choose the **Free** instance.
5. In Render → Environment, add `GEMINI_API_KEY` with your own Gemini API key. Optional: set `GEMINI_MODEL` to a model available to your key/project.
6. Deploy. Copy the service URL, e.g. `https://your-service.onrender.com`.

The `render.yaml` file is included as a reference; the dashboard flow above is the simplest beginner route.

## 3. Connect the Netlify frontend
1. Open `netlify/index.html` and replace `https://YOUR-RENDER-SERVICE.onrender.com` with your actual Render URL.
2. In Netlify, choose **Add new site → Import an existing project** and connect the same GitHub repository.
3. Build settings: leave build command blank; publish directory: `netlify`.
4. Deploy. Netlify gives you a public website URL.

## 4. Test all features
- Open the Netlify URL and wait for the embedded Gradio app to load.
- Test each of the seven modes.
- Upload a JPG/PNG containing a question and ask the chatbot to solve it.
- Ask a question covered by your PDFs to verify retrieval.
- Test Web Answer (Internet) separately; Google Search availability depends on the Gemini model/API access and quota.

## Important free-tier limits
- Render Free web services spin down after 15 minutes without inbound traffic and can take about a minute to wake up. They are not always-on.
- Render's free filesystem is ephemeral. Keep PDFs in the Git repository (only if permitted) or use a suitable external persistent file source. Files uploaded by visitors are temporary.
- Do not use an uptime-ping workaround to bypass the free-tier sleep policy.
- Netlify is only the static landing page; Python, Gemini calls, PDF retrieval and image processing run on Render.

## Security
- Add API keys only as Render environment variables. Never paste keys into source code, notebook outputs, screenshots or GitHub.
- Use only Gemini keys you own and are authorized to use; respect API quotas and terms.
- The chatbot is public once deployed. Avoid putting confidential information in prompts or PDFs.

## Local test
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
# Set GEMINI_API_KEY in your shell, then:
python app.py
```
