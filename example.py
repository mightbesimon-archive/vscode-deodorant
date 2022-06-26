'''
	COMMON STUDENT CODE SMELL
'''

def example1(condition):
	if (condition):
		return True
	else:
		return False

def correction1(condition):
	return condition




def example2(condition):
	if (condition == True):
		...

def correction2(condition):
	if (condition):
		...
