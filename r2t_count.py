import os
import psycopg2
import numpy as np
import logging
from collections import defaultdict
import cplex
import time

class SQLQuery:
    def __init__(self, query, name, query_type):
        self.query = query
        self.query_name = name
        self.query_type = query_type
    def fetch_data(self):
        """
        Connect to the PostgreSQL database and execute the given query.
        Returns the fetched data as a list of tuples.
        """
        conn = psycopg2.connect(user="postgres",
                                password="Aa123456",
                                host="localhost",
                                port="5432",
                                database= "tpch")
        cursor = conn.cursor()
        cursor.execute(self.query)
        return cursor.fetchall()

def formulate_and_solve_lp(query_tuple, tau):
    """
    Formulate the LP problem and solve it using CPLEX.

    Parameters:
    - query_tuple: List of tuples representing the query result.
    - tau: Truncation threshold.

    Returns:
    - v_value: The objective value of the solved LP problem.
    """
    num_var = len(query_tuple)
    indices = defaultdict(list)
    
    # Set variables
    my_obj = np.ones(num_var)  # Objective function coefficients
    my_var = [f'u{i}' for i in range(1, num_var + 1)]  # Variable names
    my_ub = np.ones(num_var)  # Variable upper bounds

    # Map each tuple to its corresponding variable
    for i, tpl in enumerate(query_tuple):
        indices[tpl].append(my_var[i])

    # Create linear expressions for constraints
    lin_expr = [[var_list, np.ones(len(var_list))] for var_list in indices.values()]
    
    # Initialize the CPLEX problem
    problem = cplex.Cplex()
    problem.set_log_stream(None)
    problem.set_error_stream(None)
    problem.set_warning_stream(None)
    problem.set_results_stream(None)
    
    # Set the objective to maximize
    problem.objective.set_sense(problem.objective.sense.maximize)
    problem.variables.add(obj=my_obj, ub=my_ub, names=my_var)
    
    # add constraints
    problem.linear_constraints.add(lin_expr=lin_expr, senses='L' * len(lin_expr), rhs= [tau] * len(lin_expr))
    
    # Solve the problem
    problem.solve()
    v_value = problem.solution.get_objective_value()
    
    return v_value

def laplace_noise(scale):
    """
    Generate Laplace noise with a given scale.
    
    Parameters:
    - scale: The scale parameter for the Laplace distribution.
    
    Returns:
    - noise: The generated Laplace noise.
    """
    return np.random.laplace(scale=scale)

def r2t(query_tuple, param):
    """
    Apply the R2T mechanism to ensure differential privacy.

    Parameters:
    - query_tuple: List of tuples representing the query result.
    - param: Dictionary containing the parameters (epsilon, beta, GSQ).

    Returns:
    - relative_error: The relative error between the real query result and the DP result.
    """
    beta, epsilon, GSQ = param["beta"], param["epsilon"], param["GSQ"]

    tilde_Q = 0
    # perform algorithm 
    for j in range(1, int(np.log2(GSQ)) + 1): #for tau(j) = 2^𝑗, 𝑗 = 1, . . . , log(𝐺𝑆_𝑄)
        tau = 2 ** j 
        Q_tau_j = formulate_and_solve_lp(query_tuple, tau)
        
        tilde_Q_tau = Q_tau_j + laplace_noise(np.log2(GSQ) * tau / epsilon) - np.log2(GSQ) * np.log(np.log2(GSQ) / beta) * (tau / epsilon)
        
        tilde_Q = max(tilde_Q_tau, tilde_Q)
        
    query_real_result = len(query_tuple) # the count of tuples is the real query result
    relative_error = np.abs(query_real_result - tilde_Q) / query_real_result
    logging.info(f"Real query result: {query_real_result}. After R2T query result: {tilde_Q}. Relative error: {relative_error * 100:.4f}%.")
    # print(f"The real query result is: {query_real_result}. After R2T the query result is: {tilde_Q}. The relative error is: {relative_error * 100:.4f}%.")
    return relative_error

