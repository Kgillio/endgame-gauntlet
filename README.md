# ♟️ Endgame Gauntlet

**A fast-paced chess endgame game built around calculation, technique, and premoves.**

Endgame Gauntlet turns winning chess positions into timed challenges. Rather than simply finding the right move, you have to convert the position against an engine, manage the clock, and think ahead. Queue premoves to play faster, take on progressively tougher opponents, and test your endgame skills in different game modes.

## Features

- **Timed endgame challenges** — Start from preloaded chess positions and play them out against an engine.
- **Chained premoves** — Queue moves ahead of your opponent's reply to save time, with support for canceling queued moves.
- **Adjustable time controls** — Set the time available for a round and the increment added after moves.
- **Progression and rating ladder** — Take on increasingly difficult engine opposition, build your premove rating, and unlock titles.
- **Multiple game modes** — Play a **10-Round** challenge, keep going in **Unlimited** mode, or try **Master Tournament**.
- **Master Tournament positions** — A separate collection of challenges based on Lichess puzzle positions.
- **Interactive board** — Drag pieces, see legal-move and last-move highlights, review games, and draw calculation arrows with right-click dragging.

## Game Modes

| Mode | Experience |
| --- | --- |
| **10-Round** | A focused run of endgame challenges. |
| **Unlimited** | Keep playing and pushing your performance over successive rounds. |
| **Master Tournament** | Take on positions drawn from a separate Lichess-based puzzle collection. |

## Built With

- **Python** — Application logic and position handling
- **Streamlit** — Web application interface and controls
- **python-chess** — Chess board representation and rules
- **HTML, CSS & JavaScript** — Custom chessboard interactions, premoves, and visual interface
- **Stockfish** — Browser-based engine opposition
- **JSON** — Endgame and tournament position datasets

## Run Locally

**Requirements:** Python and a modern web browser.

1. Clone the repository using `git clone https://github.com/Kgillio/endgame-gauntlet.git`.
2. Open the project directory using `cd endgame-gauntlet`.
3. Install dependencies using `pip install -r requirements.txt`.
4. Run the application using `streamlit run app.py`.
5. Open the local URL shown in the terminal, usually `http://localhost:8501`.

Some engine resources are loaded from online sources, so an internet connection may be required for engine play.

## Project Structure

- `app.py` — Streamlit application and custom board interface
- `positions.json` — Endgame challenge positions
- `master_tournament_positions.json` — Master Tournament position dataset
- `requirements.txt` — Python dependencies
- `.streamlit/` — Streamlit configuration
- `.devcontainer/` — Development environment configuration

## About the Project

Endgame Gauntlet combines chess practice with arcade-style pressure. It explores how real-time board interactions, engine play, premove queues, timed challenges, and progression systems can turn traditional endgame study into an interactive game.

The application is built primarily in Python with a customized browser interface for the chessboard and move interactions.

---

**Created by [@Kgillio](https://github.com/Kgillio)** · [View source on GitHub](https://github.com/Kgillio/endgame-gauntlet)
