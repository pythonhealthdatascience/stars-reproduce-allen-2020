import pandas as pd

def expand_multi_index(df, new_cols):
    """
    Expands a multi-index (and removes the multi-index).

    Parameters
    ----------
    df : pandas DataFrame
        DataFrame with multi-index to be expanded.
    new_cols : list
        List of column names for expanded index.

    Returns
    -------
    df : pandas DataFrame
        DataFrame with expanded multi-index.

    """
    
    # convert from objects
    df = df.convert_dtypes()
    multi_index = df.index
    
    df.reset_index(inplace=True)
    number_of_indices = len(multi_index[0])
    for i in range(number_of_indices):
        old_index = 'level_' + str(i)
        new_index = new_cols[i]
        df.rename(columns={old_index: new_index}, inplace=True)
        
    return df