from read_json_text import extract_json_text  # Import function to extract JSON text from a file
from read_image_url import extract_images  # Import function to extract images from a file
import json  # Import JSON module for handling JSON data
import os  # Import OS module for interacting with the operating system
import glob  # Import glob module for file pattern matching

def combine_json(file_path, image_skip=False):
    # Extract text JSON from the file
    text_JSON = extract_json_text(file_path)
    
    if not image_skip:
        # If image_skip is False, extract images JSON from the file
        image_JSON = extract_images(file_path)
    else:
        # If image_skip is True, skip image extraction and set a default message
        image_JSON = {"message": "No images were processed"}
    
    # Combine text JSON and image JSON into a single dictionary
    combined_result = {
        "text_JSON": text_JSON,
        "image_JSON": image_JSON
    }
    
    # Return the combined result
    return combined_result

# All files in the directory are processed at once and combined into a single JSON object
def context_directory(directory_path, image_skip=False):
    combined_results = {}
    # Iterate through all files in the specified directory
    for file_path in glob.glob(os.path.join(directory_path, '*')):
        if os.path.isfile(file_path):
            # If the path is a file, get the file name
            file_name = os.path.basename(file_path)
            # Combine JSON data from the file
            result = combine_json(file_path, image_skip)
            # Store the result in the combined_results dictionary with the file name as the key
            combined_results[file_name] = result
    # Return the dictionary containing combined results for all files
    return combined_results

# Each file in the directory is processed individually and the results are stored in a list of dictionaries
def batch_directory(directory_path, image_skip=False):
    results = []
    # Iterate through all files in the specified directory
    for file_path in glob.glob(os.path.join(directory_path, '*')):
        if os.path.isfile(file_path):
            # If the path is a file, get the file name
            file_name = os.path.basename(file_path)
            # Combine JSON data from the file
            result = combine_json(file_path, image_skip)
            # Append the result to the results list as a dictionary with file name and result
            results.append({
                "file_name": file_name,
                "result": result
            })
    # Return the list containing results for all files
    return results

# Example usage
# file_path = r"C:\Users\Admin\OneDrive - The University of the South Pacific\Documents\fig2_heat.png"
# combine_json(file_path, image_skip=False)

#if __name__ == "__main__":
#    directory_path = r"C:\Users\Admin\OneDrive - The University of the South Pacific\Documents\batch_test_old\PS205 Text Chapters\PS205 Ch1 split - done"  # Replace with the path to your directory C:\your\directory\path
#    
#    # Process all files at once and store in a single JSON object
#    context_results = context_directory(directory_path, image_skip=True)
#    print(json.dumps(context_results, indent=4))  # Print the combined JSON structure for all files
#    
#    # Process each file individually and produce separate JSON outputs
#    batch_results = batch_directory(directory_path, image_skip=True)
#    for result in batch_results:
#        print(json.dumps(result, indent=4))  # Print the combined JSON structure for each file
