import pandas as pd 



# read the employees.csv file into a data frame
df = pd.read_csv("employees.csv")

#write the data frame to an excel file
df.to_excel("employees.xlsx", index=False)