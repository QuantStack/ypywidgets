def init(self, model):
    _super = super(self.__class__, self)
    _super.__init__()
    def _on_ychange(event) -> None:
        for k, v in event.target.items():
            setattr(self, k, v)
    model.ymap.observe(_on_ychange)
    for k in model.dict().keys():
        def watch_value(self, value) -> None:
            getattr(_super, f"watch_{k}")(value)
            setattr(model, k, value)
        setattr(self, f"watch_{k}", watch_value)
