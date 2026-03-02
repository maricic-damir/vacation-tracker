# GitHub setup for Vacation Tracker

This project is ready for GitHub. Run these commands in your terminal.

## 1. Finish initializing Git (if needed)

If `.git` already exists but is incomplete:

```bash
cd /Users/d.maricic/vacation_tracker
git init   # completes repo setup (may prompt for hooks – accept or skip)
```

## 2. First commit

```bash
cd /Users/d.maricic/vacation_tracker
git add .
git status   # confirm: README, config.py, database.py, ui/, etc.; no .db or __pycache__
git commit -m "Initial commit: Vacation Tracker desktop app"
```

## 3. Create the repo on GitHub

1. Open [github.com/new](https://github.com/new).
2. Set **Repository name** to `vacation_tracker` (or any name you like).
3. Choose **Public** (or Private).
4. Do **not** add a README, .gitignore, or license (they already exist locally).
5. Click **Create repository**.

## 4. Connect and push

GitHub will show commands like these. Use your actual repo URL:

```bash
git remote add origin https://github.com/YOUR_USERNAME/vacation_tracker.git
git branch -M main
git push -u origin main
```

If you use SSH:

```bash
git remote add origin git@github.com:YOUR_USERNAME/vacation_tracker.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

---

**Already in place**

- `.gitignore` – ignores `*.db`, `__pycache__/`, `.venv/`, `config.ini`, `.DS_Store`, etc.
