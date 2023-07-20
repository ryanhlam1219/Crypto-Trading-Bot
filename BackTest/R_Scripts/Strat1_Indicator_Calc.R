library(zoo)
library(quantmod)
library(TTR)

# Load the data from a CSV file, the file to be read should be placed in the CSV_FILES folder
# 1. figure out how to open .txt files and read line by line in R
# 2. store the name of the csv file in the .txt file into string variable
# 3. append to string variable to 'CSV_FILES/'
# exampple: 'CSV_Files' + csvFileName 
df <- read.csv('CSV_FILES/SHIBUSDT-1m-2023-05-14.csv')


# Set the lookback periods
rsi_period <- 14
stoch_period <- 5
smooth_period <- 3
wma_period <- 144
sma_period <- 5

# Calculate the RSI
delta <- diff(df$Close)
gain <- ifelse(delta > 0, delta, 0)
loss <- ifelse(delta < 0, -delta, 0)
avg_gain <- rollmean(gain, rsi_period, align="right")
avg_loss <- rollmean(loss, rsi_period, align="right")
rs <- avg_gain / avg_loss
rsi <- 100 - (100 / (1 + rs))

# Calculate the Stochastic RSI
rsi_low <- rollapply(rsi, stoch_period, min, align="right")
rsi_high <- rollapply(rsi, stoch_period, max, align="right")
stoch_rsi <- (rsi - rsi_low) / (rsi_high - rsi_low) * 100
stoch_rsi_smooth <- rollmean(stoch_rsi, smooth_period, align="right")

# Calculate the weighted moving average
weights <- seq(1, wma_period)
wma <- rollapply(df$Close, wma_period, function(x) sum(x * weights) / sum(weights), align="right")

# Calculate the simple moving average
sma <- rollmean(df$Close, sma_period, align="right")

# Determine the maximum number of rows available across the calculated indicators
max_rows <- min(nrow(df), length(rsi), length(stoch_rsi_smooth), length(wma), length(sma))

# Combine the data frames with matching number of rows
output_df <- data.frame(df[1:max_rows, ], rsi[1:max_rows], stoch_rsi_smooth[1:max_rows], wma[1:max_rows], sma[1:max_rows])

# Write the results to a new CSV file
write.csv(output_df, 'output_data.csv', row.names=FALSE)

