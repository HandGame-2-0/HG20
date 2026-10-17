from handgame.main import restore_vscode_snap_env


def test_restores_and_unsets_snap_leaked_variables():
    environ = {
        "GSETTINGS_SCHEMA_DIR": "/home/user/snap/code/271/.local/share/glib-2.0/schemas",
        "GSETTINGS_SCHEMA_DIR_VSCODE_SNAP_ORIG": "",
        "XDG_DATA_DIRS": "/snap/code/271/usr/share:/usr/share",
        "XDG_DATA_DIRS_VSCODE_SNAP_ORIG": "/usr/local/share:/usr/share",
        "HOME": "/home/user",
    }

    restored = restore_vscode_snap_env(environ)

    assert sorted(restored) == ["GSETTINGS_SCHEMA_DIR", "XDG_DATA_DIRS"]
    assert "GSETTINGS_SCHEMA_DIR" not in environ
    assert environ["XDG_DATA_DIRS"] == "/usr/local/share:/usr/share"
    assert environ["HOME"] == "/home/user"


def test_leaves_environment_alone_outside_vscode_snap():
    environ = {"XDG_DATA_DIRS": "/usr/share", "HOME": "/home/user"}

    assert restore_vscode_snap_env(environ) == []
    assert environ == {"XDG_DATA_DIRS": "/usr/share", "HOME": "/home/user"}
