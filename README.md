# Portfolio

This is my unified site for cybersecurity writeups and home lab documentation, built with Jekyll and the [Just the Docs](https://github.com/just-the-docs/just-the-docs) theme.

**Read it at [francisvillalon.github.io/portfolio](https://francisvillalon.github.io/portfolio/)**

## What's here

I combined three collections into one site:

- **[Cyberdefenders](cyberdefender-writeups/)**: blue team CTF writeups covering malware analysis, endpoint forensics, network forensics, reverse engineering, and threat hunting. All challenges are from [CyberDefenders](https://cyberdefenders.org/).
- **[MemLabs](memlabs-writeups/)**: memory forensics writeups for stuxnet999's [MemLabs](https://github.com/stuxnet999/MemLabs) CTF series, using Volatility 2.
- **[Cybersecurity Home Lab](cybersecurity-home-lab/)**: a virtualized enterprise network I built (WAN/DMZ/LAN segmentation, Wazuh, Suricata) with a deliberately vulnerable agentic AI app as an attack target, plus my attack and detection write-ups.

Each collection has its own README with more detail.

## Structure

```
portfolio/
├── cyberdefender-writeups/
├── memlabs-writeups/
├── cybersecurity-home-lab/
├── _config.yml
├── _includes/
└── docker-compose.yml
```

## Local preview

```
docker compose up
```

Then visit `http://localhost:4000/portfolio/`. `_config.yml` changes need a container restart (`docker restart portfolio-jekyll-1`), content and include changes hot-reload.
