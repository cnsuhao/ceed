
def getDictionaryTreePath(dtree, path, defaultValue=None):
    """Get the value of the dictionary tree at the specified path string.
    
    Return 'defaultValue' if the path can't be found.
    """
    if dtree is None or path is None:
        return defaultValue

    # remove slashes from start because the path is always absolute.
    # we do not remove the final slash, if any, because it is
    # allowed (to return a subtree of options)
    path.lstrip("/")

    pcs = path.split("/")
    optRoot = dtree

    for pc in pcs:
        # if the path component is an empty string we've reached the destination,
        # getDictionaryTreePath("folder1/") for example.
        if pc == "":
            return optRoot

        # if the pc exists in the current root, make it root and
        # process the next pc
        if pc in optRoot:
            optRoot = optRoot[pc]
            continue

        # if it wasn't found in the current root, return the default value.
        return defaultValue

    # we've traversed the option tree, return whatever our root is
    return optRoot
