# fake empty module for file path getting

# You can normally use __file__ but that doesn't work when the whole application
# is frozen via cx_freeze (because the code is inside a zip file).
#
# What works however is doing module.__file__, it simply returns the path to
# library.zip (cx_freeze's file containing all python code)
