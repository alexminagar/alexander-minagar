# Alexander Minagar

A personal portfolio with four pages: a home page, a film page, a flashcard app, and a French sentence analyzer. The top navigation's Projects link jumps to the three project cards on the home page.

Open `START_HERE.html` for the illustrated setup guide. This repository is prepared for Vercel: GitHub holds the source files, while Vercel serves the website and runs its Python endpoint.

## What is included

| File | Purpose |
| --- | --- |
| `index.html` | Home and three project links |
| `film.html` | Film player and editable production details |
| `flashcards.html` | Preloaded decks and a study session |
| `french.html` | French sentence input and analysis results |
| `assets/js/site-content.js` | Name, introduction, and film content |
| `assets/js/decks.js` | The three preloaded flashcard decks |
| `api/analyze.py` | Python endpoint for French analysis |
| `requirements.txt` | Python dependencies and the French model |
| `pyproject.toml` | Python 3.12 requirement and dependency metadata |
| `vercel.json` | Deployment configuration |
| `serve.py` | Local development server for the pages and API |

The flashcards have fixed initial settings, 12 cards per deck, and no login, card editor, scheduling, or stored progress. The decks cover film language, French essentials, and web basics. Finishing a deck offers ways to repeat, shuffle, choose another deck, visit the French analyzer, or return home.

The French analyzer sends a sentence of up to 500 characters to this site's Python endpoint. It uses spaCy 3.8.18 and the French model `fr_core_news_md` 3.8.0. Apostrophe variants are normalized internally for parsing while the original sentence is displayed. Its grammatical labels are model predictions and can be wrong even for short sentences. There is no paid AI service or API key to configure.

## Publish through GitHub and Vercel

