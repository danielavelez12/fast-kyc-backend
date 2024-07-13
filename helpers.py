import base64
import re

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

ssn_pattern = "^(?!(000|666|9))\d{3}-(?!00)\d{2}-(?!0000)\d{4}$"
def validate_ssn(ssn):
  return re.match(ssn_pattern, ssn)
