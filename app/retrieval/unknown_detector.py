class UnkownDetetor:
    def is_unknown(self,confidence:float,threshold:float)->bool:
        return confidence<threshold