def setup_logging(log_file):
    """
    Set up logging to a specific file.
    
    Parameters:
    - log_file: The name of the log file.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Remove all handlers associated with the logger object
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    handler = logging.FileHandler(log_file)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def run_query(query, param, log_file,num_repetitions=100):
    """
    Run the R2T mechanism for a given query and parameters.
    
    Parameters:
    - query: An instance of SQLQuery containing the query and query type.
    - param: Dictionary containing the parameters (epsilon, beta, GSQ).
    - num_repetitions: Number of repetitions for running the R2T mechanism.
    
    Returns:
    - avg_running_time: Average running time for the R2T mechanism.
    - avg_relative_error: Average relative error of the R2T mechanism.
    """
    
    setup_logging(log_file)
    logging.info(f"Running query name: {query.query_name}")
    logging.info(f"Running query: {query.query}")
    
    # Fetch data using the SQLQuery class
    query_tuples = query.fetch_data()
    
    running_times = []
    relative_errors = []

    # Run the R2T mechanism multiple times and collect running times and relative errors
    for _ in range(num_repetitions):
        start_time = time.time()
        relative_error = r2t(query_tuples, param)
        end_time = time.time()
        running_time = end_time - start_time
        relative_errors.append(relative_error)
        running_times.append(running_time)
        
    # Sort the running times and relative errors together
    data = list(zip(running_times, relative_errors))
    data.sort(key=lambda x: x[1])
    # Remove the best 20 and worst 20 runs
    data = data[20:-20]
    # Unzip the sorted data
    running_times, relative_errors = zip(*data)
    print(f"relative error is {relative_errors}")

    # Calculate the average running time and average relative error
    avg_running_time = sum(running_times) / len(running_times)
    avg_relative_error = sum(relative_errors) / len(relative_errors)
    
    # Log the results
    logging.info(f"Average running time: {avg_running_time:.4f} seconds")
    logging.info(f"Average relative error is: {avg_relative_error * 100:.4f}%")

    return avg_running_time, avg_relative_error

def main():
    """
    Main function to execute the R2T mechanism for multiple queries and log the outputs.
    """
    # Define parameters
    param = { 
        "epsilon": 0.8,
        "beta": 0.1,
        "GSQ": 10**5  # Global sensitivity of the given query
    }
    
    # List of queries to run
    #queries = [query3, query12, query20, query5]
    queries = [query12]
    
    for query in queries:
        log_file = f'Result/{query.query_name.replace(" ", "_")}.txt'
        print(f"Running query name: {query.query_name}")
        
        # Run the query
        avg_running_time, avg_relative_error = run_query(query, param, log_file)
        
        # Print the results
        print(f"Average running time: {avg_running_time:.4f} seconds")
        print(f"Average relative error is: {avg_relative_error * 100:.4f}%")


# Define SQL queries    
# Type1: Single primary private relation
query12 = SQLQuery('''select o_orderkey 
                   from orders, lineitem 
                   where o_orderkey = l_orderkey''', "query12", "Single primary private relation")
query3 = SQLQuery('''SELECT customer.c_custkey
                    FROM customer, orders, lineitem
                    WHERE orders.O_CUSTKEY = customer.C_CUSTKEY
                    AND lineitem.L_ORDERKEY = orders.O_ORDERKEY
                    AND o_orderdate < DATE '1997-01-01'
                    AND l_shipdate > DATE '1994-01-01';''', "query3", "Single primary private relation")
query20 = SQLQuery('''select s_suppkey 
                   from supplier, nation, partsupp, lineitem 
                   where l_partkey = ps_partkey 
                   and l_suppkey = ps_suppkey 
                   and s_nationkey = n_nationkey 
                   and s_suppkey=ps_suppkey;''',  "query20", "Single primary private relation")
#Type2: Multiple primary private relations
query5 = SQLQuery('''select C_CUSTKEY, S_SUPPKEY 
                  from customer, orders, lineitem, supplier, nation, region 
                  where c_custkey = o_custkey 
                  and l_orderkey = o_orderkey 
                  and l_suppkey = s_suppkey 
                  and c_nationkey = s_nationkey
                  and s_nationkey = n_nationkey 
                  and n_regionkey = r_regionkey''', "query5","Multiple primary private relations")


if __name__ == "__main__":
    main()
    

