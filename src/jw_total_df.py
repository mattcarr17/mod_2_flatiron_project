import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf
import statsmodels.api as sm
import scipy.stats as stats
from sklearn.datasets import make_regression
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import power_transform
from statsmodels.stats.outliers_influence import variance_inflation_factor
import statsmodels.api as sm
import scipy.stats as stats
from sklearn.model_selection import train_test_split


def create_initial_dataframes():
    ps_df = pd.read_csv('../../data/EXTR_RPSale.csv')
    b_df = pd.read_csv('../../data/EXTR_ResBldg.csv')
    p_df = pd.read_csv('../../data/EXTR_Parcel.csv', encoding='latin-1')

    return ps_df, b_df, p_df

def add_major_leading_zeros(majors):
    # Empty list to store formatted major codes in
    f_majors = []
    
    # loop through current majors and add leading zeros
    for major in majors:
        #convert major to str and split
        s = [num for num in str(major)]
        # length of current major code
        l = len(s)
        # list with 6 zeros
        f_major = ['0', '0', '0', '0', '0', '0']
        # take current major and add to end of list
        f_major[6-l:] = s
        #join list into str
        f_major = ''.join(f_major)
        # convert to int append to formatted majors list
        f_majors.append(f_major)
    
    return f_majors

def add_minor_leading_zeros(minors):
    # Empty list to store formatted minor codes in
    f_minors = []
    
    # loop through current minors and add leading zeros
    for minor in minors:
        #convert minor to str and split
        s = [num for num in str(minor)]
        # length of current minor code
        l = len(s)
        # list with 4 zeros
        f_minor = ['0', '0', '0', '0']
        # take current minor and add to end of list
        f_minor[4-l:] = s
        #join list into str
        f_minor = ''.join(f_minor)
        # convert to int append to formatted minors list
        f_minors.append(f_minor)
    
    return f_minors

def add_leading_zeros(majors, minors):
    return add_major_leading_zeros(majors), add_minor_leading_zeros(minors)

def merge_dataframes(df1, df2, df3, type, cols):
    df = df1.merge(df2, how=type, on=cols).merge(df3, how=type, on=cols)
    return df

def create_dataframe():
    ps_df, b_df, p_df = create_initial_dataframes()
    
    
    ps_columns = ps_df.columns
    b_columns = b_df.columns
    p_columns = p_df.columns
    
    year = [True if int(d[6:]) == 2019 else False for d in ps_df['DocumentDate']]
    ps_df = ps_df[year]
    
    ps_df['Major'], ps_df['Minor'] = add_leading_zeros(ps_df['Major'], ps_df['Minor'])
    b_df['Major'], b_df['Minor'] = add_leading_zeros(b_df['Major'], b_df['Minor'])
    p_df['Major'], p_df['Minor'] = add_leading_zeros(p_df['Major'], p_df['Minor'])
    
    df = merge_dataframes(ps_df[ps_columns], b_df[b_columns], p_df[p_columns], 'inner', ['Major', 'Minor'])
    
    df = df[df['SalePrice'] > 0]
    
    has_porch = [1 if ((op > 0) | (ep > 0)) else 0 for op, ep in zip(df['SqFtOpenPorch'], df['SqFtEnclosedPorch'])]
    df['has_porch'] = has_porch
    
    return df

def dummify(df, column_names):
    dataframes = []
    copy_df = df.copy()
    for column in column_names:
        new_df = pd.get_dummies(df[column], drop_first=True)
        new_df.columns = [column + '_' + str(name) for name in new_df]
        dataframes.append(new_df)
        copy_df.drop(column, axis = 1, inplace = True)
    new_df = pd.concat(dataframes, axis=1)
    return pd.concat([copy_df, new_df], axis = 1)

def pow_transformer(df , column_names):
    dataframe = []
    copy_df = df.copy()
    for column in column_names:
        new_df = power_transform(np.array(df[column]).reshape(-1,1))
        new_df.columns = [column + '_' + str(name) for name in new_df]
        dataframes.append(new_df)
        copy_df.drop(column, axis=1, inplace=True)
    new_df = pd.concat(dataframes, axis=1)
    return pd.concat([copy_df, new_df], axis=1)

import statsmodels.formula.api as smf

def forward_selected(data, response):
    """Linear model designed by forward selection.

    Parameters:
    -----------
    data : pandas DataFrame with all possible predictors and response

    response: string, name of response column in data

    Returns:
    --------
    model: an "optimal" fitted statsmodels linear model
           with an intercept
           selected by forward selection
           evaluated by adjusted R-squared
    """
    remaining = set(data.columns)
    remaining.remove(response)
    selected = []
    current_score, best_new_score = 0.0, 0.0
    while remaining and current_score == best_new_score:
        scores_with_candidates = []
        for candidate in remaining:
            formula = "{} ~ {} + 1".format(response,
                                           ' + '.join(selected + [candidate]))
            score = smf.ols(formula, data).fit().rsquared_adj
            scores_with_candidates.append((score, candidate))
        scores_with_candidates.sort()
        best_new_score, best_candidate = scores_with_candidates.pop()
        if current_score < best_new_score:
            remaining.remove(best_candidate)
            selected.append(best_candidate)
            current_score = best_new_score
    formula = "{} ~ {} + 1".format(response,
                                   ' + '.join(selected))
    model = smf.ols(formula, data).fit()
    return model

def multi_coll(df):
    corr_df = df.corr().abs().stack().reset_index().sort_values(0, ascending=False)
    corr_df['pairs'] = list(zip(corr_df.level_0, corr_df.level_1))
    corr_df.set_index(['pairs'], inplace=True)
    corr_df.drop(columns=['level_1', 'level_0'], inplace=True)
    corr_df.columns = ['corrcoeff']
    corr_df.drop_duplicates(inplace=True)
    corr_df[(corr_df.corrcoeff>.2) & (corr_df.corrcoeff<1)]
    return corr_df