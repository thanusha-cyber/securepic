# SecurePic Studio

A redesigned image security workspace built with Streamlit.

## Setup (Windows / VS Code)

1. Open this `securepic` folder in VS Code.
2. Open Terminal > New Terminal.
3. Run `python -m pip install -r requirements.txt`.
4. Run `python -m streamlit run app.py`.
5. Open the local URL shown in the terminal (usually http://localhost:8501).

## Features

- Protect: Fernet authenticated encryption, download ciphertext and key.
- Restore: decrypt ciphertext with the corresponding key and download the image.
- Verify: SHA-256 exact file comparison.
- Visual Lab: highlight pixel differences with a threshold and bounding box.
- Reports: export a self-contained HTML report including SHA-256 values and embedded highlighted image.

## Notes

- The original uploaded project is retained as `app.original.py` for reference.
- `app.py` is the new entry point; `assets/style.css` controls the appearance.
- File upload data and results are held in the local Streamlit session; they are not uploaded to a third-party service by this code.
- Visual difference analysis is not proof of image authenticity. Images must have matching dimensions.
- Never share your secret encryption key publicly.
