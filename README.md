# binja-ui-tweaks
UI Tweaks for Binary Ninja. Seems kinda stable, I just got it working, so there may be some things that I missed. 

# Dependencies 

Requires the [binja-ui-api plugin](github.com/nbsdx/binja-ui-api) (and obviously all of it's dependencies)

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
