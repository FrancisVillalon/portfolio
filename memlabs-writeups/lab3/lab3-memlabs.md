---
title: Lab 3 - The Evil Twin
parent: MemLabs
nav_order: 3
---

# Challenge Description

A malicious script encrypted a very secret piece of information I had on my system. Can you recover the information for me please?

**Note-1**: This challenge is composed of only 1 flag. The flag split into 2 parts.

**Note-2**: You'll need the first half of the flag to get the second.

You will need this additional tool to solve the challenge,

```shell
$ sudo apt install steghide
```

The flag format for this lab is: **inctf{s0me_l33t_Str1ng}**

# Initial Thoughts

- Explicitly was told to install steghide implies information was hidden in an image
- Encrypted a secret piece of information, maybe we can find something interesting in cmdline to see what was invoked

# Finding Flag

Lets get the image info to get started

![](images/f1d8b78d90565311d9d6511c34261ae0d1a5babfd31d40e64a21de36c87b482e.webp)

Then lets do a pslist

![](images/8fa90e1b708620bb0910652e8406e50dd8bd443e22728dcb82d6482d7b758558.webp)

We can see two notepad instances open lets try doing a cmdline to see how notepad was invoked or maybe find some clues pertaining to that

![](images/93c09b13b1fe2f86998162cf692ea8340116903688815e723e602d8d25f36046.webp)![](images/77a9e034e0a1bd697c4ee8f3e2034271fad85e576b12ac2173d843261e7a1c6d.webp)

Found 2 files evilscript.py and vip.txt, lets find the offset and dump them

![](images/17849171780071525e18816161e27c06456456ea0cfa31f82f1a34bf9e54beb5.webp)

We found the offset lets try dumping them 

![](images/image-62.webp)

![](images/image-63.webp)

Now lets examine each file

![](images/image-64.webp)

![](images/image-65.webp)

The text in vip.txt was first xor'ed then encoded in base64. 
Lets decode the text using a simple python script

![](images/image-66.webp)

![](images/image-67.webp)

This gets us the first half of the flag
```
inctf{0n3_h4lf
```

The path of these files were`hello\Dekstop` lets try to do a filescan and grep `'hello\\desktop`, maybe we can find something else of value just sitting on the desktop.
![](images/image-68.webp)

There is an image sitting on the desktop lets try dumping that
![](images/image-69.webp)

Lets inspect the file using file and xxd and see if anything immediately shows up
![](images/image-70.webp)![](images/image-71.webp)

Opening the image as well just gives us a normal shutterstock photo
![](images/image-72.webp)

Maybe the  information is hidden in the image using steghide, also the challenge description does we need steghide to actually solve this.
Another note also states that we need the first part of the flag to get the second so maybe the first flag is the passphrase to extract the image.

Lets try that

![](images/image-73.webp)

We got it
![](images/image-74.webp)

The full flag is

```
inctf{0n3_h4lf_1s_n0t_3n0ugh}
```

# Submission

![](images/image-76.webp)