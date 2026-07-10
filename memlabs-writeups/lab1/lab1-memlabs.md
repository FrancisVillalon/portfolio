---
title: Lab 1 - Beginner's Luck
parent: MemLabs
nav_order: 1
---

# Challenge description

My sister's computer crashed. We were very fortunate to recover this memory dump. Your job is get all her important files from the system. From what we remember, we suddenly saw a black window pop up with some thing being executed. When the crash happened, she was trying to draw something. Thats all we remember from the time of crash.

**Note**: This challenge is composed of 3 flags.

# Initial thoughts
- Black window that popped up and ran something -> Likely cmd window so we will look at cmdscan, consoles, cmdline
- She was drawing something then it crashed -> Likely has something to do with mspaint or some other software to draw 
- My job is to get all her important files -> Maybe use filescan and see if any files have an interesting name that tells me it is important


# First Flag

![](./images/7be6a76df9940a859dd29ba4d24c7857733d28acf6b77ac18d587b00757828e1.webp)

Sister was apparently drawing something when crash happened. Challenge also stated cmd window opened with something being executed. Let us look at the pslist.

![](./images/4711d8c780e03413fd97b264c57ca3d2f5fdb91a30739ba8be5211c3b5bced80.webp)

A cmd window launched

![](./images/714f1cbeee48c07207c8769c6f82ff186c1676a4ab5158950fb160c9643f776b.webp)

Lets do a cmdscan

![](./images/18f7f0ec272668ffca765493097234571c569764d65c998936e21c283ecce74b.webp)

Looks like someone executed leetspeak for stage1. Lets see if that produced any output.

```
St4G3$1
```

Lets use consoles plugin.

![](./images/7013e7773924ae6a7e7f124f9caf62a1ae991d6d843febbd4b958983ce2a07d6.webp)

That stage 1 command looks like it produced a base64 encoded string
```
ZmxhZ3t0aDFzXzFzX3RoM18xc3Rfc3Q0ZzMhIX0=
```

Lets decode

```
echo "ZmxhZ3t0aDFzXzFzX3RoM18xc3Rfc3Q0ZzMhIX0=" | base64 -d
```

Which decodes to 
```
flag{th1s_1s_th3_1st_st4g3!!}
```

# Second Flag

Challenge states that she was drawing something on mspaint before a crash. Mspaint stores the canvas as raw pixel data in memory.  Lets dump the mspaint memory and try to get an image out of it. The pid of mspaint.exe is 2424.

![](./images/image-21.webp)

This produced the file 2424.dmp which we can change the file extension to .data to then open in gimp.

![](./images/image-22.webp)

Then we just do trial and error for the width, height, offset and pixel format until something that looks like an image appears

![](./images/image-23.webp)

We then open this image and notice that the canvas looks transformed like it was flipped horizontally or vertically.
We then just flip it either horizontal or vertically a few times until something legible appears.

![](./images/image-24.webp)
![](./images/image-25.webp)

This tells us the second flag is 

```
flag{G00d_BoY_good_girL}
```

# Third flag 

Lets look more into the phrase "all her important files".
Lets do a filescan and grep "Important"

```
vol2 -f /mnt/d/work/repo/lab1-memlabs/lab1-challenge/MemoryDump_Lab1.raw --profile=Win7SP1x64_23418 filescan | grep -i "Important"
```

![](./images/65a3b2141668ebb80148406d750cca2e4f6d2556d8f1444d647070d12f8436ad.webp)

Lets dump the file and check if its a legitimate rar file

```
vol2 -f /mnt/d/work/repo/lab1-memlabs/lab1-challenge/MemoryDump_Lab1.raw --profile=Win7SP1x64_23418 dumpfiles -Q 0x000000003fa3ebc0 --dump-dir=/mnt/d/work/repo/lab1-
memlabs/lab1-challenge/output

xxd file.None.0xfffffa8001034450.dat | head -20
```

Header has rar as well as a hint to the password of the rar file.

![](./images/b85c025d12fcc75e1be63a545f068f0a438d9e26775be32fa2b033dedfc0b005.webp)

Password to the rar file is NTLM hash of alissa so lets hashdump

![](./images/95f0b779f50d8948d9c2d4591cd5934092ff12eb0e3f2b463d7f02f9b2e1e596.webp)

Then just upper case the entire hash

![](./images/9c88cd8293a3977a10ecb4d1fc15e23b751cebb7a0847e54061de5270c732cb8.webp)

so the password is
```
F4FF64C8BAAC57D22F22EDC681055BA6
```

We then just unpack rar file

![](./images/5a89e0f41fe958ce75e186f8e38052dd02632dc148fd0f483806a61339d41546.webp)

Then we just open the png

![](./images/2c548d5292ae77634a900387fe7b8f5ea87d32a8eab398ab506304a5b0051c72.webp)

flags collected

```
flag1 : flag{th1s_1s_th3_1st_st4g3!!}
flag2 : flag{G00d_BoY_good_girL}
flag3 : flag{w3ll_3rd_stage_was_easy}
```
# Submission

Lets now submit
![](./images/image-29.webp)

# Additional Notes
We could have used cmdline to determine

Winrar was used to create the important.rar, important for flag 2

![](./images/image-27.webp)


Mspaint had no arguments so likely the image was not saved, challenge description also hints at this because she was trying to draw something then it crashed. Heavily implies a memdump is required on that process.

![](./images/image-28.webp)

