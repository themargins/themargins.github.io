---
title: Communication in Bits
description: What a bits-per-second count of human speech leaves out, and whether we could ever write it down.
date: October 16, 2026
category: Essay
---

The other day I heard someone cite a number of bits that humans can communicate per second. It's a tidy number, the kind that sticks: spoken language moves at roughly 39 bits per second, and it's about the same across languages.<span class="marginnote">Coupé et al., *Science Advances*, 2019. Fast languages pack less into each syllable and slow ones pack more, so they all land near the same rate.</span> My first thought was that this counts the content and the context, the *what*, and leaves out almost everything about the *how*: the tone, the delivery, the half-second of hesitation before someone says "sure." That is information too, and it may be why so many things get misunderstood over text that would have come through clean in person.

So what are we losing out on? And could we ever encode it?

## Two messages at once

Every message carries two things: what is being said, and what it says about us. "The meeting moved to Thursday" is a fact. Said one way, it's a heads-up between friends. Said another, it's a small accusation. The words are identical; the relationship they describe is not.<span class="marginnote">The psychologist Paul Watzlawick made this an axiom: every communication has a content aspect and a relationship aspect.</span>

Tone, timing, the face and the hands carry most of that second layer. In bit terms it might be small, but it has enormous leverage. Sarcasm can be close to a single bit, and that one bit inverts the meaning of the entire sentence. "Great job" becomes its exact opposite without a single word changing. All of the information in the words survives intact, and it means the reverse. Stress works the same way on a smaller scale. *I* didn't say she took it. I didn't *say* she took it. I didn't say *she* took it. Same sentence, three different accusations.

That's what a bits-per-second count misses. Not all bits are equal, and a few bits of tone decide how all the rest should be read.

## The loop

Something else gets lost that's harder to see. In person, communication is a loop, not a broadcast. While I'm talking, you're nodding, frowning, saying "mm-hm," raising an eyebrow, and I'm adjusting as I go. A misunderstanding gets caught halfway through the sentence that caused it, and repaired before it sets.

Text has no loop. I send, you read alone, and in the silence you fill in the missing tone with whatever you brought to the reading: your mood, your day, your guess about how I feel about you. Usually the guess drifts negative. In one study, people writing emails meant to be either sarcastic or serious expected about 78% of their readers to get the tone right. About 56% did, barely better than a coin flip.<span class="marginnote">Kruger, Epley, Parker and Ng, "Egocentrism over e-mail," 2005.</span> We hear our own voice in our writing. Nobody else does.

## What we've already invented

We haven't sat still. Without anyone designing it, texting has grown its own rough prosody. A period at the end of "ok." reads cold. "lol" stopped meaning laughter and became a softener. Emoji stand in for a face. Ellipses trail off the way a voice does. "/s" marks sarcasm because nothing else reliably can. Even how long you take to reply has become part of the message.

We've wanted this for a long time. People have been proposing an irony mark for centuries, and none has ever caught on.

## How else could we write it down

A few directions I keep coming back to.

**Prosody as markup.** Speech scientists already annotate pitch, stress and pauses in recorded speech. A light version for writing could let you mark emphasis, uncertainty or warmth, the way italics already let you lean on a word.

**Text that remembers how it was typed.** Every message is written with a rhythm: the hesitation before a hard sentence, the fast burst of an excited one, the word typed and deleted three times. Almost all of that is thrown away. It could be kept and shown, with letters that spread apart where you paused or grow heavier where you hurried.

**Going upstream of the words.** This one is closer to my own work. Speech brain-computer interfaces were first built to recover words, and now they are starting to recover tone. In 2025 a group at UC Davis showed a neuroprosthesis that let a man with ALS raise his pitch to ask a question, stress a word, and even sing a short melody, all decoded from activity in his motor cortex.<span class="marginnote">Wairagkar et al., *Nature*, 2025.</span> There, tone isn't something left out. It's a decoding target.

## The catch

Underneath all of this is a question I don't have an answer to. Tone works partly because it's involuntary. A voice cracks, a laugh comes out a little too fast, and that's how you know it's real. Once tone becomes something I choose to encode, is it still tone? Or is it just another layer of content, something I perform?

Maybe that's why the number felt so incomplete to me. It measures what we say on purpose, and a lot of what we mean slips out on its own.
