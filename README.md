# MSBD5014B Answering SQL Queries Under Differential Privacy

## Introduction
This project focuses on implementing algorithms for achieving differential privacy (DP) in the context of the TPC-H benchmark queries. The goal is to apply the concepts and techniques presented in the research paper: ["R2T: Instance-optimal Truncation for Differentially Private Query Evaluation with Foreign Keys"](https://cse.hkust.edu.hk/~yike/R2T.pdf).

## Clone this Repository

```bash
git clone https://github.com/ZixinMa27/MSBD5014B_DP.git
cd MSBD5014B_DP
```

## Generate Data from TPCH benchmark

To generate data from the TPCH benchmark, follow these steps:

1. Change directory to TPCH/dbgen: `cd TPCH/dbgen`
2. Generate data with a scale of 0.125 and convert it to CSV format using the command: 
```bash
./dbgen -s 0.125
for i in $(ls *.tbl); do sed 's/|$//' $i > ${i/tbl/csv}; echo $i; done;
```
3. Copy the generated data to the /data folder.

## Set up Database and Import Data

To set up the database and import the generated data, follow these steps:

1. Make sure PostgreSQL is installed.
2. Create an empty database using the command: `createdb tpch`
3. Go to the MSBD5014B_DP directory: `cd MSBD5014B_DP`
4. Run the command: `python SetUpDB.py tpch 0.125` (Replace 0.125 with the desired data scale)
5. If you want to change the database, you can use the command: `python CleanDB.py tpch` to clean up the tables, and then rerun `SetUpDB.py`.

## Run Query on R2T

To run queries on R2T, there are two scripts available:

1. **r2t_count.py**: This script can run queries 3, 5, and 12, which fall under the "Single primary private relation" and "Multiple primary private relations" types of queries.
2. **r2t_aggregation.py**: This script can run queries 11 and 18, which also fall under the "Single primary private relation" and "Multiple primary private relations" types of queries.

## Testing Instructions

To adjust the parameters and test the scripts, follow these instructions:

1. Open the script file.
2. Under the `main` function, you can adjust the following parameters: `epsilon`, `beta`, `GSQ`, the list of queries to run, and the number of repetitions for the experiment.
3. The default parameter settings are as follows:

   ```python
   param = {
       "epsilon": 0.8,
       "beta": 0.1,
       "GSQ": 10**5,
       "num_repetition": 100
   }
   ```
For r2t_count.py, the default query list is [query12], and for r2t_aggregation.py, the default query list is [11]. 

5. The log results will be saved in the /Result folder.



