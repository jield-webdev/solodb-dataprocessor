from .plot import histogram


class Hist():
  link: str = "raman_hist"
  input_type: str = "raman"
  description: str =(  
    "Write a custom description here"
  )
  example_config: dict = {"key" : "g_w"}
  def run(self, *args, **kwargs):
    return histogram(*args, **kwargs)


processors = [Hist()]  