from django import template

register = template.Library()

@register.filter
def truncatechars(obj, count):
	if len(obj) > count:
	    return obj[:count-1] + u'\N{HORIZONTAL ELLIPSIS}'
	else:
		return obj