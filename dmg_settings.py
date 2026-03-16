import os

app_path = os.path.join("dist", "Font Maker.app")

application = app_path
appname = os.path.basename(app_path)

format = "UDBZ"
size = None
files = [app_path]
symlinks = {"Applications": "/Applications"}

icon_locations = {
    appname: (140, 200),
    "Applications": (500, 200),
}

background = "builtin-arrow"

window_rect = ((200, 200), (640, 480))
default_view = "icon-view"

icon_size = 128
text_size = 14