1. Extract the ZIP and open the folder that directly contains `index.html`.
2. Sign in to [GitHub](https://github.com). Create a new public repository named `alexander-minagar`. Enable the initial README and create the repository.
3. Choose **Add file → Upload files**. Drag in the extracted files and their folders, including `assets` and `api`. Upload the contents, not the outer folder or ZIP. Commit the upload to `main`.
4. Check that `index.html`, `requirements.txt`, `pyproject.toml`, and `vercel.json` appear in the repository's top-level file list. The `api` folder should contain `analyze.py`.
5. Go to [vercel.com/new](https://vercel.com/new), sign in, select your personal Hobby account, connect GitHub, and import this repository.
6. Use the settings below, then click **Deploy**. Wait for the deployment to show **Ready** and open the production URL Vercel provides.

| Vercel setting | Value |
| --- | --- |
| Framework Preset | `Other` |
| Root Directory | Repository root, shown as `./` |
| Build Command | Empty; if an Override switch is shown, enable it and leave the command blank |
| Output Directory | Default; do not set `dist`, `build`, or `public` |
| Install Command | Default; let the Python runtime install `requirements.txt` |
| Environment Variables | None required |

The production address will resemble `https://alexander-minagar.vercel.app`; Vercel may assign a different name if that one is taken. Use the actual URL shown in your dashboard.

Vercel Hobby is intended for personal, noncommercial projects and has usage limits. This project does not require upgrading to Pro for its basic features. The current plan details are linked below.

GitHub Pages alone will not run the Python endpoint. You do not need to enable GitHub Pages when using these instructions.

## Check the deployed site

- Open all three project links from Home.
- In Flashcards, choose a deck, reveal an answer, move between cards, and finish a session.
- In the French analyzer, enter `Le chat mange une pomme.` and run the analysis. In the word-by-word table, look for `chat` as a subject, `mange` as a verb, and `pomme` as an object. Automatic labels can be wrong even for short sentences, and predictions can change with model updates.
- The first French request after inactivity can take longer while the Python function loads its model.
- The film page initially displays a clearly identified placeholder. Add your own footage and details below.

## Add your film and personal text

Edit `assets/js/site-content.js` in a text editor or open it on GitHub and select the pencil icon. Change the field values while keeping the quotation marks, commas, and braces intact.

| Field | What to put there |
| --- | --- |
| `name`, `intro` | Your name and short introduction |
| `film.title`, `film.description` | Film title and a short description |
| `film.year`, `film.runtime`, `film.role` | Actual year, running time, and your contribution |
| `film.synopsis`, `film.credits` | Synopsis and real production credits |
| `film.videoUrl` | Your YouTube/Vimeo link or a local MP4 path |
| `film.poster` | An image path such as `assets/images/my-film-poster.jpg` |
| `film.captionsUrl` | Optional WebVTT caption file for a directly hosted video |

For the easiest video setup, upload the film to your own YouTube or Vimeo account, allow embedding, then place its link in `videoUrl`. A local video can instead be placed in `assets/media` and referenced as `assets/media/film.mp4`. A video platform handles large footage more conveniently; GitHub's browser uploader has a per-file limit.

The film itself, its title, synopsis, credits, dates, and your exact role were not supplied. Replace the placeholders with your real information before presenting the page as a completed film case study. Empty optional production details are hidden.

## Change preloaded flashcards

This is an author edit; visitors never need to enter cards. Edit `assets/js/decks.js`. Each deck in `window.FLASHCARD_DECKS` contains `id`, `title`, `description`, `theme`, `label`, and `cards`. A card looks like this:

```javascript
{
  question: "What does bonjour mean?",
  answer: "Hello or good day.",
  note: "A common French greeting."
}
```

Keep each deck's `id` unique and preserve the existing array/object structure. The app derives its displayed card counts from the data.

## Update the published site

Edit or upload changed files in the same GitHub repository and commit to `main`. Vercel's connected project will deploy the update. Wait for the latest deployment to show Ready before checking the production URL. Keep the existing folder paths and filename capitalization.

## Preview locally

You can double-click `index.html` to inspect the portfolio and flashcards. The French analyzer needs its Python endpoint, so use the deployed Vercel site or the local server below for that feature.

Install Python 3.12, then open a terminal in the extracted project folder.

macOS or Linux:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python serve.py
```

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe serve.py
```

Open `http://127.0.0.1:8000` or the local address printed by the server. Press Ctrl+C in the terminal to stop it. The dependency installation needs internet access and downloads the French model. Do not upload the local `.venv` folder to GitHub.

Opening `/api/analyze` directly returns a small status response; it does not analyze text or prove that model loading succeeded. Submitting a sentence from the French page tests the actual analysis request.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Home returns 404 | `index.html` must be at the configured repository root. Check Framework Other and the default Output Directory. |
| Pages have no styling or images | Upload the complete `assets` folder; preserve its nested paths and filename case. |
| French analysis fails from a double-clicked file | Use the deployed website or `serve.py`. A `file://` page has no Python server. |
| French endpoint returns 404 after deployment | Verify `api/analyze.py`, `vercel.json`, and `requirements.txt` were uploaded at the expected paths. Check the deployment's function list. |
| Python dependency or model installation fails | Open Vercel's build log and find the first installation error. Keep the provided version files and model dependency intact; confirm the model download URL is reachable before retrying. |
| French analysis returns an error | Inspect the deployment's runtime logs. Confirm the model installed successfully, then retry a short French sentence after the first model load. |
| Film does not play | Check the link and the video's embedding/privacy settings. For local video, confirm its filename and path exactly match `videoUrl`. |
| A change is missing | Check that the latest GitHub commit has a Ready deployment. Reload the production URL. |

## Verification included

The backend was checked with 11 tests using the actual installed French model. After installing dependencies, run them with your virtual environment's Python:

```bash
python -m unittest discover -s tests -v
```

Replace `python` with `.venv/bin/python` on macOS/Linux or `.\.venv\Scripts\python.exe` on Windows if the environment is not activated.

Browser checks covered a complete 12-card session, repeat and shuffle, switching decks, keyboard study controls, real French analysis, selecting word details, blank-input validation, and page layouts at desktop and 390-pixel widths. Actual film playback awaits your video URL. The package has not been deployed to your Vercel account; verify the production deployment using the checklist above.

## Official documentation

- [Adding files to GitHub](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository)
- [Vercel Git deployments](https://vercel.com/docs/git)
- [Vercel build settings](https://vercel.com/docs/builds/configure-a-build)
- [Vercel Python functions in `/api`](https://vercel.com/docs/functions/runtimes/python/api-directory)
- [Vercel Hobby plan](https://vercel.com/docs/plans/hobby)
- [Vercel pricing and permitted Hobby use](https://vercel.com/pricing)
- [spaCy French models](https://spacy.io/models/fr)

Setup guidance checked November 13, 2026. Hosting interfaces and plan limits may change.
