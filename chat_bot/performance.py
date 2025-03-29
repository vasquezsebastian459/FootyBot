import time


class Performance:
    def __init__(self):

        self.start_overall_time = time.time()
        self.overall_time = 0

        self.extract_key_info_time = 0
        self.get_user_intention_time = 0
        self.run_chat_bot_time = 0

        self.tokens_used = {}
