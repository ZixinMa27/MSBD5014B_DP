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

def formulate_and_solve_lp(query_tuple, tau, primary_relation_num=1):
    """
    Formulate the LP problem and solve it using CPLEX.
    
    Parameters:
    - query_tuple: List of tuples representing the query result.
    - tau: Truncation threshold.
    - primary_relation_num: The number of primary relation attributes to consider.
    
    Returns:
    - query_result: The real query result (sum of upper bounds).
    - v_value: The objective value of the solved LP problem.
    """
    num_var = len(query_tuple)
    my_obj = np.ones(num_var)  # Objective function coefficients
    my_var =  [f'u{i}' for i in range(1, num_var + 1)]   # Variable names
    my_ub = [float(tpl[primary_relation_num]) for tpl in query_tuple]  # Variable upper bounds
    
    indices = defaultdict(list)
    lin_expr = []
    for i, tpl in enumerate(query_tuple):
        indices[tpl[:primary_relation_num]].append(my_var[i])
        lin_expr.append([[my_var[i]], [1]])
    
    query_result = sum(my_ub)
    
    # Initialize the CPLEX problem
    problem = cplex.Cplex()
    problem.set_log_stream(None)
    problem.set_error_stream(None)
    problem.set_warning_stream(None)
    problem.set_results_stream(None)
    
    # Set the objective to maximize
    problem.objective.set_sense(problem.objective.sense.maximize)
    problem.variables.add(obj=my_obj, ub=my_ub, names=my_var)
    problem.linear_constraints.add(lin_expr=lin_expr, senses='L' * len(lin_expr), rhs=[tau] * len(lin_expr))
    
    # Solve the problem
    problem.solve()
    v_value = problem.solution.get_objective_value()
    
    return query_result, v_value


def laplace_noise(scale):
    """
    Generate Laplace noise with a given scale.
    
    Parameters:
    - scale: The scale parameter for the Laplace distribution.
    
    Returns:
    - noise: The generated Laplace noise.
    """
    return np.random.laplace(scale=scale)

def r2t(query_tuple, param, primary_relation_num=1):
    """
    Apply the R2T mechanism to ensure differential privacy.
    
    Parameters:
    - query_tuple: List of tuples representing the query result.
    - param: Dictionary containing the parameters (epsilon, beta, GSQ).
    - primary_relation_num: The number of primary relation attributes to consider.
    
    Returns:
    - relative_error: The relative error between the real query result and the DP result.
    """
    beta, epsilon, GSQ = param["beta"], param["epsilon"], param["GSQ"]
    tilde_Q = 0 

    for j in range(1, int(np.log2(GSQ)) + 1):
        tau = 2 ** j 
        
        # Get LP solver result
        query_result, Q_tau_j = formulate_and_solve_lp(query_tuple, tau, primary_relation_num)
        
        # Compute tilde_Q_tau 
        tilde_Q_tau = Q_tau_j + np.random.laplace(loc=0, scale=np.log2(GSQ) * tau / epsilon) - np.log2(GSQ) * np.log(np.log2(GSQ) / beta) * (tau / epsilon)
        
        # Compute final result
        tilde_Q = max(tilde_Q_tau, tilde_Q)
        
    relative_error = np.abs(query_result - tilde_Q) / query_result
    logging.info(f"Real query result: {query_result}. After R2T query result: {tilde_Q}. Relative error: {relative_error * 100:.4f}%.")
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
        "GSQ": 10 ** 5  # Global sensitivity of the given query
    }
    
    # List of queries to run
    #queries = [query11, query18]
    queries = [query11]
    
    for query in queries:
        log_file = f'Result/{query.query_name.replace(" ", "_")}.txt'
        print(f"Running query name: {query.query_name}")
        
        # Run the query
        avg_running_time, avg_relative_error = run_query(query, param, log_file)
        
        # Print the results
        print(f"Average running time: {avg_running_time:.4f} seconds")
        print(f"Average relative error is: {avg_relative_error * 100:.4f}%")


# Define SQL queries    
#Type3: Aggregation
query11 = SQLQuery('''select s_suppkey, ps_supplycost * ps_availqty/1000000 
                   from nation, supplier, partsupp 
                   where ps_suppkey = s_suppkey 
                   and s_nationkey = n_nationkey;''', "query11", "Aggregation")
query18 = SQLQuery('''select c_custkey, l_quantity 
                   from customer, orders, lineitem 
                   where c_custkey = o_custkey 
                   and l_orderkey = o_orderkey''', "query18","Aggregation")



if __name__ == "__main__":
    main()
    

