# TFEX Terminal V4

Streamlit wrapper for the TFEX Terminal live-account shell.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Cloud

Set the main file to `app.py`.

The app is currently a live-account shell with demo trading data removed. TFEX credentials should be stored in Streamlit Secrets when API integration is added; never commit real secrets to GitHub.

## Layout fix

The embedded terminal is configured to use the available Streamlit width without a nested vertical scrollbar. The page is responsive for desktop and smaller screens.
