import os

def generate_file(file_size_kb):
    bytes_per_item = 3  # 1 byte for each digit, 1 byte for comma, and 1 byte for space
    file_size_bytes = file_size_kb * 1024
    
    current_size = 0
    num = 0
    
    with open("output.txt", "w") as f:
        while current_size < file_size_bytes:
            f.write(str(num))
            current_size += len(str(num))
            if current_size + bytes_per_item <= file_size_bytes:
                f.write(", ")
                current_size += 2 
            num += 1
    print("File generated successfully!")

if __name__ == "__main__":
    file_size_kb = int(input("Enter the desired file size in kilobytes: "))
    generate_file(file_size_kb)
