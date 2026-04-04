from stegolib.stego_rdh import extract_file
import argparse

parser = argparse.ArgumentParser("extract")
parser.add_argument("--stego_pic", help="stego pic including the data to extract")
parser.add_argument("--extract_data_path", help="path to the data to extracted")
args = parser.parse_args()

file_path, restored = extract_file(stego_path=args.stego_pic, output_folder=args.extract_data_path)

#restored.save(args.extract_data_path)