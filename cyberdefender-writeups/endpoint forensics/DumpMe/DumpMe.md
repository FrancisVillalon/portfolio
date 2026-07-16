---
title: DumpMe
parent: Endpoint Forensics
grand_parent: Cyberdefenders
nav_order: 5
difficulty: Medium
date: 2026-05-30
---

#endpoint-forensics #volatility2 #powershell #shimcache #strings #cyberdefender-medium #reviewed #finished 
# Scenario
A SOC analyst took a memory dump from a machine infected with a meterpreter malware. As a Digital Forensicator, your job is to analyze the dump, extract the available indicators of compromise (IOCs) and answer the provided questions.

# Questions

##  What is the SHA1 hash of Triage-Memory.mem (memory dump)?

We use `Get-FileHash` in PowerShell on Windows to get the hash of the memory dump.
Similarly, on Linux we can use `sha1sum`.

![](images/image-172.webp)

## What volatility profile is the most appropriate for this machine? (ex: Win10x86_14393)

In volatility2, we need a profile otherwise it will not be able to properly map memory locations.
We get suggested profiles using `imageinfo`.

![](images/image-173.webp)

## What was the process ID of notepad.exe?

We use the vol2 plugin `pslist` to list all the processes at the time of image capture and do a `sls`, the cmdlet for `select-strings`, for `notepad`.
This gets us the PID of notepad which is `3032`.

![](images/image-174.webp)

## Name the child process of wscript.exe.

For this we use the plugin `pstree` which shows the parent processes and their subsequent child processes.
We then do a `sls` for `wscript` with a context window of `0,10` which means include 10 lines after the match and 0 lines before the match.

![](images/image-175.webp)

## What was the IP address of the machine at the time the RAM dump was created?

For this we use `netscan` which shows the network connections established at the time the RAM dump was created.
We can see the local IPv4 address is `10.0.0.101`.

![](images/image-176.webp)

## Based on the answer regarding the infected PID, can you determine the IP of the attacker?

We know the infected PID is `3496` so we can find the IP of the attacker by checking if that process has established any network connections.
We can see this in the `netscan` output where PID `3496` has an established connection to `10.0.0.106`.

![](images/image-177.webp)

## How many processes are associated with VCRUNTIME140.dll?

For this we use the `dlllist` plugin and `sls` for `vcruntime140`.
This shows us how many processes are handling `VCRUNTIME140.dll`.

![](images/image-178.webp)

Note: 
The command is actually correct but only returns 1 process in my case.
I checked the sha1sum in question 1 and it matches so the memory dump is not corrupted.
I am not sure why my output differs from the actual answer but the command used here is correct.

## After dumping the infected process, what is its md5 hash?

We first dump the process with PID `3496` using `procdump`.

![](images/image-179.webp)

![](images/image-180.webp)

We then use `Get-FileHash` to get the MD5 hash of the malicious process.

![](images/image-181.webp)

## What is the LM hash of Bob's account?

This is trivially solved using the `hashdump` plugin, where the LM hash of Bob's account is the first hash (left to right) in his entry.

![](images/image-182.webp)

## What memory protection constants does the VAD node at 0xfffffa800577ba10 have?

We use the `vadinfo` plugin for this and `sls` the memory location in the question to find the one we want.

![](images/image-183.webp)

## What memory protection did the VAD starting at 0x00000000033c0000 and ending at 0x00000000033dffff have?

Similarly, we use `vadinfo` again but this time `sls` has two positive lookaheads. This causes the command to return matches that contain both values simultaneously.

![](images/image-184.webp)

##  There was a VBS script that ran on the machine. What is the name of the script? (submit without file extension)

We use `cmdline` here because it scans how programs were invoked and what arguments were passed to them.
If a VBS script ran, it means wscript must have been invoked with the file as the argument.
Therefore, we can see the name of the script by looking through `cmdline`.

![](images/image-185.webp)

##  An application was run at 2019-03-07 23:06:58 UTC. What is the name of the program? (Include extension)

`shimcache` is a plugin that allows us to track which executable files have been run or were present on the system.
It works by extracting the `Application Compatibility Cache` from a Windows memory image.
We can then `sls` for that timestamp to find what program was last modified at that time.

![](images/image-186.webp)

## What was written in notepad.exe at the time when the memory dump was captured?

To figure this out we can dump the entire addressable memory of the notepad process using `memdump`.

![](images/image-187.webp)

We can then rename the dump to notepad_memdump then perform strings on it.
We will send the strings output into a text file so it is easier to analyse.
It should also be noted that `-u` is passed to `strings` because Windows uses little endian.

![](images/image-188.webp)


We can create a regex pattern based on the CyberDefenders censored placeholder.

![](images/image-190.webp)


![](images/image-189.webp)

Though this is a pretty cheesy way of doing it, a more proper way is just to grep for some key terms like `flag` or a regex pattern like `.+\<.+>`.
Also a small note, we do not need to actually escape `<` or `>` here.
## What is the short name of the file at file record 59045?

To get the short name of a file we need to check the `MFT` which is the master file table.
To see the `MFT` we need to use `mftparser`.
Then we just `sls` for file record `59045`.

![](images/image-192.webp)

![](images/image-193.webp)

## This box was exploited and is running meterpreter. What was the infected PID?

Meterpreter is a payload in Metasploit that functions as a RAT. We can check netscan to see if there are any services that connect on the default Metasploit port (4444).

![](images/image-194.webp)

![](images/image-195.webp)

The PID is 3496 which corresponds to the infected process we found earlier.

# Completion 

![](images/image-196.webp)
