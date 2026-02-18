# Repository Setup – Single Source of Truth

## The Single Repo

| Location | Purpose |
|----------|---------|
| **Local folder** | `C:\Users\ppandya\Git_DB_Cursor\desktop-tutorial-1` | Where you edit code and docs |
| **GitHub** | https://github.com/hcg-demo/hcg-demo | Remote copy (backup, share, CI) |

**They are the same repo.** The local folder is your working copy; GitHub is the remote.

---

## Flow

```
You edit files in:  C:\Users\ppandya\Git_DB_Cursor\desktop-tutorial-1
                            ↓
                    git add → git commit
                            ↓
                    git push origin main
                            ↓
            Code appears at: github.com/hcg-demo/hcg-demo
```

---

## Quick Commands (from project root)

```powershell
cd C:\Users\ppandya\Git_DB_Cursor\desktop-tutorial-1

# Push your changes to GitHub
git add .
git commit -m "Your message"
git push origin main

# Pull latest from GitHub
git pull origin main
```

---

## What’s in this repo

- **Slack + ServiceNow** integration (webhook, supervisor, ticket creation)
- **Multi-tenant** docs from Amazon Q (Aurora, Lambda, SAM)
- **Sample data** for KB ingestion
- **Scripts** for deploy, infra, tests
- **Docs**: architecture, lessons learned, do’s and don’ts

---

## Account

- **GitHub org/repo**: hcg-demo/hcg-demo  
- **Your email**: ppandya@hcg.com  
- **Auth**: GitHub CLI (`gh auth status`)
