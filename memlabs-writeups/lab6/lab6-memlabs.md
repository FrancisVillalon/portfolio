---
title: Lab 6 - The Reckoning
parent: MemLabs
nav_order: 6
---

# Challenge Description

We received this memory dump from the Intelligence Bureau Department. They say this evidence might hold some secrets of the underworld gangster David Benjamin. This memory dump was taken from one of his workers whom the FBI busted earlier this week. Your job is to go through the memory dump and see if you can figure something out. FBI also says that David communicated with his workers via the internet so that might be a good place to start.

**Note**: This challenge is composed of 1 flag split into 2 parts.

The flag format for this lab is: **inctf{s0me_l33t_Str1ng}**

**Challenge file**: [MemLabs_Lab6](https://mega.nz/#!C0pjUKxI!LnedePAfsJvFgD-Uaa4-f1Tu0kl5bFDzW6Mn2Ng6pnM)

# Initial thoughts

- Communicated with workers via internet -> Browser related artifacts and maybe also netscan

# Getting Started

![](images/307b9422f9614e981444b12f54409d7f0af91db804853bc1c20865a7757429ba.webp)

There is alot of chrome and firefox processes running. The google crash handler also was running so the browser likely crashed.
Lets see cmdline as well to see if any interesting programs were invoked and with arguments.

![](images/bb66d031f282b52773607ccda457eddb7680cabcca221f21e42c7dc62b9ad4ce.webp)

Winrar was invoked to archive a rar file for user jaffa. We can also see that cmd was running lets try checking cmdscan and consoles for any clues.

![](images/55ff1d180fb653f37e7bd28581dc89bf40220ea1250f97367e98a7181843e7f0.webp)

This is odd, the user ran whoami and env on the cmd. Also the name of the pc is virus-pc.
Env is a linux command to show the current environment variables so it is strange to see it be used in cmd.

From this we have a few interesting leads
- Browser processes , both firefox and chrome
- Crash handlers for chrome were running
- Winrar was invoked for a rar archive called flag 
- whoami and env were run on the cmd for some reason


# Checking envars

The user ran `env` in cmd for some reason. 
Maybe there is something hidden in the envars, lets investigate.
Lets output the envars into a file then grep from there since the output is very long.
Lets start with grepping chrome to see if anything interesting surfaces.

![](images/image-163.webp)

Interestingly enough, there is a rar password in the envars `easypeasyvirus`.
This could be the password to the rar file.

# WinRAR
Lets start with investigating the rar file. 
We first do a filescan and grep the path `jaffa\desktop` and see what we get.

![](images/a7df26a98c06cc1311afa441d9524eedbd66659edfc1aa2382187328b2c7c759.webp)

Few interesting files come up.
Flag.rar looks like it contains part of the flag in the challenge.
However, there is a memory dump file as well.
Lets dump both these files and investigate them.

![](images/d45308c54ddc66edc723b5451ff1d76f906bd686e7c85c2b43e8ca76564952b6.webp)

Trying to dump the .raw file results in nothing being written.
Lets inspect the rar file and see what we can find.

![](images/d471d05d617881a99ce43a222d1602f4b3d97d96c3d4d9e680d36e1a4cdc9a79.webp)
![](images/4b950ee8fb88cec6b18906015d2ad1eddae72bf933373537b31d63658ee38898.webp)

The rar archive contains an image called flag2.png is password protected. Lets then use the password we found in envars to unlock it.


![](images/image-164.webp)

This outputs a flag2.png which when opened reveals

![](images/image-165.webp)

Part2 of the flag is `aN_Am4zINg_!_i_gU3Ss???_}`
# Browsers
Lets see how these browsers were invoked through cmdline.

![](images/826edb25538dcd3600eb05eabc25d70b1f49d41b16bd2b7ff695ea8f74213549.webp)

Looks like they are running from the expected directories, lets try a filescan to see if we can get the local db for the browsers

For firefox the file is called places.sqlite  so we grep for that.

![](images/815b281021698869e9169546fcfa1c64e4968ccbe9542f03106df5a2629c467d.webp)

For google chrome its just called History but its actually also an sqlite db.

![](images/5fe47a4b5074b55bb5ff24fbe7818290d46060d8438e1f7460d5a2c6fca4bf04.webp)

There is also history files for internet explorer, we can investigate those as well.

## Dumping the firefox history files

We should dump the shm,wal and main sqlite files. These are all required for a fuller picture because the main places.sqlite file may not have the most recent changes.

![](images/9ab4cc680511d0ad4d91eec359e9cbf02c04a4dbea90f4d079f494cfa372a7e6.webp)

Lets perform a strings on the places.sqlite-wal file because it was the only file that we got from dumpfiles that was a .dat file.
The actual places.sqlite file was only .vacb which means its only the memory mapped cached view. 
We should look at both regardless but we can start on the .dat first.

![](images/image-139.webp)

The challenge description states that `FBI also says that David communicated with his workers via the internet so that might be a good place to start` . One of the most common ways to communicate with anyone on the internet is through email, let's try to grep for keyword mail to see what we can get.

![](images/image-140.webp)

Here we see a few interesting things
- User received an email from davidbenjamin939@gmail.com 
- The email was about a mega drive key

Lets try grepping for mega to see if we can get the actual link 

![](images/image-141.webp)

We get nothing.  Lets try dumping the firefox process later to see if we can get something interesting.

##  Dumping google history files

Before dumping the history files for google chrome we have to also note that googlecrashhandler was running. 
This could mean that the history for the browser is instead in the history-journal file instead of history since chrome ended abruptly.
History-journal is the write ahead journal for the history file.
It is the temporary transaction log created by sqlite so that when chrome crashes, it can roll back incomplete transactions.

Lets dump both files to see what we get.

![](images/image-146.webp)

Lets do a strings on the history-journal and see what we get

![](images/image-147.webp)
![](images/image-148.webp)

Nothing of use , lets strings history instead 

![](images/image-149.webp)

When we do a strings on history and cat the output we find something interesting.

![](images/image-150.webp)

We find a pastebin link. Going to this pastebin link we will see 

![](images/image-151.webp)

It confirms the david sent the key in the mail and if we look at the google doc it links to

![](images/image-152.webp)

At first it looks like nothing but if we look through the text , we ill find a mega link hidden inside it.

![](images/image-153.webp)

Going to this link will ask us for a decryption key which confirms what we found in the firefox history strings dump as well.

![](images/image-154.webp)

We need to find the key to this mega drive.

## Dumping firefox process


Lets dump the firefox process to see if we can find anything interesting.

![](images/image-142.webp)

![](images/image-143.webp)

Then lets do a strings on the dump and grep davidbenjamin emails

![](images/image-145.webp)

![](images/image-156.webp)

This shows an email with subject "zyWxCjCYYSEMA-hZe552qWVXiPwa5TecODbjnsscMIU" which is highly suspect.
Lets try using it to unlock the mega drive.

## Unlocking the mega drive

In the firefox process we found the an email subject `zyWxCjCYYSEMA-hZe552qWVXiPwa5TecODbjnsscMIU`.
Lets try to unlock the mega drive using that key.

![](images/image-158.webp)

![](images/image-159.webp)

Success! Lets download this file and see what it looks like.

## flag_.png

Trying to open this image results in this

![](images/image-160.webp)

Maybe there is something else hidden in the image lets first check what type of file is this

![](images/image-161.webp)

If we do xxd on the file we can see its header

![](images/image-166.webp)


We can see the png magic bytes but for some reason file is not properly classifying it as a png file.
Lets google what a png header should be.
We find [PNG Specification: Chunk Specifications](https://www.libpng.org/pub/png/spec/1.2/PNG-Chunks.html#:~:text=The%20IDAT%20chunk%20contains%20the%20output%20datastream%20of%20the%20compression,of%20all%20the%20IDAT%20chunks) .

It states that an IHDR chunk must appear first. 
However, if we look at the hex output of flag_.png , we can see instead of IHDR it is iHDR.
Maybe the file is not opening because of the lower case "i".
Lets edit that in hxd.

![](images/image-167.webp)
 
Change "i" to "I".

![](images/image-168.webp)

Then we save it as a new file and try to open it.

![](images/image-169.webp)

Opening it now, we get

![](images/image-170.webp)

Giving us the first part of the flag which is `inctf{thi5_cH4LL3Ng3_!s_g0nn4_b3_?_`

# Combining the flags

We found two parts of the flag
- Part 1 : `inctf{thi5_cH4LL3Ng3_!s_g0nn4_b3_?_`
- Part 2 : `aN_Am4zINg_!_i_gU3Ss???_}`

Putting this together we have ,

`inctf{thi5_cH4LL3Ng3_!s_g0nn4_b3_?_aN_Am4zINg_!_i_gU3Ss???_}`

# Submission

![](images/image-171.webp)
