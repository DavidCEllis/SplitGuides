# SplitNotes 2 #

**Speedrun notes with markdown and html formatting**

SplitNotes2 is an application for displaying speedrun notes in sync with livesplit.
Requires *livesplit server* to be running.

There is now a server version included to allow reading from a browser on another device.

## Install/Setup ##

1. Under the Livesplit layout editor add 'LiveSplit Server' (listed under 'control')
2. Download SplitNotes2 from the [**releases page**](https://github.com/DavidCEllis/SplitNotes-2/releases)
3. Extract anywhere and run *splitnotes2.exe*

## Usage ##

1. Connect with livesplit by starting the livesplit server component selecting 
   'Control' and 'Start Server'
2. Right click in the splitnotes window and select 'Open Notes' and find the text file
   containing the notes you wish to use.
   
Formatting can now be done either using plain text and html tags or by using markdown formatting.
Plain text files will automatically have breaks inserted for newlines, html files will not.
Markdown files will also have breaks inserted on newlines.
If a blank line is used as the split separator, multiple empty lines will be ignored.
   
## splitnotes2_server.exe ##

Now included is a server version which launches a (local) webhost so you can view the splitnotes
on another device on your local network. Launch splitnotes2_server.exe to start the service.

If the hostname and port defaults aren't usable you can set them by editing server_hostname 
and server_port in settings.json. There is no dialog for editing these settings yet.
   
### Example Notes ###

#### Source ####

```markdown
## High Hedge ##
### Friendly Arm Inn ###
* *East*
* *Pick up the ring*
* **Peldvale**

### Peldvale ###
* *South*
* **High Hedge**

### High Hedge ###
* Rest and Spin
* *South to Shop*
* Thalantyr (1, 1)
* Shop:
    * Sell the wand
    * Identify the ring
    * Sell the ring
    * 3x Potion of Explosions
    * Potion of Magic Blocking
    * Protection from Magic
    * Identify
    * Shield
    * Mirror Image
    * 3x Invisibility
* *South*
* Go to Wilderness Map
/split
```

#### Result ####

![Image of splitnotes rendering](resources/demo_notes_md.png)

## Configuration ##

The settings page offers some customisation and connection settings including:

  * Server hostname and port
  * Show previous/next N splits
  * Custom split separator
  * Base font size
  * Default text and background colour
  * HTML (Jinja2) template and CSS files to use for rendering

## Dependencies ##
pyside2 - QT Gui Bindings
jinja2 - Templating for the notes page
bleach - Cleaning HTML to help protect if someone decided to make notes with a malicious script
flask - Handling the server version
attrs -  

--- 

Inspired by (but otherwise unassociated with) the original splitnotes: https://github.com/joeloskarsson/SplitNotes

[*] approximately 19x larger in file size :) (Mostly Qt and PySide2)
