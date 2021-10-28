game_pos = {
    "start_button": [(142, 573), (308, 613)],
    "return_home": [(65,687), (101,722)],
    "retry": [(199,684),(359,725)],
    "jump_tap":[(38,190),(431,765)],
}

game_scene = {
    "start_index": ["img/start_game.png", "img/start_title.png", True],
    "over_page": ["img/retry.png", "img/return_home.png", True],
    "play_page": ["img/player.png", False],
}


class GamePos():
    def __init__(self):
        self.game_pos = game_pos

    def get_pos(self,name):
        if name in self.game_pos:
            return self.game_pos[name]
        else:
            return False

    def get_all(self):
        return self.game_pos


class GameScene():
    def __init__(self):
        self.game_scene = game_scene

    def get_scene(self, name):
        if name in self.game_scene:
            return self.game_scene[name]
        else:
            return False

    def get_all(self):
        return self.game_scene
