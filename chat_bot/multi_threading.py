import threading
from queue import Queue
import threading
import time
from print_colors import print_colored
from run_query import init_connection_pool,close_connection_pool


def threaded_function_with_timing(func, args, kwargs, color, output_queue,num):
    """Function to execute any function with timing and place the result into a queue."""
    start_time = time.time()
    result = func(*args, **kwargs)  # Execute the passed function with its arguments.
    elapsed_time = time.time() - start_time
    print_colored(f"Total time for {func.__name__} {num}: {elapsed_time:.3f} seconds", color)
    output_queue.put(result)  # Put the result into the queue.

def run_functions_in_threads(functions):
    """Run multiple functions in separate threads and return their outputs."""
    threads = []
    results = []
    output_queue = Queue()  # Queue to collect results in a thread-safe manner.

    # Create and start a thread for each function.
    
    for num,arguments in enumerate(functions):
        func, args, kwargs = arguments
        with open("chat_bot/multi_threading/threading_log.txt", "a") as f:
            f.write(f"Function: {func.__name__} \n")
            f.write(f"Arguments: {args} \n")
            f.write(f"Keyword Arguments: {kwargs} \n")
        
        thread = threading.Thread(
            target=threaded_function_with_timing,
            args=(func, args, kwargs, "MAGENTA", output_queue, num)
            )
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete.
    
    for thread in threads:
        thread.join()
    
    # Collect all results from the queue.
    
    while not output_queue.empty():
        results.append(output_queue.get())
    
    return results

# Example usage:

# init_connection_pool()

# # Define variabels for function
# response = {
#     "User Question": "How many games in this season has Vinicuis Junior scored at least a goal?",
#     "Previous Context": {},
#     "Performance Data": {},
#     "Tokens Used": {}
#     }
# keywords = ["running", "swimming", "jumped","expected goals"]

# # List of functions with arguments
# functions_to_run = [
#     (process_text_with_model, (keywords,), {}),
#     (extract_key_info_openai, (response,), {}),
#     (add, (2, 3), {}),
# ]

# # Run functions in threads
# start_time = time.time()
# threads_output = run_functions_in_threads(functions_to_run)
# print("Function outputs:", threads_output)
# print_colored(f"Total time: {time.time() - start_time}", "MAGENTA")
# close_connection_pool()
