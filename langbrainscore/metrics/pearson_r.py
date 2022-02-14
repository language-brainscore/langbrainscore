import scipy

scipy.stats.pearsonr


def pearson_r(x, y):
    """
    Calculates the Pearson correlation coefficient between two lists of
    numbers.

    Parameters
    ----------
    x : list
        List of numbers.
    y : list
        List of numbers.

    Returns
    -------
    float
        Pearson correlation coefficient.

    Raises
    ------
    ValueError
        If lists are not of equal length.
    """
    if len(x) != len(y):
        raise ValueError("Lists must be of equal length.")

    r, p = scipy.stats.pearsonr(x, y)
    return r

def pearson_r_nd(X, Y):
    assert X.shape == Y.shape
    return np.diag(np.corrcoef(X.T,Y.T)[X.shape[1]:,:X.shape[1]])