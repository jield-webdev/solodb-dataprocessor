import pandas as pd
class Processor():
  link: str = "raman"
  input: str = "file"
  def run(self, file):
    
    return [
      {
        "metadata": [
          {
            "name": "Other thickness",
            "value": 3300,
            "std_dev": 12,
            "unit": "angstrom",
            "str_value": None
          }
        ],
        "processed": pd.DataFrame(),
      }
    ]

processors = [Processor()]  