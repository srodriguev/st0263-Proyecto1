import os

def split_file_into_blocks(input_file, output_directory):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    block_size = 4 * 1024  # 4KB
    with open(input_file, 'rb') as file:
        block_number = 0
        while True:
            block_data = file.read(block_size)
            if not block_data:
                break
            block_filename = os.path.join(output_directory, f"block_{block_number}")
            with open(block_filename, 'wb') as block_file:
                block_file.write(block_data)
            block_number += 1

if __name__ == "__main__":
    input_file_path = "output.txt" 
    output_directory = "blocks"
    split_file_into_blocks(input_file_path, output_directory)
