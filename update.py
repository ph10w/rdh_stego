from stegolib.stego_rdh import update_file_in_stego
import argparse

parser = argparse.ArgumentParser("update")
parser.add_argument("--input_pic", help="input pic to embed data into")
parser.add_argument("--input_data", help="input data to embed into pic")
parser.add_argument("--stego_pic", help="output stego pic updated with new data")
args = parser.parse_args()

# Neues Stego-Bild mit aktualisierter Datei
update_file_in_stego(
    stego_path=args.input_pic,
    new_file_path=args.input_data,
    output_path=args.stego_pic
)