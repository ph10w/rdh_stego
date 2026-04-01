from stegolib.stego_rdh import extract_file

file_path, restored = extract_file("stego.png", "./restored_data")

restored.save("./restored_data/restored.png")