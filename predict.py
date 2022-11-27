import pandas as pd
import numpy as np
import math
from sklearn.model_selection import train_test_split
from xgboost.sklearn import XGBRegressor as XGB

df = pd.read_parquet('./../data/BMTC.parquet.gzip', engine='pyarrow')
dfInput = pd.read_csv('./../data/Input.csv')
dfGroundTruth = pd.read_csv('./../data/GroundTruth.csv')


def EstimatedTravelTime(df, dfInput):  # The output of this function will be evaluated
    df['hour_of_the_day'] = df['Timestamp'].dt.hour
    df['minute_of_the_hour'] = df['Timestamp'].dt.minute

    df['second_of_the_minute'] = df['Timestamp'].dt.second

    df['day_of_week'] = df['Timestamp'].dt.day_name()
    df['day_of_week'] = df['day_of_week'].map(
        {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6, 'Sunday': 7})

    dfInput['distance'] = dfInput.apply(
        lambda row: distance(row['Source_Lat'], row['Source_Long'], row['Dest_Lat'], row['Dest_Long']), axis=1)
    dfInput['distance'] = dfInput['distance'].astype(float)

    dfInput.drop('Unnamed: 0', inplace=True, axis=1)

    df['Source_Lat'] = df['Latitude']
    df['Source_Long'] = df['Longitude']

    merge = pd.merge(df, dfInput)
    merge_filtered = merge[merge['Speed'] != 0]

    for i in range(len(merge_filtered) - 1):
        x = merge_filtered.iloc[i, 0] == merge_filtered.iloc[i + 1, 0]
        y = merge_filtered.iloc[i, 1] != merge_filtered.iloc[i + 1, 1]
        z = merge_filtered.iloc[i, 2] != merge_filtered.iloc[i + 1, 2]
        flag = x & (y | z)
        merge_filtered.iloc[i, 14] = 0
        if (flag):
            merge_filtered.iloc[i, 11] = merge_filtered.iloc[i + 1, 1]
            merge_filtered.iloc[i, 12] = merge_filtered.iloc[i + 1, 2]
            merge_filtered.iloc[i, 14] = (merge_filtered.iloc[i + 1, 4] - merge_filtered.iloc[i, 4]) / np.timedelta64(1,
                                                                                                                      'm')

    merge_filtered['Time'] = merge_filtered['Time'].apply(pd.to_numeric, downcast='float', errors='coerce')
    index = merge_filtered[merge_filtered['Time'] == 0].index
    merge_filtered.drop(index, inplace=True)
    merge_filtered['distance'] = merge_filtered.apply(
        lambda row: distance(row['Source_Lat'], row['Source_Long'], row['Dest_Lat'], row['Dest_Long']), axis=1)
    merge_filtered['distance'] = merge_filtered['distance'].astype(float)

    merge_filtered = merge_filtered.dropna()

    x = merge_filtered[['Source_Lat', 'Source_Long', 'Dest_Lat', 'Dest_Long', 'distance']]
    Y = merge_filtered[['Time']]

    x_train, x_test, y_train, y_test = train_test_split(x, Y, test_size=0.1)

    m = XGB()  # n_estimators (int, optional (default=100)) – Number of boosted trees to fit.
    m.fit(x_train, y_train)

    dfOutput = m.predict(dfInput[['Source_Lat', 'Source_Long', 'Dest_Lat', 'Dest_Long', 'distance']])

    return dfOutput


def distance(lat1, lon1, lat2, lon2):
    # distance between latitudes and longitudes
    dLat = (lat2 - lat1) * math.pi / 180.0
    dLon = (lon2 - lon1) * math.pi / 180.0

    # convert to radians
    lat1 = (lat1) * math.pi / 180.0
    lat2 = (lat2) * math.pi / 180.0

    # apply formulae
    a = (pow(math.sin(dLat / 2), 2) +
         pow(math.sin(dLon / 2), 2) *
         math.cos(lat1) * math.cos(lat2));
    rad = 6371
    c = 2 * math.asin(math.sqrt(a))
    return rad * c

dfOutput = EstimatedTravelTime(df, dfInput)