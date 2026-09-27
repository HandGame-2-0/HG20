# HandGame 2.0

Modular educational app for learning selected PJM (Polish Sign Language) signs using hand gesture recognition.

## Requirements

- Python 3.11
- Poetry

## Repository setup

### GitHub

1. Create a new private repository on GitHub.
2. Clone it locally:
   ```bash
   git clone <REPO_URL>
   cd handgame-app
   ```
3. Copy the template files into the project directory.
4. Add the first commit:
   ```bash
   git add .
   git commit -m "chore: initialize project"
   git push origin main
   ```

### GitLab

1. Create a new private project in GitLab.
2. Clone it locally:
   ```bash
   git clone <REPO_URL>
   cd handgame-app
   ```
3. Copy the template files into the project directory.
4. Add the first commit:
   ```bash
   git add .
   git commit -m "chore: initialize project"
   git push -u origin main
   ```

## Installing dependencies

```bash
poetry install
```

## Enabling pre-commit

```bash
poetry run pre-commit install
```

## Running the app

```bash
poetry run python -m handgame.main
```

Alternatively:

```bash
poetry run handgame
```

## Camera and PJM letter recognition

By default the app uses the first webcam (OpenCV) and recognizes the static
PJM letters `A B C E I L M N O P R S T U V W Y` with MediaPipe hand landmarks
and the bundled classifier `models/pjm_static_letters.joblib` (MLP on
`hand_geometry` features: signed palm-plane volumes, method from
[MagMat03/handgesture](https://github.com/MagMat03/handgesture), plus all
pairwise landmark distances, from MediaPipe world landmarks).

On first run the app downloads the MediaPipe hand landmarker (~7.5 MB) to
`models/hand_landmarker.task` if that file is missing (not committed).

The recognized letter and its confidence are shown under the camera preview
during a game ("Rozpoznano: A (87%)").

Run without a webcam / models (mock camera + mock AI):

```powershell
$env:HANDGAME_CAMERA_BACKEND = "mock"; $env:HANDGAME_ALGORITHM = "MOCK_YOLO"
poetry run handgame
```

All `HANDGAME_*` settings (camera index, mirroring, model paths, stabilization)
are listed in `docs/gui_camera_ai_contract.md`, section "Backends, algorithms
and configuration".

## Suggested minimal directory structure

```text
handgame-app/
├── src/
│   └── handgame/
│       ├── __init__.py
│       └── main.py
├── tests/
├── assets/
├── config/
├── pyproject.toml
├── .pre-commit-config.yaml
├── .gitignore
└── README.md
```

## Minimal entry point

Create `src/handgame/main.py`:

```python
from PySide6.QtWidgets import QApplication, QLabel
import sys


def main() -> None:
    app = QApplication(sys.argv)
    label = QLabel("HandGame 2.0")
    label.resize(320, 120)
    label.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

## Tips

- Don't commit the `.venv/` environment.
- Don't push camera recordings, frame dumps, local SQLite databases, or large AI models to the repo.
- Make all changes through branches and a Merge Request / Pull Request.
- Keep source code in `src/`, tests in `tests/`, and app assets in `assets/`.
