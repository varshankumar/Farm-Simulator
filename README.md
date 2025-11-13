# 🌾 Farm Simulator

A farming simulation game built with Python and Pygame.

## 🚀 Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd Farm-Simulator
```

2. **Create a virtual environment** (recommended)
```bash
python -m venv .venv
```

3. **Activate the virtual environment**

Windows (PowerShell):
```powershell
.\.venv\Scripts\Activate.ps1
```

Windows (CMD):
```cmd
.venv\Scripts\activate.bat
```

macOS/Linux:
```bash
source .venv/bin/activate
```

4. **Install dependencies**
```bash
pip install -r requirements.txt
```

## 🎮 Running the Game

```bash
python main.py
```

## 🎯 Controls

- **Left Click**: Plant a seed on empty plot
- **Right Click**: Water a crop
- **H** (while hovering): Harvest mature crop
- **N**: Advance to next day
- **S**: Open seed shop
- **Tab**: Change selected crop type
- **F5**: Quick save
- **R**: Trigger rain event

## 📁 Project Structure

```
Farm Simulator/
├── main.py                 # Main game loop
├── models.py               # Data models
├── game_logic.py           # Game logic
├── logic_system.py         # Unlock system
├── concurrency_system.py   # Async systems
├── renderer.py             # Pygame rendering
├── save_system.py          # Save/load functionality
└── requirements.txt        # Dependencies
```

## 🐛 Troubleshooting

### Pygame installation issues on Windows
If you encounter errors installing pygame, try:
```bash
pip install pygame-ce
```

### Virtual environment not activating
Make sure you're using the correct activation script for your shell (see Setup step 3).

## 📝 License

Educational project.
