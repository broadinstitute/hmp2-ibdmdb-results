import json
from django.template import Library

register = Library()

@register.filter(name="hmp2json")
def hmp2json(value):
  return json.dumps(value)
