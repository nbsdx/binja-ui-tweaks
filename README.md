# binja-ui-tweaks
UI Tweaks for Binary Ninja. Seems kinda stable, I just got it working, so there may be some things that I missed. 

Stability could be totally killed by any future updates to Binary Ninja, so take caution applying tweaks after an update.

# Suggestions

If you have suggestions for UI modifications, open a pull request and we can talk about it :)

# Dependencies 

1. Ubuntu 16.04 (only platform tested)
2. Binary Ninja
3. PyQt5 (Ubuntu Repo Version)
4. [binja-ui-api](http://www.github.com/nbsdx/binja-ui-api)

# Usage

Drop "binja-ui-tweaks.py" into the plugins directory (must be able to see the BinjaUI directory).

Tweaks will show up in the "Tools" menu. Since they require the view from Binary Ninja, we cannot use the AddMenuTree function from BinjaUI.

# Features

## Sortable Function Window

Location: `Tools -> Tweak Function List`

* Enables you to sort the function list.

### Bugs

1. Will only work for one view. Whichever view that is is probably random if you have more than one open. I sugest not using more than one view with this tweak currently
  * You might be able to enable the tweak, then open another view, but you probaly won't be able to enable the tweak for the new tab.

## Function Graph Preview

Location: `Tools -> Add Graph Preview`

* Gives you a high-level overview of your function - similar to IDA's. It's located in the `Graph` tab next to `Xrefs`

### Bugs

1. Rendering the image takes a lot of resources, so if you're resizing it with a large function, there will be some lag. 
   * Might look at rendering an SVG image that can be resized more easily when you enter a new function
