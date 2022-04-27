import logging

class Logger:
    def __init__(self, name, debug, show, save=True ):
        """
        日志记录系统
        :param name: 日志保存时使用的Name
        :param debug: 控制台输出等级传参    #有人懒得在外面传loghandler
        :param show: 是否在控制台显示日志
        :param save: 是否将日志保存至本地
        """
        log_path = f"logs/{name}.log"
        self.logger = logging.getLogger(name)
        # self.logger.handlers.clear()
        self.logger.setLevel(logging.DEBUG)
        if not self.logger.handlers:
            if show:
                sh = logging.StreamHandler()
                if debug:
                    sh.setLevel(logging.DEBUG)
                else:
                    sh.setLevel(logging.INFO)
                sh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
                self.logger.addHandler(sh)
            if save:
                fh = logging.FileHandler(log_path)
                fh.setLevel(logging.DEBUG)
                fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
                self.logger.addHandler(fh)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warn(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)