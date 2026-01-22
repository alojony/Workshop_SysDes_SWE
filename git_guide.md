Minimal Git Workflow (Workshop Guide)

This project uses Git for collaboration, not for ceremony.
We are not mastering Git. We are preventing chaos.

⸻

Ground Rules
	•	No one works on main directly
	•	Everyone works on their own branch
	•	Small commits, clear messages
	•	If something breaks, we fix it together

⸻

0. Prerequisites
	•	Git installed
	•	Repository cloned locally
	•	You have access to the remote repo

⸻

1. Add the remote (once)

If you cloned correctly, this may already exist.
If not:

git remote add origin <REPO_URL>

Verify:

git remote -v

You should see origin listed.

⸻

2. Create your own branch (mandatory)

** Never work on main. **
Create a branch using your name or something clearly identifiable.

git checkout -b <your-name>

Examples:

git checkout -b chevo
git checkout -b ruben
git checkout -b jon

This branch is your sandbox. Break things here, not on main.

⸻

3. Work and commit (often)

After making changes:

git status
git add .
git commit -m "describe what you actually changed"

Commit message rules

Bad:

stuff

Acceptable:

add inspection table schema
fix csv parsing for maintenance logs

If future-you can’t understand the message, redo it.

⸻

4. Push your branch upstream

First push only:

git push -u origin <your-name>

After that:

git push


⸻

5. Sync with main (before each session)

Before starting new work, pull the latest changes from main:

git checkout main
git pull origin main
git checkout your-name
git merge main

If there are conflicts:
	•	Read them
	•	Fix them
	•	Commit the fix

Conflicts are normal. Panic is not.

⸻

6. Getting changes into main
	•	You do not push directly to main
	•	Open a Pull Request from your-name → main
	•	We review and merge together during sessions

This keeps main usable for everyone.

⸻

Mental Model (important)
	•	main = shared truth
	•	your branch = safe sandbox
	•	Git = time machine + seatbelt

If Git feels annoying, that means it’s doing its job.

⸻

Final Rule

If you accidentally break main, you buy the next round of beer.

This rule has a 100% compliance rate.
