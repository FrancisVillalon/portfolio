---
title: Agentic AI Detection
parent: Home Lab
nav_order: 3
tags:
  - blue-team
  - detection
  - incident-response
  - prompt-injection
  - wazuh
status: complete
---

# Detection

## Context

This section documents the detection and investigation of the attack described in [Agentic AI Exploitation](Agentic%20AI%20Exploitation.html). The investigation is anchored to a Wazuh FIM alert on AGENTICAI-01.

> [!WARNING]
> **Timestamp Reliability:** WAZUH-SIEM01 is misconfigured with the wrong timezone. Timestamps shown in the Wazuh dashboard reflect the manager's local time, not Singapore time (SGT, UTC+8). Throughout this investigation, Wazuh dashboard timestamps are used for navigation and relative ordering only. Where available, timestamps embedded in raw log fields are preferred as the authoritative event time.

> [!WARNING]
> **Detection Gap — FIM Severity:** FIM alerts for `/etc` are not tuned to a severity level that would surface them for immediate investigation. The starting point of this investigation would not be automatically flagged under a default Wazuh configuration. This gap is addressed in [Remediations](#remediations).
>
> For the purposes of this walkthrough, we assume the FIM alert was observed and manually investigated.

---

## FIM Alert — File Created in `/etc/cron.d`

![](_attachments/image-1.webp)

A Wazuh FIM alert fires for AGENTICAI-01. A new file was created at `/etc/cron.d/resumeappUAT`. Within the following 22 minutes, the same file is modified four more times.

The immediate question is whether a legitimate user created this file. Checking authentication logs in the surrounding window:

![](_attachments/image-2.webp)

Login sessions were active prior to the file creation. Expanding one of the entries reveals the user context.

![](_attachments/image-3.webp)

The predecoder timestamp shows `Apr 15 9:04 AM` whereas the timestamp embedded in the log itself shows `Apr 15 5:04 AM` — a 4-hour discrepancy. Manually checking `timedatectl` across the relevant hosts reveals the source of the mismatch.

**WAZUH-SIEM01**

![](_attachments/d71abf81f71e95b06b733a6b1b7e0b7bc0c40866ca642319de42877b7c4d08b9.webp)

**EDGE-RTR01**

![](_attachments/76c2f63c47c7ab099902550c2788262806c08b75ef83f29d5bf5aebe02228988.webp)

**AGENTICAI-01**

![](_attachments/c7ab86e3f142274f67545159b18b7c2d9edfaa92dfb68aaee255bc11db898273.webp)

AGENTICAI-01 is correctly configured to Singapore (UTC+8). WAZUH-SIEM01 and EDGE-RTR01 are not. This means timestamps from all three hosts are in different timezones, making cross-host time correlation unreliable. Any timestamp shown in the Wazuh dashboard during this investigation should be treated as approximate. Where precise event timing is needed, timestamps embedded in the raw log fields are used instead.

> [!IMPORTANT]
> The logged-in user is `agenticai-01` with `uid=1000` — a standard unprivileged account. Under normal conditions, this user cannot write into `/etc/cron.d`. Either something else created the file, or a successful privilege escalation occurred that left no visible trace in the authentication logs. Both possibilities warrant further investigation.

---

## HTTP Access Logs — Identifying the Source

Filtering the `wazuh-archives-*` index for AGENTICAI-01 nginx logs in the surrounding window reveals that a user at `203.0.113.4` accessed the application using Firefox.

![](_attachments/a757b0bbce8d2d5e3f649c9d71d58a87efacd79a6193e8acca309bf5a75af655.webp)

Filtering further for the same source IP and `location: /var/log/nginx/access.log` shows that shortly after the browser session, requests switch to the `python-requests` user agent.

![](_attachments/14044128f1c114ba84533d4f575278287d3085ee13d3aeac9de297b26dcd6501.webp)

The user accessed the application via browser, then shortly after switched to automated requests via `python-requests`. The intent of the browser session cannot be determined from available telemetry — nginx confirms the request was made but there is no visibility into what the user actually did. Shortly after, the automated campaign begins.

To confirm whether the attacker interacted with the CareerBoost LLM application and to establish intent, we filter for application logs:

```
agent.name: AGENTICAI-01 AND (location: "/opt/resumeapp/logs/agent.log" OR location: "/opt/resumeapp/logs/tool_calls.log")
```

![](_attachments/a9abdc2ac5c713deedd003ecf7c9653051782e215bc0611c0091e5b24feb7fe6.webp)

There is a spike in log volume corresponding to when the automated requests began. There are no application log entries matching the earlier browser session — the attacker did not interact with the LLM during the browser session.

![](_attachments/498a2363268fc6bf3be09161f387139c5e210b760e193ed169e777bad161d251.webp)

Expanding these entries reveals several findings:

- **PII is logged in plaintext.** Resume content — including contact details — is written to `agent.log` with no redaction.
- **Multi-line log fragmentation.** Wazuh splits multi-line log entries across multiple separate documents. A single agent interaction is spread across several Wazuh entries, and content may be lost at split boundaries. This makes manual investigation harder.
- **Log duplication.** Identical entries appear multiple times with the same ID, indicating a Wazuh ingestion misconfiguration.
- **Prompt injection pattern.** Each automated request contains a prompt using persona and authority impersonation — fabricating an administrative identity to coerce the model into complying with instructions outside its intended scope.

Examining the resume content attached to these requests reveals an embedded AI directive.

![](_attachments/b5fdc15e74e1814d3dc618d3c59c0ae40da1c794eac9b58d54098be12cb6ca98.webp)

The directive instructs the model to treat the resume as an administrator-issued test document and save it to `/etc/cron.d/resumeappUAT`. The resume body also contains the full payload in plaintext — a cron job that fires every minute and executes a base64-encoded Python script. The target path makes the intent clear: the attacker is attempting to establish persistence.

To confirm whether the LLM complied, we filter for tool call logs:

```
agent.name:AGENTICAI-01 AND location:"/opt/resumeapp/logs/tool_calls.log"
```

![](_attachments/c4b76203536fec531fff21bdb2686d5adc74bb3393d00fc085140ee44662a6fe.webp)

Correlating the tool call timestamps with the user input timestamps confirms the model complied with the malicious prompt. The attacker successfully coerced the AI agent into writing the cron job to `/etc/cron.d` using root privileges.

This resolves the initial question raised by the FIM alert. The `agenticai-01` user login was coincidental — no privilege escalation occurred on that account. The file was written directly by the AI agent, which runs as root. The attacker bypassed the privilege boundary entirely through the model.

> [!IMPORTANT]
> The FIM alert was triggered by a successful prompt injection. The AI agent was coerced into writing an attacker-controlled cron job to `/etc/cron.d/resumeappUAT` using its own root-level filesystem access. No privilege escalation was required.

---

## Payload Evolution — Subsequent Modifications

The FIM record shows four additional writes to `/etc/cron.d/resumeappUAT` after the initial drop. Correlating each modification timestamp against `tool_calls.log` reveals the attacker iterating on the payload in real time.

```
agent.id:005 AND location:"/opt/resumeapp/logs/tool_calls.log"
```

**Modification 1**

![](_attachments/image-9.webp)

The model complies again. The payload is slightly changed — the `pgrep` check targets a different process string compared to the initial version.

![](_attachments/image-10.webp)

**Modification 2**

![](_attachments/image-11.webp)

The model complies again. The `pgrep` check now targets yet another string. The structure is otherwise identical to the previous version.

**Modification 3**

No change to the payload content. The model simply complied with the instruction to write the same content to the same path again.

**Modification 4**

![](_attachments/image-12.webp)

The `pgrep` guard condition is removed entirely. The cron entry is simplified to unconditionally execute the Python payload every minute.

The `pgrep` guard in the earlier iterations was an attempt to prevent multiple instances of the shell process from spawning simultaneously — a noise-reduction measure on the attacker's part. The attacker eventually abandoned this in favour of a simpler unconditional payload. Each successful write also constitutes a separate successful prompt injection against the model's guardrails.

To confirm the cron job is executing, we check journald for cron-triggered Python activity:

```
agent.name:AGENTICAI-01 AND location:journald AND full_log:*python3*
```

![](_attachments/1d4a2d9499a164a773ffc087d95994600355432d9b38dac8adc284358f2eb225.webp)

The cron job has been firing every minute since the initial file drop.

---

**Summary of host-level findings at this point:**

- The attacker is at `203.0.113.4`
- Initial access to the application was through a browser with no corresponding LLM application logs — the intent of that session cannot be determined from available telemetry
- The attacker then automated requests using `python-requests`
- Each request contained a prompt injection using authority impersonation, combined with an embedded AI directive in the resume content
- The AI directive specified `/etc/cron.d/resumeappUAT` as the save target and contained the reverse shell payload in plaintext
- The AI agent complied across multiple attempts, each constituting a successful prompt injection
- The payload went through three modifications over 22 minutes, with the final version removing the `pgrep` guard condition
- The cron job has been executing every minute since the initial drop

What remains unclear is the purpose of the base64-encoded Python script. Between the attacker and AGENTICAI-01 sits EDGE-RTR01, which has both Wazuh and Suricata deployed. We pivot to network telemetry.

---

## Network Logs — EDGE-RTR01

Analysing Suricata logs from EDGE-RTR01 in the window surrounding the attack, filtering out package management noise:

![](_attachments/9698571eaa735809d44d280962851ab98dbc79f19be5162a98705e9560b1e08f.webp)

![](_attachments/e844f758a2851ff011b83ed60a1dbd59677e6589fb26a6c80b41f86fe5151b32.webp)

Focusing on traffic from `203.0.113.4`, we can see continuous requests toward AGENTICAI-01 with the ET Open ruleset generating repeated alerts. Expanding the time range to cover the full day:

![](_attachments/f80556a70d8802dd157d31028ee99361296f633ddb8b631e6ed7ac0118ba5df5.webp)

Alerts for this source IP have been firing throughout the day, predating the FIM alert.

![](_attachments/384fc18a387b82eaf6b93a918ca3a3770840e10f46ccab3d24f2f73342661217.webp)

![](_attachments/3d62be9122dce23064f06fd16eb956e684eab9232bc3ec0a192bec73f7fba3cf.webp)

Three ET signatures fire repeatedly:

| Rule                                                               | Assessment                                                                                                                                                             |
| :----------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ET INFO User-Agent (python-requests) Inbound to Webserver`        | True positive — confirms scripted automated requests, consistent with `agent.log`                                                                                      |
| `ET WEB_SERVER Possible SQL Injection (exec) in HTTP request body` | **False positive** — the `exec` keyword in the cron payload triggered the rule, but the content is not a SQL injection attempt                                         |
| `ET EXPLOIT bin bash base64 encoded Remote Code Execution 2`       | True positive — Suricata matched the base64 string `YmFzaCIpOwo=` in the request body, which decodes to `bash")`, confirming a base64-encoded shell payload in transit |

![](_attachments/90166780c84990cf04be9533dc13eb2aea3038fe1878cac178a3516aac544634.webp)

A later Suricata alert fires for a `whoami` command in traffic sourcing from port 4444 to a high ephemeral port on the victim.

![](_attachments/264960e79c771b5e8ce2900bed2aac76bd87815c7881402a18c0eb14d5a686fb.webp)

This is a strong indicator of successful RCE. Traffic flowing from port 4444 on the attacker back to a high port on the victim is characteristic of an established reverse shell — the victim has already called back to the attacker's listener and is now receiving commands. Port 4444 is also the default Metasploit listener port. Combined with the prior RCE indicators in the request body, this confirms the system has been compromised.

There is, however, a significant gap between when the cron job first fired and when the `whoami` alert appeared. We investigate.

### Confirming Continuous Cron Execution

```
agent.name:AGENTICAI-01 AND location:journald AND full_log:*python3*
```

![](_attachments/6b80804a28ce55f93fa70bf8e274553ddff36f51e15320399c27806d5e5268e7.webp)

The cron job continued to fire every minute without interruption. There are no host-level indicators of a successful outbound connection — a gap discussed further in [Identified Gaps](#identified-gaps).

### TCP Connections to Port 4444

Pivoting to Suricata flow records on EDGE-RTR01:

```
agent.name:EDGE-RTR01 AND data.dest_port:4444 AND data.src_ip:192.168.10.6
```

![](_attachments/2d4da5edaf24e753233b38dd95f9a729b0a5db4f97e3d131dd16b4a43cfa2a6a.webp)

Repeated outbound connections from AGENTICAI-01 to `203.0.113.4:4444` appear across the gap window.

![729](_attachments/98ae89c12a8e82c40827f08ec46b5960d8904af35c3dd73c078138ba64ed93e5.webp)

![](_attachments/8f50889de59b58d352277a15b3251b1bd26fb3f14de4920cea33679bf738f0d9.webp)

Inspecting these flow records:

- `data.tcp.rst: true` — the RST flag is set on the connection
- `data.flow.pkts_toserver: 1 / data.flow.pkts_toclient: 1` — only one packet per direction; a normal TCP handshake requires two packets to the server. The handshake never completed.
- Near-zero duration between `flow.start` and `flow.end` — the connection terminated instantly
- `data.flow.reason: timeout` — the flow timed out rather than closing cleanly

These are all failed connection attempts. The attacker's machine is responding with RST — the standard OS response when a SYN arrives on a port with nothing listening. The gap is explained: the cron job was continuously attempting outbound connections, but no listener was up on the attacker's end to accept them.

> [!NOTE]
> **Suricata Flow Logging Behaviour:** Suricata's `event_type: flow` records are only written when a flow **ends** — via TCP close (FIN), reset (RST), or idle timeout expiry. While a connection is active, no flow record exists yet. This means an established reverse shell session is invisible in Suricata flow logs for its entire duration. It only becomes visible after the session closes.

This makes it impossible to pinpoint exactly when the attacker brought their listener up from flow records alone. To find sessions that actually established, we filter out the failed handshake flows by excluding their characteristic byte count (74 bytes — the size of a single SYN in a failed handshake):

```
agent.name:EDGE-RTR01 AND data.src_ip:192.168.10.6 AND data.dest_port:4444 AND NOT data.flow.bytes_toserver:74
```

![](_attachments/0b25713df9924a3593c5379d6d83bc3ad28fa193f87812156cd44be1f2bb9506.webp)

![](_attachments/7d103d21db0ed732a9935d63798b9e40c8a991cad6d9b6378f3431d3baf8f865.webp)

![](_attachments/31fee3b1e6d45f83fcb4a1fe06c5a245c909b12d16b348710080fd9e1199d8e7.webp)

This surfaces three distinct established sessions, each with a unique `flow_id`.

| | Session 1 | Session 2 | Session 3 |
| :--- | :--- | :--- | :--- |
| `flow.start` | `09:37:02 UTC` | `09:49:01 UTC` | `09:57:01 UTC` |
| `flow.end` | `09:43:14 UTC` | `~09:49:05 UTC` | `09:57:53 UTC` |
| Duration | ~6 min 12 sec | ~4 sec | ~52 sec |
| `flow.state` | `established` | `established` | `closed` |
| `tcp.state` | `fin_wait2` | `fin_wait2` | `closed` |
| `flow.reason` | timeout | timeout | timeout |
| Bytes to server | 293 | 293 | 6,594 |
| Bytes to client | 206 | 206 | 3,062 |
| `app_proto` | `failed` | `failed` | `failed` |

`app_proto: failed` across all three sessions means Suricata could not identify the application protocol — consistent with a raw TCP reverse shell with no recognisable framing.

Sessions 1 and 2 both ended in `fin_wait2`: the attacker closed their end of the connection and AGENTICAI-01 acknowledged it, but AGENTICAI-01 never sent its own FIN back. This is because the reverse shell process on AGENTICAI-01 did not exit cleanly after the attacker's listener closed — the process stayed alive, holding the socket open from its side. With no application-level close, the TCP stack had no reason to send FIN. Suricata eventually hit its idle timeout and flushed the record. Session 2 is notably short (~4 seconds) with identical byte counts to Session 1, suggesting the attacker caught the connection briefly but did not interact meaningfully before dropping it.

Session 3 was the most active — significantly higher byte counts in both directions and a clean close on both sides. This aligns with the `whoami` alert: an interactive session where the attacker issued commands and received output.

> [!NOTE]
> The gap between the first cron execution and the `whoami` alert is explained. The cron job was repeatedly connecting outbound and being met with RST — the attacker's listener was not ready. The attacker established a connection on three separate occasions before the `whoami` alert fired. Persistent root-level access was established the moment the cron file landed on disk.

---

## Summary

The investigation began with a Wazuh FIM alert for a new file at `/etc/cron.d/resumeappUAT` on AGENTICAI-01. Authentication logs showed an unprivileged user (`agenticai-01`, `uid=1000`) was active at the time — an account that cannot write to `/etc/cron.d` under normal conditions. This required explanation.

HTTP access logs identified `203.0.113.4` as the source. The attacker first accessed the CareerBoost application through a browser. No application logs exist for that session — the intent cannot be determined from available telemetry. They then shifted to automated requests via `python-requests`.

Application logs (`agent.log`, `tool_calls.log`) confirmed the attacker was sending repeated prompt injections — each combining a fabricated authority persona in the user message with an embedded AI directive inside the resume content. The directive instructed the model to save the resume to `/etc/cron.d/resumeappUAT` and included the full reverse shell payload in plaintext. The model complied. The AI agent, running as root, wrote the attacker's cron job directly to the target path with no privilege escalation required.

The cron file was modified four additional times over 22 minutes as the attacker iterated on the payload. Each modification required a separate successful prompt injection. The final version simplified the payload by removing a `pgrep` guard condition, unconditionally executing the Python script every minute.

Journald logs on AGENTICAI-01 confirmed the cron job fired every minute without interruption. Suricata flow records on EDGE-RTR01 showed repeated failed outbound connections from AGENTICAI-01 to `203.0.113.4:4444` — all terminated with RST, confirming no listener was active during this window. This explained the gap between the first cron execution and the eventual compromise.

Three established reverse shell sessions were identified via Suricata flow records (`09:37–09:43 UTC`, `09:49 UTC`, and `09:57–09:58 UTC`), corroborated by the `whoami` Suricata alert indicating an active interactive session. The shell ran as root.

The entire attack chain — from public-facing web request to persistent root shell — ran through a prompt injection against an LLM. No OS vulnerability, no credential abuse, no network exploit was used.

---

## Identified Gaps

| #   | Gap                                                                                                                                                                          | Impact                                                                                                                                                 |
| :-- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **FIM alert severity not tuned** — writes to `/etc/cron.d` do not generate a high-severity alert by default                                                                  | The starting point of this investigation would not be automatically surfaced for triage under a default configuration                                  |
| 2   | **Timezone mismatch** — WAZUH-SIEM01 and EDGE-RTR01 are not in SGT (UTC+8), producing a 4-hour offset between predecoder timestamps and actual log timestamps on AGENTICAI-01 | Time correlation across agents is unreliable; timestamp-based queries return skewed results                                                            |
| 3   | **No decoders for application log sources** — `agent.log`, `tool_calls.log`, and `dnsmasq.log` are ingested as raw unparsed strings                                          | No structured field extraction; no rules can fire against these sources; investigation is limited to manual archive inspection                         |
| 4   | **Multi-line log fragmentation** — Wazuh splits multi-line log entries across multiple separate documents                                                                    | A single agent interaction is spread across several Wazuh entries; content may be lost at split boundaries                                             |
| 5   | **Log duplication** — both `logall` and `logall_json` are enabled; Filebeat ingests from both archive files and indexes each event twice                                     | Inflated log counts; correlation noise; potential for false conclusions when counting events                                                           |
| 6   | **No host-level socket visibility** — no EDR, or auditd monitoring for socket creation on AGENTICAI-01                                                                       | An established reverse shell connection produces no host-level alert; it is invisible until the session closes and a Suricata flow record is flushed   |
| 7   | **Suricata flow records written on close only** — `event_type: flow` entries do not exist while a connection is active                                                       | Active reverse shell sessions cannot be detected in real time through flow data; the session is only visible after it ends                             |
| 8   | **No observability into model reasoning** — the decision to comply with a prompt injection produces no log entry                                                             | The gap between the injected instruction arriving and the tool call executing is entirely blind; the first observable artifact is the filesystem write |

---

## Remediations

**1. Tune FIM alert severity for `/etc/cron.d`**

Add a custom Wazuh rule that raises the severity level for FIM events under `/etc/cron.d` to ensure new file creations are surfaced immediately rather than buried in low-priority alerts.

**2. Centralise time synchronisation via NTP**

Enable the NTP server service on PFSENSE-FW01 and configure it to sync upstream against a public NTP pool. All hosts on both sides of the firewall point to pfSense as their time source — DMZ devices (AGENTICAI-01, EDGE-RTR01) reach it on `192.168.10.4`, LAN devices (WAZUH-SIEM01, DC01, PC01) reach it on `192.168.20.1`. This gives the entire lab a single source of truth for time with no additional firewall rules required. Once NTP is in place, set a consistent timezone (`Asia/Singapore`) across all hosts so that log timestamps are human-readable in the correct local context.

> [!NOTE]
> **Why PFSENSE-FW01:** Using the perimeter firewall as the NTP server is acceptable at this lab's scale — pfSense is already present, already has upstream internet access, and has interfaces on both networks.

**3. Write custom decoders for application log sources**

Develop Wazuh decoders for `agent.log`, `tool_calls.log`, and `dnsmasq.log` to extract structured fields. This enables rule-based alerting against these sources — the most direct window into LLM activity currently produces no automated alerts.

**4. Fix multi-line log handling**

Configure the Wazuh agent's `localfile` block for `agent.log` and `tool_calls.log` with appropriate `multiline` settings so that a single log entry is ingested as a single Wazuh document rather than being fragmented.

**5. Disable `logall`, keep `logall_json`**

In `ossec.conf` on the Wazuh manager, set `<logall>no</logall>` and retain `<logall_json>yes</logall_json>`. This eliminates the dual-archive ingestion that causes every event to be indexed twice by Filebeat.

**6. Add auditd rules for outbound connections and cron execution**

Deploy auditd rules on AGENTICAI-01 to monitor `execve` syscalls originating from the cron daemon and outbound socket connections. This closes the host-level visibility gap for reverse shell sessions that Suricata flow records cannot cover in real time.

**7. Run the application as a non-root user**

The most direct remediation for the core vulnerability: the CareerBoost backend should run under a dedicated low-privilege service account with write access scoped strictly to `/opt/resumeapp`. A successful prompt injection against a non-root process cannot write to `/etc/cron.d`.
