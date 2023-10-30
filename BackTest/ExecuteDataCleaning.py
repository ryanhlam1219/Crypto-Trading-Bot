import pandas as pd

# Function to read CSV file based on filename
# Ammend exchange name in file path when cleaning different exchanges
def read_csv_file(file_name):
    file_path = 'BackTest/CSV-Files/CSV-Files-BTCUSDT/' + file_name  # Assuming CSV_FILES is the directory where CSV files are located
    df = pd.read_csv(file_path, names=['OpenTimeStamp', 'Open', 'High', 'Close', 'Volume', 'CloseTimeStamp']) 
    return df

def executeScript():
    # Read the .txt file with the list of CSV filenames
    # Ammend exchange name in file path when cleaning different exchanges
    with open('BackTest/CSV-FileNames.txt/CSV-FileNames-BTCUSDT.txt', 'r') as file:
        file_names = file.read().splitlines()

    # Create an empty dictionary to store data frames
    all_data = {}

    # Loop through the list and read each CSV file
    for csvFileName in file_names:
        df = read_csv_file(csvFileName)

        # Set the lookback periods
        rsi_period = 14
        stoch_period = 5
        smooth_period = 3
        wma_period = 144
        sma_period = 5

        # Calculate the RSI
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=rsi_period, min_periods=1).mean()
        avg_loss = loss.rolling(window=rsi_period, min_periods=1).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # Calculate the Stochastic RSI
        rsi_low = rsi.rolling(window=stoch_period, min_periods=1).min()
        rsi_high = rsi.rolling(window=stoch_period, min_periods=1).max()
        stoch_rsi = (rsi - rsi_low) / (rsi_high - rsi_low) * 100
        stoch_rsi_smooth = stoch_rsi.rolling(window=smooth_period, min_periods=1).mean()

        # Calculate the weighted moving average
        weights = range(1, wma_period + 1)
        wma = df['Close'].rolling(window=wma_period).apply(lambda x: sum(x * weights) / sum(weights), raw=False)

        # Calculate the simple moving average
        sma = df['Close'].rolling(window=sma_period).mean()

        # Determine the maximum number of rows available across the calculated indicators
        max_rows = min(len(df), len(rsi), len(stoch_rsi_smooth), len(wma), len(sma))

        # Combine the data frames with matching numbers of rows
        output_df = pd.DataFrame({
            **df.iloc[:max_rows, :].to_dict(orient='list'),
            'rsi': rsi.iloc[:max_rows],
            'stoch_rsi_smooth': stoch_rsi_smooth.iloc[:max_rows],
            'wma': wma.iloc[:max_rows],
            'sma': sma.iloc[:max_rows]
        })

        # Append the processed data frame to the dictionary
        all_data[csvFileName] = output_df

        # Optionally, write the results to a new CSV file for each CSV file processed
        # Ammend exchange name in file path when cleaning different exchanges
        output_file_path = 'BackTest/Cleaned-CsvData/Cleaned-CsvData-BTCUSDT/' + csvFileName.replace('.csv', '_output.csv')
        output_df.to_csv(output_file_path, index=False, header=True)
