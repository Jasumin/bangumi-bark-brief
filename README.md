# bangumi-bark-brief

Daily Bangumi watching-list brief pushed to iPhone with Bark.

This repository uses GitHub Actions to read a Bangumi user's current watching anime list, combine collection progress with official episode airing data, generate a concise Chinese brief, and send it to iPhone through Bark. It also hosts the custom notification icon used by Bark.

## Features

- Generates a daily Bangumi watching-list brief
- Uses the official Bangumi API to read watching collections and `ep_status`
- Uses the `v0/episodes` API to read episode counts, air dates, and next episode dates
- Puts already-aired but unwatched episodes in the priority section
- Sends the brief to iPhone through Bark
- Uses the custom Bark notification icon `icon.jpg`
- Supports manual runs from the GitHub Actions page

## Schedule

GitHub Actions schedules are configured in UTC:

```yaml
cron: "0 4 * * *"
```

This runs every day at `12:00` Asia/Shanghai.

## Required Secrets

In the repository, go to:

`Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`

Add these three repository secrets:

```text
BANGUMI_USER
```

Your Bangumi username, for example `jasumin`.

```text
BANGUMI_TOKEN
```

Your Bangumi API token.

```text
BARK_DEVICE_KEY
```

The device key from your Bark URL, which is the part after `https://api.day.app/`.

Do not put the Bangumi token or Bark key in code, README files, issues, or Actions logs.

## Manual Run

Open the repository `Actions` page:

1. Select `Bangumi brief`
2. Click `Run workflow`
3. Select `main`
4. Click `Run workflow` again

After a successful run, Bark should receive a notification with a title like:

```text
Bangumi 在看简报｜YYYY-MM-DD
```

## File Layout

```text
.github/workflows/bangumi-brief.yml  # GitHub Actions workflow
scripts/bangumi_brief.py             # Bangumi reader and Bark push script
icon.jpg                             # Custom Bark notification icon
```

## Icon

Current Bark icon URL:

```text
https://raw.githubusercontent.com/Jasumin/bangumi-bark-brief/main/icon.jpg
```

To replace the icon, replace `icon.jpg` in the repository root. A square JPG or PNG under `500 KB` is recommended.

## Local Test

To test locally, set the environment variables and run the script:

```powershell
$env:BANGUMI_TOKEN="your_bangumi_token"
$env:BANGUMI_USER="your_bangumi_username"
$env:BARK_DEVICE_KEY="your_bark_device_key"
python scripts\bangumi_brief.py
```

The script does not print secrets, but it sends the generated brief to Bark.
