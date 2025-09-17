
Calculate difference/ratio find the fee for whenever based off price

ratio average = for each time get the difference from each one and their fees, then add them up then divide by the number of ratios there are. 
Ex.  T1 - T2 = T_ratio ; fee(T2) - fee(T1) = fee_ratio 
For T3-T2 = T1_ratio ; fee(T3) - fee(T2) = fee1_ratio 
Thus, Ratio1 = T_ratio / fee_ratio
Ratio2 = T1_ratio / fee1_ratio 

Add however number of ratios together and divide by number of ratios 
This would be the ratio average for that specific epoch

T_amt * (ratio average) = fee_Tamt

HashMap (rate execution rate fees)
Map = {Key: Price Point/Size of Transaction, Value: {{Fee, Timestamp}}

EXAMPLE
Key: {$1000, $2000, $4000, $8000, $16000...,$N} (all the way until $1 million)
Values : { [{5.00, 43944398840398490}], 
[{10.00, 413414398590854}], {[7.00, 43944398840398490]}


The keys and values are arrays but each match correspondingly. Transaction/Money put in must be at least 0.001 of the price of the coin itself. Then we increment of values 2x, so 0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64, 1.28, 2.56 and so on until it hits 10x the price of the coin. Then given all the fees and transaction at the point in time, give a ratio / average for that given timestamp. when calculating the difference, do so for each price and fee (within the same time epoch). For example if there are 1, 2, 3, 4, 5 transaction amounts and fees, then it would be T5 - T4, T4-T3, T3-T2, T2-T1, and do so for the fees as well to calculate ratio.                                                                     