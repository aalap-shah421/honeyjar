# HoneyJar

A lightweight honeypot you can drop on a $5 VPS. Listens on commonly-probed ports, captures attacker IPs and commands, and ships structured events to a webhook (Discord / Slack / SIEM).

> Status: early scaffold. The async listener and webhook shipping work. Banner emulation and dashboard are next.

## Quickstart (local)

```bash
git clone https://github.com/aalap-shah421/honeyjar.git
cd honeyjar
cp .env.example .env  # set your webhook URL
python honeyjar.py
```

## Quickstart (Docker)

```bash
docker compose up -d
```

## What it captures

For each connection on the listened ports (default: 22, 23, 80, 445):

- timestamp (UTC)
- source IP + ASN/geo (free `ipinfo.io` tier)
- destination port
- first 256 bytes received (decoded best-effort)
- session duration

Events are POSTed to the webhook URL set in `.env`. Discord-shaped JSON works for both Discord and Slack with minor field tweaks.

## Why

After tuning SIEM rules at Mindboard, I wanted to see what a noisy day on the open internet looks like firsthand. The cleanest detection signal is "stuff nobody should be touching" - so I built that exact thing.

## Roadmap

- [x] Async listeners on configurable ports
- [x] Webhook shipping (Discord/Slack-shaped)
- [x] Docker image + compose file
- [ ] Banner emulation (cowrie-lite)
- [ ] OpenSearch and Splunk HEC sinks
- [ ] Auto-block via UFW after N hits
- [ ] Top-attacker dashboard

## About

Built by [Aalap Shah](https://aalap-shah421.github.io) - cybersecurity engineering student at GMU, Security Professional at QTS Data Centers.
