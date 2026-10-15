#!/usr/bin/env python3
"""Generate neon stats SVGs from the GitHub GraphQL API. Stdlib only, no third-party service."""
import json, os, sys, urllib.request, datetime as dt
from html import escape

USER = os.environ.get("GH_USER", "cipher0x9")
TOKEN = os.environ["GITHUB_TOKEN"]
OUT = sys.argv[1] if len(sys.argv) > 1 else "dist"
os.makedirs(OUT, exist_ok=True)

Q = """query($u:String!){user(login:$u){followers{totalCount} name
 contributionsCollection{totalCommitContributions totalPullRequestContributions totalIssueContributions totalPullRequestReviewContributions
  contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}
 repositories(first:100,ownerAffiliations:OWNER,isFork:false,privacy:PUBLIC){totalCount nodes{stargazerCount
  languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name color}}}}}}}"""
req = urllib.request.Request("https://api.github.com/graphql",
    data=json.dumps({"query": Q, "variables": {"u": USER}}).encode(),
    headers={"Authorization": f"bearer {TOKEN}", "User-Agent": "profile-stats"})
d = json.load(urllib.request.urlopen(req))
if "errors" in d: sys.exit(str(d["errors"]))
u = d["data"]["user"]; cc = u["contributionsCollection"]
days = [x for w in cc["contributionCalendar"]["weeks"] for x in w["contributionDays"]]
today = dt.date.today().isoformat()
days = [x for x in days if x["date"] <= today]

# streaks
longest = run = 0
for x in days:
    run = run + 1 if x["contributionCount"] else 0
    longest = max(longest, run)
cur = 0
for x in reversed(days):
    if x["contributionCount"]: cur += 1
    elif x["date"] == today: continue
    else: break
stars = sum(r["stargazerCount"] for r in u["repositories"]["nodes"])
langs = {}
for r in u["repositories"]["nodes"]:
    for e in r["languages"]["edges"]:
        n = e["node"]; langs.setdefault(n["name"], [0, n["color"] or "#00f0ff"])[0] += e["size"]
top = sorted(langs.items(), key=lambda kv: -kv[1][0])[:6]
tot = sum(v[0] for _, v in top) or 1

C, P, Y, BG, FG = "#00f0ff", "#ff2bd6", "#ffd400", "#0a0420", "#e8e6ff"
FONT = "font-family='Segoe UI,Helvetica,Arial,sans-serif'"
def wrap(w, h, title, body, desc):
    return (f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}' role='img' aria-label='{escape(desc)}'>"
     f"<title>{escape(desc)}</title><defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='{C}'/><stop offset='1' stop-color='{P}'/></linearGradient>"
     f"<filter id='glow'><feGaussianBlur stdDeviation='2' result='b'/><feMerge><feMergeNode in='b'/><feMergeNode in='SourceGraphic'/></feMerge></filter></defs>"
     f"<rect x='1' y='1' width='{w-2}' height='{h-2}' rx='14' fill='{BG}' stroke='url(#g)' stroke-width='2'/>"
     f"<text x='24' y='36' {FONT} font-size='18' font-weight='700' fill='{C}' filter='url(#glow)'>{escape(title)}</text>{body}</svg>")
def w(name, s): open(os.path.join(OUT, name), "w").write(s)

# stats card
rows = [("Commits (12 mo)", cc["totalCommitContributions"], C), ("Pull requests", cc["totalPullRequestContributions"], P),
        ("Issues", cc["totalIssueContributions"], Y), ("Reviews", cc["totalPullRequestReviewContributions"], C),
        ("Public repos", u["repositories"]["totalCount"], P), ("Stars earned", stars, Y), ("Followers", u["followers"]["totalCount"], C)]
b = "".join(f"<text x='24' y='{68+i*26}' {FONT} font-size='14' fill='{FG}'>{escape(k)}</text>"
            f"<text x='296' y='{68+i*26}' {FONT} font-size='14' font-weight='700' fill='{c}' text-anchor='end'>{v:,}</text>" for i, (k, v, c) in enumerate(rows))
w("stats.svg", wrap(320, 262, f"{USER} · GitHub Stats", b, f"GitHub stats for {USER}"))

# langs
b = ""
for i, (n, (sz, col)) in enumerate(top):
    y = 64 + i * 32; pct = sz / tot * 100
    b += (f"<text x='24' y='{y}' {FONT} font-size='13' fill='{FG}'>{escape(n)}</text><text x='376' y='{y}' {FONT} font-size='13' fill='{C}' text-anchor='end'>{pct:.1f}%</text>"
          f"<rect x='24' y='{y+7}' width='352' height='8' rx='4' fill='#1a1040'/><rect x='24' y='{y+7}' width='{max(4,352*pct/100):.0f}' height='8' rx='4' fill='{col}'/>")
w("top-langs.svg", wrap(400, 262, "Top Languages", b, "Top languages by bytes across public repos"))

# streak
def big(x, val, lab, col):
    return (f"<text x='{x}' y='110' {FONT} font-size='44' font-weight='800' fill='{col}' text-anchor='middle' filter='url(#glow)'>{val}</text>"
            f"<text x='{x}' y='142' {FONT} font-size='13' fill='{FG}' text-anchor='middle'>{lab}</text>")
b = big(110, f"{cc['contributionCalendar']['totalContributions']:,}", "Contributions · 12 mo", C) + big(400, cur, "Current streak (days)", Y) + big(690, longest, "Longest streak in window", P)
w("streak.svg", wrap(800, 180, "Contribution Streak", b, f"Current streak {cur} days, longest {longest} days"))

# activity graph (last 30 days)
last = days[-30:]; mx = max([x["contributionCount"] for x in last] + [1])
W, H, L, T, B = 900, 280, 50, 56, 44
cw, ch = W - L - 30, H - T - B
pts = [(L + i * cw / (len(last) - 1), T + ch - x["contributionCount"] / mx * ch) for i, x in enumerate(last)]
path = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(pts))
area = path + f" L{pts[-1][0]:.1f},{T+ch} L{pts[0][0]:.1f},{T+ch} Z"
b = f"<defs><linearGradient id='a' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='{P}' stop-opacity='.35'/><stop offset='1' stop-color='{P}' stop-opacity='0'/></linearGradient></defs>"
for k in range(5):
    gy = T + ch * k / 4; b += f"<line x1='{L}' x2='{W-30}' y1='{gy:.0f}' y2='{gy:.0f}' stroke='#2a1a5e' stroke-width='1'/><text x='{L-8}' y='{gy+4:.0f}' {FONT} font-size='11' fill='{FG}' text-anchor='end'>{round(mx*(1-k/4))}</text>"
b += f"<path d='{area}' fill='url(#a)'/><path d='{path}' fill='none' stroke='{C}' stroke-width='2.5' filter='url(#glow)'/>"
b += "".join(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='3' fill='{Y}'/>" for x, y in pts)
for i in (0, 7, 14, 21, 29):
    b += f"<text x='{pts[i][0]:.0f}' y='{H-16}' {FONT} font-size='11' fill='{FG}' text-anchor='middle'>{last[i]['date'][5:]}</text>"
w("activity.svg", wrap(W, H, "Contribution Activity · last 30 days", b, "Daily contributions over the last 30 days"))
print("ok", cur, longest)
