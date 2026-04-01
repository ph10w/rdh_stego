from stegolib.stego_rdh import update_file_in_stego

# Neues Stego-Bild mit aktualisierter Datei
update_file_in_stego(
    stego_path="input.png",
    new_file_path="secret_data.7z",
    output_path="stego_updated.png"
)