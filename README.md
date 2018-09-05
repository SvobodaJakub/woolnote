# woolnote
Woolnote note and task management app written in Python

## README

### Setting up
* Create folders described in woolnote/config.py
* Create empty .dat files described in woolnote/config.py
* Set path to sync file in woolnote/config.py
* Generate an SSL/TLS certificate according to instructions in woolnote/config.py and note the fingerprint there.

### Easy to type lists
Lists are text lines beginning with "-" or "+" or "\*"or "\*\*" or "\*\*\*" followed by a space and text. The following lines automatically gain the same prefix on save (until an empty line or until a different list is defined). This allows you to easily type a long list on the phone keyboard because you don't have to search for the special characters on each line - just on the first line. If you don't like the feature, set the note's format to plaintext - this is useful when you insert arbitrary copy&pasted things like emails or code.
More information about formatting is directly inside woolnote in the "_woolnote_config" note.

### Backups
Woolnote creates local backup copies of the task database on these occasions:
* Starting up the woolnote server.
* Export
* Import

Sometimes, you might need to recover old data. You might find them in the backups directory. The primary task database is task_store.dat. To recover data, first make a backup of task_store.dat so that you can revert in case you do something wrong. Quit woolnote. Manually fix the database file (make sure not to break the file format structure). You might find the tools grep, meld, windiff useful.

The backups directory is growing, you might want to clean it from time to time.

# FAQ 
A.k.a. questions nobody asks that I pulled out of my colored hat :)

* Is woolnote better than other note-taking apps?
    * Objectively, no.
* What are the strengths of woolnote?
    * OpenSource, 
    * easily hackable in Python, 
    * allows easy switching between using PC and phone without synchronization, 
    * simple data format that doesn't lock you in (and you can use woolnote's source code to hack together export to another format should you decide to move to sth else), 
    * you are in control of the data,
    * backup archive with previous note database versions, 
    * simple markup language allowing the creation of ad-hoc mixed checklists and notes with simple formatting, 
    * use of a markup language to insert lists and textboxes into an ordinary plaintext text area is much faster and smoother than the feature-rich text areas that some other note-taking apps use,
    * import&export including a rudimentary ability to handle conflicts,
    * no user tracking (well, if you don't use cloud storage for import&export),
    * individual notes can be shared over the local network as read-only to other people who don't have login,
    * access token & password checking is implemented in a secure way preventing timing attacks to reveal the password over network,
    * HTTPS support.
* Should I use woolnote?
    * Depends on your needs and expertise with Python and IT in general in case something breaks.
    * If you are happy with Google Keep, Evernote, Simplepad, or any other existing product, please don't use woolnote. Woolnote is not a product, has no development lifecycle, has no support, and is not tailored to keep most users happy.
    * If you tried all of them and you are still in a search for something else, you should check out woolnote and if it fits your style, use it as a base for your own app.
* Should I fork?
    * Yes, because woolnote is not aimed for the general user, it has been created to serve my peculiar needs. Adding too much additional functionality wouldn't fit woolnote's non-extensible "architecture". It's better to create a new app using woolnote as a base.
* How do I request new functionality?
    * You can certainly try to request it through github or through a merge request. I might implement/merge it if it fits my needs, or I might advise you to fork and create your own version. If your idea is especially intriguing, I might even maintain a fork for a time, just to experiment with the idea. (I don't usually have much time for woolnote, so don't hold your breath.)
* How can we collaborate?
    * If you happen to have the exact same needs for note and task management, collaboration on a single project with a unified vision might work.
    * If you create a fork, I'd be happy to collaborate on fixing parts that are shared between our forks, to a sensible extent. I believe in friendly forking, leading to healthy competition, growth of fresh ideas, and experiments.
* Will woolnote magically help me with note and task management?
    * No.
    * You need a good system. Start with reading GTD and ZTD for much needed inspiration. Think about yourself and your life. Create a system that suits you. Create a system where you do things not because someone said so but because you have personal reasons why you should do it so.
    * A good system is a vehicle for your thoughts
    * Woolnote is a vehicle for the system. A part of it, actually. I don't want emails in woolnote. I can't have physical stuff in woolnote.
* Why is there such a weak support for reminders?
    * I don't use that functionality that often. A central part of my task list is a week-by-week timeline-like task list where most of the short-term stuff ends up. Most of the long-term reminders end up on my calendar and in my tickler note. The reminder/deadline functionality is therefore for the oddball notes that are perhaps temporary projects (like home renovation) which can't be put easily on one line into a tickler or into the calendar but are a topic of notes and tasks in one woolnote note and then I remember I need this note to pop up on me on a certain date. You can see a few examples of that in the demo file tasks.dat.
* Why does it look so awful?
    * Some people feel uneasy looking at unaligned graphical elements and whatnot. If you are one of them, I know the interface looks insane to you. I don't care about such things and I don't have the time nor the skills necessary to fix it. If you want to make the UI better, you are welcome.

# Bugs

On Windows, there are encoding errors I still don't understand, e.g. when reading pickled tests generated on GNU/Linux and when writing generated tests.
