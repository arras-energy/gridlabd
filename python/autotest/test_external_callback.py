import gldcore

def my_callback(data):
	print("my_callback(data) -> 1")
	return 1

gldcore.add_callback("my_callback",my_callback)
