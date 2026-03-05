from tqdm import tqdm
import time

def example_function(total_iterations):
    # Initialize tqdm with the total number of iterations
    progress_bar = tqdm(total=total_iterations, desc="Processing")

    for i in range(total_iterations):
        variable_to_display = i * 2  # Replace with your variable

        # Update the progress bar description with the variable value
        progress_bar.set_description(f"Processing: {variable_to_display}")
        progress_bar.update(1)  # Increment the progress bar
        time.sleep(0.1)  # Simulate a time-consuming operation

    # Close the progress bar when the loop is complete
    progress_bar.close()

# Call the example function with the total number of iterations
example_function(total_iterations=100)
