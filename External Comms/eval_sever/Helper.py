def ice_print(*arg, end='\n', color=0):
    # ANSI colors
    _c = (
        "\033[0m",  # End of color
        "\033[36m",  # Cyan
        "\033[91m",  # Red
        "\033[35m",  # Magenta
    )

    if color == 0:
        for a in arg:
            print(a, end=' ')
    else:
        for a in arg:
            print(_c[color] + str(a) + _c[0], end=' ')
    print(end, end='')


DEBUG = True


def ice_print_debug(*arg, color=2):
    if not DEBUG:
        return
    ice_print (*arg, color=color)


class Actions:
    no      = 'none'
    shoot   = "shoot"
    shield  = "shield"
    grenade = "grenade"
    reload  = "reload"
    logout  = "logout"
    all = [no, shoot, shield, grenade, reload]
