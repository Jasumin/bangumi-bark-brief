import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


BGMI_USER = os.getenv("BANGUMI_USER")
BGMI_TOKEN = os.getenv("BANGUMI_TOKEN")
BARK_DEVICE_KEY = os.getenv("BARK_DEVICE_KEY")
BARK_ICON_URL = os.getenv(
    "BARK_ICON_URL",
    "https://raw.githubusercontent.com/Jasumin/bangumi-bark-brief/main/icon.jpg",
)
BARK_SOUND = os.getenv("BARK_SOUND", "shake")
LOCAL_TIMEZONE = os.getenv("LOCAL_TIMEZONE", "Asia/Shanghai")
STATE_FILE = Path(os.getenv("STATE_FILE", ".state/last_success_date.txt"))


class BriefError(Exception):
    pass


def require_env(name, value):
    if not value:
        raise BriefError(f"Missing required environment variable: {name}")


def request_json(url, headers=None, data=None, method=None):
    body = None
    request_headers = headers or {}
    if data is not None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        request_headers = {
            **request_headers,
            "Content-Type": "application/json; charset=utf-8",
        }
    req = urllib.request.Request(
        url,
        data=body,
        headers=request_headers,
        method=method or ("POST" if data is not None else "GET"),
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise BriefError(f"HTTP {exc.code} from {url}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise BriefError(f"Network error from {url}: {exc.reason}") from exc


def bgm_headers():
    return {
        "Authorization": f"Bearer {BGMI_TOKEN}",
        "User-Agent": "CodexBangumiBrief/1.0",
        "Accept": "application/json",
    }


def get_collection():
    all_items = []
    limit = 100
    offset = 0
    while True:
        query = urllib.parse.urlencode(
            {"subject_type": 2, "type": 3, "limit": limit, "offset": offset}
        )
        url = f"https://api.bgm.tv/v0/users/{BGMI_USER}/collections?{query}"
        page = request_json(url, headers=bgm_headers())
        data = page.get("data", [])
        all_items.extend(data)
        total = int(page.get("total", len(all_items)))
        if offset + limit >= total:
            return all_items
        offset += limit
        time.sleep(0.15)


def get_episodes(subject_id):
    all_eps = []
    limit = 100
    offset = 0
    while True:
        query = urllib.parse.urlencode(
            {"subject_id": subject_id, "limit": limit, "offset": offset}
        )
        url = f"https://api.bgm.tv/v0/episodes?{query}"
        page = request_json(url, headers=bgm_headers())
        data = page.get("data", [])
        all_eps.extend(data)
        total = int(page.get("total", len(all_eps)))
        if offset + limit >= total:
            return all_eps
        offset += limit
        time.sleep(0.12)


def parse_day(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def title_for(item):
    subject = item.get("subject") or {}
    return subject.get("name_cn") or subject.get("name") or str(item.get("subject_id"))


def build_rows(items, today):
    rows = []
    for item in items:
        subject_id = item.get("subject_id")
        ep_status = int(item.get("ep_status") or 0)
        episodes = get_episodes(subject_id)
        main_eps = [ep for ep in episodes if int(ep.get("type") or 0) == 0]
        fallback = False
        if not main_eps and episodes:
            main_eps = episodes
            fallback = True

        dated_eps = [(ep, parse_day(ep.get("airdate"))) for ep in main_eps]
        aired = [(ep, day) for ep, day in dated_eps if day and day <= today]
        future = sorted([day for _, day in dated_eps if day and day > today])
        last_aired = max((day for _, day in aired), default=None)
        aired_count = len(aired)
        total = len(main_eps)
        rows.append(
            {
                "title": title_for(item),
                "ep_status": ep_status,
                "aired": aired_count,
                "total": total,
                "due": max(0, aired_count - ep_status),
                "next": future[0].isoformat() if future else None,
                "last_aired": last_aired.isoformat() if last_aired else None,
                "fallback": fallback,
            }
        )
        time.sleep(0.15)
    return rows


def build_brief(rows, today):
    priority = sorted(
        [row for row in rows if row["due"] > 0],
        key=lambda row: (row["due"], row.get("last_aired") or ""),
        reverse=True,
    )
    no_update = sorted([row for row in rows if row["due"] <= 0], key=lambda row: row["title"])

    lines = [f"Bangumi 在看简报｜{today.isoformat()}", "", "优先看"]
    if not priority:
        lines.append("今天没有发现新集更新。")
    else:
        for row in priority[:8]:
            start = row["ep_status"] + 1
            end = row["aired"]
            total = row["total"] if row["total"] else "未知"
            next_text = f"，下一话 {row['next']}" if row["next"] else ""
            lines.append(
                f"优先看｜{row['title']}：看到第 {row['ep_status']} 话 / "
                f"已放送到第 {end} 话，建议补第 {start}-{end} 话（总 {total}）{next_text}"
            )

    lines.extend(["", "当前在看与进度概览"])
    overview = sorted(rows, key=lambda row: (-row["due"], row["title"]))
    for row in overview:
        total = row["total"] if row["total"] else "未知"
        if row["next"]:
            status = f"下一话 {row['next']}"
        elif row["total"] and row["aired"] >= row["total"]:
            status = "已放送完或暂无下一话"
        else:
            status = "下一话未知"
        lines.append(f"{row['title']}｜看到 {row['ep_status']}/{total} 话｜{status}")

    lines.extend(["", "暂无新更新"])
    if no_update:
        for row in no_update[:12]:
            lines.append(f"- {row['title']}")
    else:
        lines.append("无。")

    if any(row["fallback"] for row in rows):
        lines.extend(["", "注：部分条目未找到正片 type=0，已谨慎退回全部章节数据。"])
    return "\n".join(lines), len(priority)


def push_bark(title, body):
    payload = {
        "device_key": BARK_DEVICE_KEY,
        "title": title,
        "body": body,
        "group": "Bangumi",
        "level": "active",
        "icon": BARK_ICON_URL,
        "sound": BARK_SOUND,
    }
    result = request_json("https://api.day.app/push", data=payload)
    if result.get("code") != 200:
        raise BriefError(f"Bark push failed: {result}")
    return result


def today_local():
    return datetime.now(ZoneInfo(LOCAL_TIMEZONE)).date()


def already_sent(today):
    if not STATE_FILE.exists():
        return False
    return STATE_FILE.read_text(encoding="utf-8").strip() == today.isoformat()


def mark_sent(today):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(today.isoformat() + "\n", encoding="utf-8")


def main():
    require_env("BANGUMI_USER", BGMI_USER)
    require_env("BANGUMI_TOKEN", BGMI_TOKEN)
    require_env("BARK_DEVICE_KEY", BARK_DEVICE_KEY)
    today = today_local()
    if already_sent(today):
        print(
            json.dumps(
                {"skipped": True, "reason": "already_sent_today", "date": today.isoformat()},
                ensure_ascii=False,
            )
        )
        return

    try:
        items = get_collection()
        rows = build_rows(items, today)
        body, priority_count = build_brief(rows, today)
        title = f"Bangumi 在看简报｜{today.isoformat()}"
    except BriefError as exc:
        body = (
            f"Bangumi 在看简报｜{today.isoformat()}\n\n"
            f"生成失败：{exc}\n\n"
            "请检查 Bangumi User、Bangumi Token、GitHub Actions 网络、Bangumi API 状态或 Bark 配置。"
        )
        title = f"Bangumi 在看简报失败｜{today.isoformat()}"
        priority_count = 0

    result = push_bark(title, body)
    mark_sent(today)
    print(
        json.dumps(
            {
                "bark_code": result.get("code"),
                "bark_message": result.get("message"),
                "priority_count": priority_count,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except BriefError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
