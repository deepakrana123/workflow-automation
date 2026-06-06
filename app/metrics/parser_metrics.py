class ParserMetrics:
    

    def __init__(self):
        self.total_requests = 0
        self.cache_hits = 0
        self.regex_hits = 0
        self.llm_hits = 0
        self.failures = 0
        self.fallback_used = 0
        self.total_cost = 0.0
        self.ollama_hits = 0
        self.gemini_hits = 0

    def reset(self):
        self.__init__()

    def to_dict(self):
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "regex_hits": self.regex_hits,
            "llm_hits": self.llm_hits,
            "failures": self.failures,
            "fallback_used": self.fallback_used,
            "total_cost": self.total_cost,
            "ollama_hits": self.ollama_hits,
            "gemini_hits": self.gemini_hits,
        }


parser_metrics = ParserMetrics()
