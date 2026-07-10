# MemLabs Writeups

Writeups for [stuxnet99's MemLabs](https://github.com/stuxnet999/MemLabs) — a series of CTF-style memory forensics challenges. I'm working through these to build a practical understanding of memory forensics techniques and tooling.

## Why MemLabs

Memory forensics is one of those areas where reading about it only gets you so far. MemLabs provides hands-on scenarios with real memory dumps, which forces you to actually work through the analysis process rather than just follow theory. The CTF format also makes it easier to know when you're on the right track and I personally find it fun.

## Tools Used

- **Volatility 2** (`vol2`) — primary analysis framework.
- **GIMP** — reconstructing raw pixel data from process memory dumps
- **Standard Unix utilities** — `xxd`, `base64`, `grep`, etc.

## Labs

| Lab | Title | Status | Flags |
|-----|-------|--------|-------|
| [Lab 1](./lab1/lab1-memlabs.md) | Beginner's Luck | Complete | 3 / 3 |
| [Lab 2](./lab2/lab2-memlabs.md) | A New World | Complete | 3 / 3 |
| [Lab 3](./lab3/lab3-memlabs.md) | The Evil Twin | Complete | 1 / 1 |
| [Lab 4](./lab4/lab4-memlabs.md) | Obsession | Complete | 1 / 1 |
| [Lab 5](./lab5/lab5-memlabs.md) | Black Tuesday | Complete | 3 / 3 |
| [Lab 6](./lab6/lab6-memlabs.md) | The Reckoning | Complete | 1 / 1 |

## Structure

Each lab lives in its own directory containing a writeup markdown file and an `images/` folder with screenshots taken during analysis.

